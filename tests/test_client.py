"""
This module contains test functions for the webserver.client module.

The functions in this module test the functionality of various functions
in the webserver.client module, including send_request, connect_to_server,
reconnect, and managed_socket_connection.
"""


import sys
import os
import socket
from unittest.mock import patch, call
from webserver.client import (send_request, connect_to_server, reconnect,
                              managed_socket_connection, SERVER_HOST,
                              SERVER_PORT, sslcert, sslkey)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_send_request() -> None:
    """
    Test the send_request function.
    """
    with patch(
            'webserver.client.managed_socket_connection'
    ) as mock_managed_socket_connection:
        mock_managed_socket = mock_managed_socket_connection.return_value
        mock_client_socket = mock_managed_socket.__enter__.return_value
        mock_client_socket.send.return_value = None
        mock_client_socket.recv.return_value = b'server response'

        with patch('builtins.input', side_effect=['test data', ':q']
                   ) as mock_input:
            send_request()
            assert mock_input.call_count == 2
            mock_input.assert_has_calls([
                call("Enter a string (or ':q' to quit): "),
                call("Enter a string (or ':q' to quit): ")
            ])
            mock_client_socket.send.assert_called_once_with(b'test data')
            mock_client_socket.recv.assert_called_once_with(1024)


def test_connect_to_server_with_ssl() -> None:
    """
    Test the connect_to_server function with SSL.
    """
    with patch('webserver.client.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = True
        with patch('webserver.client.ssl.SSLContext') as mock_ssl_context:
            mock_context = mock_ssl_context.return_value
            with patch('webserver.client.socket.socket') as mock_socket:
                wrap_socket_return = mock_socket.return_value
                mock_context.wrap_socket.return_value = wrap_socket_return
                result = connect_to_server()
                assert result == wrap_socket_return
                assert mock_socket.call_count == 2
                mock_socket.assert_any_call(
                    socket.AF_INET, socket.SOCK_STREAM)
                wrap_socket_return.connect.assert_called_once_with(
                    (SERVER_HOST, SERVER_PORT))
                mock_context.load_cert_chain.assert_called_once_with(
                    sslcert, sslkey)
                mock_context.wrap_socket.assert_called_once_with(
                    mock_socket.return_value, server_side=False)


def test_connect_to_server_without_ssl() -> None:
    """
    Test the connect_to_server function without SSL.
    """
    with patch('webserver.client.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = False
        with patch('webserver.client.socket.socket') as mock_socket:
            mock_client_socket = mock_socket.return_value
            result = connect_to_server()
            assert result == mock_client_socket
            mock_socket.assert_called_once_with(
                socket.AF_INET, socket.SOCK_STREAM)
            mock_client_socket.connect.assert_called_once_with(
                (SERVER_HOST, SERVER_PORT))


def test_reconnect_success() -> None:
    """
    Test the reconnect function for successful reconnection.
    """
    with patch(
        'webserver.client.close_client_socket'
    ) as mock_close_client_socket:
        with patch(
            'webserver.client.connect_to_server'
        ) as mock_connect_to_server:
            mock_connect_to_server.return_value = 'mock client socket'
            result = reconnect(None)
            assert isinstance(result, str)
            assert result == "mock client socket"
            mock_close_client_socket.assert_called_once_with(None)
            mock_connect_to_server.assert_called_once()


def test_managed_socket_connection() -> None:
    """
    Test the managed_socket_connection context manager.
    """
    with patch(
        'webserver.client.connect_to_server'
    ) as mock_connect_to_server:
        mock_connect_to_server.return_value = 'mock client socket'
        with patch(
            'webserver.client.close_client_socket'
        ) as mock_close_client_socket:
            with managed_socket_connection() as client_socket:
                assert isinstance(client_socket, str)
                assert client_socket == 'mock client socket'
            mock_connect_to_server.assert_called_once()
            mock_close_client_socket.assert_called_once_with(
                'mock client socket')

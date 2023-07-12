"""
This module contains test functions for the webserver.server module.

The functions in this module test the functionality of various functions
in the webserver.server module, including start_server,
handle_client_connection, read_file, and linuxpath.
"""

import sys
import os
import socket
import ssl
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pytest
from webserver.server import (read_file, handle_client_connection,
                              start_server, linuxpath, SERVER_HOST,
                              SERVER_PORT, sslkey, sslcert)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_start_server() -> None:
    """
    Test starting the server and listening for client connections.

    This test verifies the behavior of the start_server function when
    the server is started and listens for client connections. It uses
    patching to mock the necessary functions and simulate the
    KeyboardInterrupt to exit the server loop. The expected behavior
    is that the appropriate functions are called to start the server
    and listen for connections.

    Returns:
        None
    """
    mock_socket = MagicMock()
    mock_socket.bind.return_value = None
    mock_socket.listen.return_value = None
    mock_socket.accept.side_effect = KeyboardInterrupt

    with patch('webserver.server.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = True
        with patch('webserver.server.socket.socket', return_value=mock_socket):
            with patch('webserver.server.ssl.create_default_context'
                       ) as mock_create_default_context:
                mock_context = MagicMock()
                mock_context.wrap_socket.return_value = mock_socket
                mock_create_default_context.return_value = mock_context
                with patch('webserver.server.threading.Thread') as mock_thread:
                    start_server()
                    assert not mock_thread.called


def test_start_server_with_ssl() -> None:
    """
    Test starting the server with SSL.

    This test verifies the behavior of the start_server function when
    the server is started with SSL. It uses patching to mock the
    necessary functions and simulate the SSL behavior. The expected
    behavior is that the appropriate functions are called to start
    the server with SSL.

    Returns:
        None
    """
    with patch('webserver.server.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = True
        with patch(
            'webserver.server.ssl.create_default_context'
        ) as mock_create_default_context:
            mock_context = mock_create_default_context.return_value
            mock_ssl_socket = MagicMock()
            mock_client_socket = MagicMock()
            mock_client_socket.recv.return_value = b''
            mock_ssl_socket.accept.side_effect = [
                (mock_client_socket, (SERVER_HOST, SERVER_PORT)),
                KeyboardInterrupt]
            mock_context.wrap_socket.return_value = mock_ssl_socket
            with patch('webserver.server.socket.socket') as mock_socket:
                mock_socket.return_value.bind.return_value = None
                mock_socket.return_value.listen.return_value = None
                start_server()
                mock_getboolean.assert_called_once_with('Server', 'ssl')
                mock_create_default_context.assert_called_once_with(
                    ssl.Purpose.CLIENT_AUTH)
                mock_context.load_cert_chain.assert_called_once_with(
                    certfile=sslcert, keyfile=sslkey)
                mock_context.wrap_socket.assert_called_once_with(
                    mock_socket.return_value, server_side=True)


def test_start_server_with_client_connection() -> None:
    """
    Test starting the server with a client connection.

    This test verifies the behavior of the start_server function when a
    client connection is established. It uses patching to mock the
    necessary functions and simulate the client connection.
    The expected behavior is that a new thread is created and the
    handle_client_connection function is called.

    Returns:
        None
    """

    mock_socket = MagicMock()
    mock_socket.bind.return_value = None
    mock_socket.listen.return_value = None
    mock_socket.accept.side_effect = [(None, None), KeyboardInterrupt]

    with patch('webserver.server.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = True
        with patch('webserver.server.socket.socket', return_value=mock_socket):
            with patch('webserver.server.ssl.create_default_context'
                       ) as mock_create_default_context:
                mock_context = MagicMock()
                mock_context.wrap_socket.return_value = mock_socket
                mock_create_default_context.return_value = mock_context
                with patch('webserver.server.threading.Thread') as mock_thread:
                    with patch(
                        'webserver.server.handle_client_connection'
                    ) as mock_handle_client_connection:
                        start_server()
                        assert mock_thread.called
                        assert not mock_handle_client_connection.called


def test_start_server_with_socket_error() -> None:
    """
    Test starting the server with a socket error.

    This test verifies the behavior of the start_server function when a
    socket error occurs during server startup. It uses patching to mock
    the necessary functions and simulate the socket error. The expected
    behavior is that the error message is printed to the console.

    Returns:
        None
    """
    with patch('webserver.server.config.getboolean') as mock_getboolean:
        mock_getboolean.return_value = False
        with patch('webserver.server.socket.socket') as mock_socket:
            mock_socket.side_effect = socket.error('test error')
            with patch('builtins.print') as mock_print:
                start_server()
                mock_print.assert_called_once_with(
                    'Error starting server: test error')


def test_handle_client_connection_empty_data() -> None:
    """
    Test for the handle_client_connection function with empty data.

    This test verifies the behavior of the 'handle_client_connection'
    function when the client receives an empty data. It uses mocking to
    simulate a client socket and checks if the function doesn't send
    any response.

    Returns:
        None
    """
    client_socket = Mock()
    client_socket.recv.return_value = b""
    handle_client_connection(client_socket, (SERVER_HOST, SERVER_PORT))
    client_socket.send.assert_not_called()


def test_handle_client_connection_with_string_found() -> None:
    """
    Test handle_client_connection function with a matching string found.

    This test verifies the behavior of the 'handle_client_connection'
    function when a matching string is found in the requested file. It
    uses patching to mock the necessary functions and simulate the file
    content and the client request. The expected behavior is that the
    function sends the appropriate response to the client socket.

    Returns:
        None
    """
    with patch('webserver.server.read_file') as mock_read_file:
        mock_read_file.return_value = {'test string': [0]}
        with patch('webserver.server.search_string_in_file'
                   ) as mock_search_string_in_file:
            mock_search_string_in_file.return_value = True
            with patch('socket.socket') as mock_socket:
                mock_socket.recv.side_effect = [b'test string', b'']
                handle_client_connection(
                    mock_socket, (SERVER_HOST, SERVER_PORT))
                mock_socket.send.assert_called_with(b'STRING EXISTS\n')


def test_handle_client_connection_with_file_not_found() -> None:
    """
    Test handle_client_connection function with a file not found error.

    This test verifies the behavior of the 'handle_client_connection'
    function when the requested file is not found. It uses patching to
    mock the necessary functions and checks if the appropriate error
    message is printed to the console and the socket is closed.

    Returns:
        None
    """
    with patch('webserver.server.read_file') as mock_read_file:
        mock_read_file.side_effect = FileNotFoundError
        with patch('webserver.server.socket.socket') as mock_socket:
            with patch('builtins.print') as mock_print:
                handle_client_connection(mock_socket, (SERVER_HOST,
                                                       SERVER_PORT))
                mock_print.assert_called_once_with(
                    'File not found:', linuxpath)
                mock_socket.close.assert_called_once()


def test_read_file(tmp_path: Path) -> None:
    """
    Test for the read_file function.

    This test verifies the behavior of the 'read_file' function by
    creating a temporary file, writing some text to it, and then checking
    if the function reads the file correctly. It also tests the behavior
    when attempting to read a non-existent file, which should raise a
    FileNotFoundError.

    Args:
        tmp_path: A temporary directory provided by the pytest framework.

    Returns:
        None.
    """
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    expected_index = {'Hello, world!': [0]}
    assert read_file(str(test_file)) == expected_index
    with pytest.raises(FileNotFoundError):
        read_file(str(tmp_path / "non_existent.txt"))


def test_handle_client_connection_with_socket_error() -> None:
    """
    Test for the handle_client_connection function with a socket error.

    This test verifies the behavior of handle_client_connection when a
    socket error occurs during data receiving or sending. It uses
    patching to mock the necessary functions and simulate the socket
    error. The expected behavior is that the error message is printed
    to the console.

    Returns:
        None
    """
    with patch('webserver.server.read_file') as mock_read_file:
        mock_read_file.return_value = b'test string'
        with patch('webserver.server.socket.socket') as mock_socket:
            mock_socket.recv.side_effect = socket.error('test error')
            with patch('builtins.print') as mock_print:
                handle_client_connection(mock_socket, (SERVER_HOST,
                                                       SERVER_PORT))
                mock_print.assert_called_once_with(
                    'Error receiving or sending data: test error')

"""
This module provides client-side functionality for connecting to a server,
sending requests, and managing socket connections.
"""
import socket
import ssl
import configparser
import time
from typing import Optional, Generator
from contextlib import contextmanager

config = configparser.ConfigParser()
config.read("config.ini")
sslcert = config.get("Server", "sslcert")
sslkey = config.get("Server", "sslkey")

SERVER_HOST = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 12345


# function that creates a gateway to the server
def connect_to_server() -> socket.socket:
    """
    Connects to the server and returns the client socket.

    This function establishes a connection to the server using a socket.
    If SSL is enabled, it creates an SSL context, loads the certificate
    chain, and performs an SSL handshake with the server. If SSL is not
    enabled, it connects to the server without SSL.

    Returns:
        socket.socket: The client socket connected to the server.
    """

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    use_ssl = config.getboolean('Client', 'ssl')
    if use_ssl:
        # Create an SSL context
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.check_hostname = False
        client_context.verify_mode = ssl.CERT_NONE

        # Send our generated certificate chain during the handshake
        client_context.load_cert_chain(sslcert, sslkey)

        # Connect to the server
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket = client_context.wrap_socket(sock, server_side=False)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("[*] Connected to the server with SSL.")

        except (socket.error,
                ssl.SSLError,
                ssl.CertificateError) as connection_error:
            print(f"{type(connection_error).__name__} error: "
                  f"{connection_error}")
    else:
        # Connect to the server without SSL
        try:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("[*] Connected to the server without SSL.")
        except socket.error as connection_error:
            print("Socket error:", connection_error)

    return client_socket


def close_client_socket(client_socket: Optional[socket.socket]) -> None:
    """
    Closes the client socket if it is not None.

    Args:
        client_socket (Optional[socket.socket]): The client socket to close.

    Returns:
        None
    """
    if client_socket is not None:
        client_socket.close()


def reconnect(client_socket: Optional[socket.socket]) -> socket.socket:
    """Attempt to reconnect to the server.

    Args:
        client_socket (Optional[socket.socket]): The client socket
        to close before reconnecting.

    Returns:
        socket.socket: The new client socket connected to the server.
    """
    print('Attempting to reconnect...')
    attempts = 0
    while attempts < 5:
        close_client_socket(client_socket)
        time.sleep(0.2)
        client_socket = connect_to_server()
        if client_socket is not None:
            return client_socket
        attempts += 1
    raise ConnectionRefusedError("Failed to reconnect after 5 attempts.")


@contextmanager
def managed_socket_connection() -> Generator[Optional[socket.socket],
                                             None, None]:
    """
    Context manager for managing a client socket connection.

    This context manager handles the opening and closing of a client
    socket connection. It uses the 'connect_to_server()' function to
    obtain a client socket and yields it for use within the 'with'
    block. When the 'with' block is exited, either normally or due to
    an error, the context manager automatically closes the client
    socket using the 'close_client_socket()' function.

    Yields:
        Optional[socket.socket]: The client socket obtained from the
            'connect_to_server()' function.
    """
    client_socket: Optional[socket.socket] = connect_to_server()
    try:
        yield client_socket
    finally:
        close_client_socket(client_socket)


# function that Sends a message to the server
def send_request() -> None:
    """
    Sends a request message to the server.

    This function sends a request message to the server using the client
    socket obtained from the 'connect_to_server()' function. It reads
    the contents of the specified file and sends each line as a separate
    message to the server. It then waits for a response from the server
    and prints it.

    Returns:
        None
    """
    with managed_socket_connection() as client_socket:
        while True:
            message = input("Enter a string (or ':q' to quit): ")
            if message.lower() == ':q':
                break
            try:
                if client_socket is not None:
                    client_socket.send(message.encode())
                    response = client_socket.recv(1024).decode()
                    print(response)
                else:
                    print("Invalid client socket.")
            # Handle the errors appropriately
            except (BrokenPipeError, ConnectionError, TimeoutError,
                    socket.error, OSError, ConnectionRefusedError,
                    socket.timeout) as connection_error:
                print(
                    f'{type(connection_error).__name__} occurred:'
                    f'{str(connection_error)}')
                # Handle the error appropriately
                if isinstance(connection_error, ConnectionRefusedError):
                    print("Reconnection may not be possible")
                else:
                    client_socket = reconnect(client_socket)
            except Exception as connection_error:
                print(f'Unhandled exception occurred: {connection_error}')
                break


if __name__ == '__main__':
    send_request()

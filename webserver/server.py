"""
This module provides server-side functionality for handling client connections
and processing requests.
"""
import socket
import threading
import configparser
import time
import ssl
from typing import Tuple, Dict, List

config = configparser.ConfigParser()
config.read("config.ini")
linuxpath = config.get("Server", "linuxpath")
sslcert = config.get("Server", "sslcert")
sslkey = config.get("Server", "sslkey")
reread_on_query = config.getboolean('Server', 'REREAD_ON_QUERY')

# Set up a server socket
SERVER_HOST = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 12345


# function to reuse when reading files
def read_file(file_name: str) -> Dict[str, List[int]]:
    """
    Read a file and create an index of lines.

    Args:
        file_name (str): The name of the file to be read.

    Returns:
        Index dictionary of lines and line numbers.
    """
    index: Dict[str, List[int]] = {}
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line_number, line in enumerate(lines):
            print(line, line_number)
            line = line.strip()
            if line not in index:
                index[line] = []
            index[line].append(line_number)
            print(index)
    return index


# function to search for the string
def search_string_in_file(index: Dict[str, List[int]], string_to_search: str
                          ) -> bool:
    """
    Search for a string in the provided index.

    Args:
        index: Dictionary containing lines as keys and line numbers
        as values.
        string_to_search: String to search for in the index.

    Returns:
        bool: True if the string is found in the index, False otherwise.
    """
    return string_to_search in index


# function to handle client connections
def handle_client_connection(client_socket: socket.socket,
                             address: Tuple[str, int],
                             ) -> None:
    """
    Handles a client connection and receives messages.

    Receives messages from the client connected to the socket
    and address specified.

    Args:
        client_socket (socket.socket): Socket connection with client.
        address (Tuple[str, int]): IP address and port of the client.

    Returns:
        None
    """
    requesting_ip: str = address[0]
    try:
        index = read_file(linuxpath)
    except FileNotFoundError:
        print('File not found:', linuxpath)
        client_socket.close()
        return
    while True:
        try:
            # Specify the maximum amount of data to receive
            received_data = client_socket.recv(1024)
            try:
                # Specify the correct encoding
                decoded_data = received_data.decode('utf-8')
            except UnicodeDecodeError:
                # Use an alternative encoding if utf-8 fails
                decoded_data = received_data.decode('iso-8859-1')
            # Strip any trailing null bytes and newlines
            data = decoded_data.rstrip('\x00\n')
            if not data:
                break

            if reread_on_query:
                index = read_file(linuxpath)
            start_time: float = time.time()
            if search_string_in_file(index, data):
                response = 'STRING EXISTS\n'
            else:
                response = 'STRING NOT FOUND\n'
            execution_time_ms: float = (time.time() - start_time) * 1000
            # Respond to the client
            client_socket.send(response.encode())

            # Ensure payload size and strip trailing \x00 characters
            if len(response) > 1024:
                print('Payload exceeds maximum size.')
                client_socket.close()
                return

            log_msg: str = (
                f'DEBUG: search_query={data}, '
                f'requesting_ip={requesting_ip}, '
                f'execution_time={execution_time_ms:.3f}ms, '
                f'timestamp={time.time()}'
            )
            print(log_msg)
        except socket.error as socket_error:
            print(
                f'Error receiving or sending data: {socket_error}')
            break
    client_socket.close()


# function that creates a server
def start_server() -> None:
    """
    Starts the server and listens for incoming connections.

    The function starts the server and listens for incoming connections on
    the specified SERVER. It accepts client connections, creates a new thread
    for each connection, and assigns the client handling to the
    'handle_client_connection' function.

    Returns:
        None
    """
    server_socket = None
    use_ssl = config.getboolean('Server', 'ssl')
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen()
        if use_ssl:
            # Create an SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=sslcert, keyfile=sslkey)
            # Wrap the server socket with SSL
            server_socket = context.wrap_socket(
                server_socket, server_side=True)
        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client_connection, args=(client_socket, address))
            client_thread.start()
    except (socket.error, ssl.SSLError) as connection_error:
        print(f'Error starting server: {connection_error}')
    except KeyboardInterrupt:
        pass
    finally:
        if server_socket:
            server_socket.close()


if __name__ == '__main__':
    start_server()

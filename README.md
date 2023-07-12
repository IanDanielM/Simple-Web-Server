# WebServer

This is a client-server application that allows clients to send queries to a server and receive responses based on the presence of a specific string in a file.documentation provides instructions for using the server and client modules, along with their configuration options and dependencies.

## Introduction

The server and client modules are designed to facilitate server-side and client-side functionality for handling connections, processing requests, and managing socket connections.

## Prerequisites

Before using the server and client modules, make sure you have the following prerequisites:

- Python 3.8 or later
- config.ini file with the required configuration options
- Certificate and key files (cert.pem and key.pem) if using SSL

## Installation

Install the required dependencies:

```pip install -r requirements.txt```


## Server.py

The `server.py` module handles server-side functionality, including listening for incoming connections, handling client connections, and processing client requests.

### Usage

To use the `server.py` module, follow these steps:

1. Set up the server socket by specifying the `SERVER_HOST` and `SERVER_PORT` variables in the `server.py` file.
    - the server_host is usually picked automatically but if you want to changed it you can input your own address
    - the server_port is specified asthe one requested in the instructions

2. `read_file` function: The read_file function is a helper function that reads the contents of a file and creates an index of lines. 
   - The function takes a file_name parameter, which specifies the name of the file to be read.
   - It attempts to open the file in read mode using open with the specified file_name.
   - The function creates an empty dictionary called index to store the lines and their corresponding line numbers.
   - It iterates over each line in the file using a for loop and the enumerate function to keep track of the line number.
   - For each line, it strips any leading or trailing whitespace using the strip method.
   - If the line is not already in the index, it adds it as a key with an empty list as its value.
   - It then appends the current line number to the list of line numbers for that line in the index.
   - Finally, it returns the index dictionary containing the lines and their corresponding line numbers.

4. `search_string_in_file` function: The search_string_in_file function is a helper function that searches for a string in the provided index.
   - The function takes two parameters: index and string_to_search.
   - The index parameter is a dictionary containing lines as keys and line numbers as values.
   - The string_to_search parameter is the string to search for in the index.
   - The function checks if the string_to_search is in the index using the in keyword.
   - It returns True if the string is found in the index, and False otherwise.

3. `handle_client_connection` function: The handle_client_connection function is responsible for handling a client connection and receiving messages from the client. 
   - It takes two parameters: client_socket (the socket connection with the client) and address (the IP address and port of the client). 
   - The function attempts to read the contents of a file specified by the linuxpath variable into an index using the read_file helper function. If the file is not found, it prints an error message and closes the client socket. 
   - Inside an infinite loop, the function receives data from the client using recv and decodes it based on the specified encoding (utf-8 or iso-8859-1). The received data is stripped of any trailing null bytes and newlines. 
   - If the reread_on_query flag is set to True, it reads the file again into the index. 
   - It searches for the received data in the index using search_string_in_file. If the data is found, it sends the response "STRING EXISTS\n" back to the client. Otherwise, it sends "STRING NOT FOUND\n". 
   - The function also handles potential errors that may occur during data receiving or sending, printing appropriate error messages. 
   - It logs debug information including the search query, requesting IP, execution time, and timestamp.


4. `start_server` function: The `start_server` function is responsible for starting the server and listening for incoming connections. Here's an overview of its functionality:
    - It reads the SSL configuration flag from the config.ini file to determine whether SSL encryption should be used for the server.
    - It creates a server socket using socket.socket and binds it to the SERVER_HOST and SERVER_PORT.
    - If SSL is enabled, it creates an SSL context, loads the certificate chain from cert.pem and key.pem, and wraps the server socket with SSL using wrap_socket.
    - The function enters a loop to continuously listen for incoming client connections using accept.
    - For each new client connection, it creates a new thread by calling handle_client_connection and passing the client socket and address as arguments.
    - The server continues to accept new connections and spawn threads to handle them until the program is interrupted by a keyboard interrupt (Ctrl+C).
    - It handles potential errors during server setup or keyboard interrupt, printing appropriate error messages.
    - Finally, when the server is no longer needed, it closes the server socket.

5. Run the `start_server` function to start the server:
   ```
   python server.py
   ```

### Configuration

The server can be configured using the `config.ini` file located in the same directory as the `server.py` module. The following configuration options are available:

- `[Server]`
  - `linuxpath`: The path to the file to be searched by the server.
  - `REREAD_ON_QUERY`: A boolean value indicating whether the server should re-read the file on each query.
  - `ssl`: A boolean value indicating whether to use SSL/TLS for secure connections.

### Dependencies

The `server.py` module requires the following dependencies: `io`, `socket`, `threading`, `configparser`, `time`, and `ssl`.

## Client.py

The `client.py` module provides client-side functionality, including connecting to the server, sending requests, and managing socket connections.

### Usage

To use the `client.py` module, follow these steps:

1. Set up the client socket connection by specifying the `SERVER_HOST` and `SERVER_PORT` variables in the `client.py` file.

2. `connect_to_server()` function:
   - This function establishes a connection to the server by creating a socket using `socket.socket()` and connecting it to the server's address and port.
   - If SSL is enabled, it creates an SSL context, loads the certificate chain, and performs an SSL handshake with the server.
   - If SSL is not enabled, it connects to the server without SSL.
   - It returns the client socket connected to the server.

3. `close_client_socket(client_socket)` function:
   - This function closes the client socket if it is not `None`.
   - It takes the `client_socket` as an argument and calls the `close()` method on it to close the socket connection.

4. `reconnect(client_socket)` function:
   - This function attempts to reconnect to the server in case of a connection failure.
   - It takes the `client_socket` as an argument, closes it using `close_client_socket()`, waits for a short duration, and then attempts to reconnect by calling `connect_to_server()`.
   - It repeats this process for a maximum of 5 attempts.
   - If the reconnection is successful, it returns the new client socket connected to the server.
   - If the maximum number of attempts is reached without a successful reconnection, it raises a `ConnectionRefusedError` indicating the failure.

5. `managed_socket_connection()` context manager:
   - This context manager handles the opening and closing of a client socket connection.
   - It uses the `connect_to_server()` function to obtain a client socket and yields it for use within the `with` block.
   - When the `with` block is exited, either normally or due to an error, the context manager automatically closes the client socket using `close_client_socket()`.

6. send_request function: This function sends a request message to the server using the client socket obtained from the managed_socket_connection context manager.
   - Inside a while loop, the function prompts the user to enter a string or ':q' to quit. 
   - If the user enters ':q', the loop breaks and the function exits. 
   - Otherwise, it encodes the entered message as bytes and sends it to the server using client_socket.send(). 
   - It then waits for a response from the server using client_socket.recv() and decodes and prints the response. 
   - The function also handles potential errors that may occur during data sending or receiving, printing appropriate error messages and attempting to reconnect if necessary. If an unhandled exception occurs, it breaks out of the loop.

These functions provide the necessary functionality for the client-side communication with the server, including establishing connections, managing socket resources, reconnecting in case of failures, and sending requests to the server.

7. Run the `send_request` function to send a request to the server:
   ```
   python client.py
   ```

### Configuration

The client can be configured using the `config.ini` file located in the same directory as the `client.py` module. The following configuration option is available:

- `[Client]`
  - `ssl`: A boolean value indicating whether to use SSL/TLS for secure connections.

### Dependencies

The `client.py` module requires the following dependencies: `socket`, `ssl`, `configparser`, `time`, `typing`, and `contextlib`.

## Troubleshooting

If you encounter any issues or errors while using the server and client modules, refer to the following troubleshooting steps:

- Ensure that the necessary

 configuration files (`config.ini`, `cert.pem`, and `key.pem`) are available and properly configured according to your specific setup.
- Double-check that the required dependencies are installed correctly by running `pip install -r requirements.txt`.
- Verify that the server and client modules are running on the correct host and port as specified in their respective files.




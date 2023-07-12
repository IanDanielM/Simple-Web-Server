# import sys
# import os
# import socket
# import csv
# import time
# from webserver.server import (SERVER_HOST, SERVER_PORT)

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# def test_execution_time_and_queries_per_second() -> None:
#     """
#     Test the execution time for different file sizes and the server's ability
#     to handle multiple queries per second.

#     Returns:
#         None
#     """
#     # Test different file sizes from 10,000 to 1,000,000
#     file_sizes = range(10000, 1000001, 100000)
#     # Test different numbers of queries per second
#     queries_per_second = range(1, 51, 5)
#     # Test different threshold values in seconds
#     thresholds = range(1, 6)

#     for threshold in thresholds:
#         with open(
#             f'execution_times_and_queries_per_second_{threshold}.csv', 'w'
#         ) as file:
#             writer = csv.writer(file)
#             writer.writerow(['File Size', 'Queries per Second',
#                              'Execution Time (s)', 'Average Response Time (s)',
#                              'Threshold (s)'])

#             for file_size in file_sizes:
#                 for qps in queries_per_second:
#                     # Create a mock client socket and connect to the server
#                     client_socket = socket.socket()
#                     client_socket.connect((SERVER_HOST, SERVER_PORT))
#                     message = b'0' * file_size
#                     start_time = time.time()
#                     response_times = []
#                     for _ in range(qps):
#                         client_socket.send(message)
#                         response_time = time.time() - start_time
#                         response_times.append(response_time)
#                         time.sleep(1 / qps)
#                     execution_time = time.time() - start_time
#                     average_response_time = sum(response_times) / len(
#                                                        response_times)
#                     writer.writerow([file_size, qps, execution_time,
#                                      average_response_time, threshold])

#                     try:
#                         # Assert that execution time and average response time,
#                         #  are below the threshold
#                         assert_message: str = "Execution time exceeds"
#                         avg_message: str = "Average response time exceeds"
#                         assert execution_time < threshold, assert_message
#                         f"threshold for file size {file_size}"
#                         assert average_response_time < threshold, avg_message
#                         f"threshold for {qps} queries per second"
#                     except AssertionError as e:
#                         print(e)
#                     finally:
#                         client_socket.close()

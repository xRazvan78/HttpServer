import socket

HOST = "127.0.0.1"
PORT = 8080


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"Server is listening on {HOST}:{PORT}")

    client_socket, client_address = server_socket.accept()
    print("Client connected from:", client_address)

    request = client_socket.recv(1024)
    print("Received request:")
    print(request.decode())
    print()

    body = "Hello from my own HTTP server"
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )

    client_socket.sendall(response.encode())
    client_socket.close()
    server_socket.close()

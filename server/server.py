import os
import socket

HOST = "127.0.0.1"
PORT = 8080

def build_http_response(status, body, content_type):
    return (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"Server is listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print("Client connected from:", client_address)

        request = client_socket.recv(1024)
        request_text = request.decode()
        lines = request_text.split("\r\n")
        request_line = lines[0]
        method, path, version = request_line.split(" ")

        status = "500 Internal Server Error"
        body = ""
        content_type = "text/plain"

        print("Method: ", method, " Path: ", path)

        print("Received request:")
        print(request.decode())
        print()

        static_dir = os.path.abspath("static")

        if path == "/":
            requested_path = "index.html"
        else:
            requested_path = path.lstrip("/") + ".html"

        safe_path = os.path.normpath(requested_path)
        filename = os.path.abspath(os.path.join(static_dir, safe_path))

        if not filename.startswith(static_dir):
            body = "<h1>403 Forbidden</h1>"
            status = "403 Forbidden"
            content_type = "text/html"
        else:
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    body = file.read()
                    status = "200 OK"
                    content_type = "text/html"
            except FileNotFoundError:
                body = "<h1>404 Not Found</h1>"
                status = "404 Not Found"
                content_type = "text/html"

        response = build_http_response(status, body, content_type)

        client_socket.sendall(response.encode())
        client_socket.close()
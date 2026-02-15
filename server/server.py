import os
import socket

HOST = "127.0.0.1"
PORT = 8080
STATIC_DIR = os.path.abspath("static")

def build_http_response(status, body, content_type):
    if isinstance(body, str):
        body = body.encode("utf-8")

    headers = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    ).encode("utf-8")

    return headers + body

def get_content_type(filename):
    if filename.endswith(".html"):
        return "text/html"
    elif filename.endswith(".css"):
        return "text/css"
    elif filename.endswith(".js"):
        return "application/javascript"
    elif filename.endswith(".png"):
        return "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    elif filename.endswith(".gif"):
        return "image/gif"
    else:
        return "application/octet-stream"

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Server is listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print("Client connected from:", client_address)

        request = client_socket.recv(1024)

        if not request:
            client_socket.close()
            continue

        request_text = request.decode(errors="ignore")
        lines = request_text.split("\r\n")
        request_line = lines[0]

        try:
            method, path, version = request_line.split(" ")
        except ValueError:
            client_socket.close()
            continue

        body = ""

        print("Method: ", method, " Path: ", path)

        print("Received request:")
        print(request.decode())
        print()

        if path == "/":
            requested_path = "index.html"
        else:
            requested_path = path.lstrip("/")
            if "." not in os.path.basename(requested_path):
                requested_path += ".html"

        safe_path = os.path.normpath(requested_path)
        filename = os.path.abspath(os.path.join(STATIC_DIR, safe_path))

        if not filename.startswith(STATIC_DIR):
            body = "<h1>403 Forbidden</h1>"
            status = "403 Forbidden"
            content_type = "text/html"
        else:
            try:
                content_type = get_content_type(filename)

                if content_type.startswith("image"):
                    with open(filename, "rb") as file:
                        body = file.read()
                else:
                    with open(filename, "r", encoding="utf-8") as file:
                        body = file.read()

                status = "200 OK"

            except FileNotFoundError:
                body = "<h1>404 Not Found</h1>"
                status = "404 Not Found"
                content_type = "text/html"

        print("Sending response:", status)
        response = build_http_response(status, body, content_type)

        client_socket.sendall(response)
        client_socket.close()
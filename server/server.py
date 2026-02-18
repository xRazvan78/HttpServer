import os
import socket
import json
import threading
import datetime

HOST = "127.0.0.1"
PORT = 8080
STATIC_DIR = os.path.abspath("static")
MAX_BODY_SIZE = 1024 * 1024


def build_http_response(status, body, content_type, extra_headers=None):
    if isinstance(body, str):
        body = body.encode("utf-8")

    headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(body)),
        "Connection": "close",
        "Server": "CustomPythonHTTPServer"
    }

    if extra_headers:
        headers.update(extra_headers)

    header_text = f"HTTP/1.1 {status}\r\n"
    for key, value in headers.items():
        header_text += f"{key}: {value}\r\n"
    header_text += "\r\n"

    return header_text.encode("utf-8") + body


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


ROUTES = {}


def route(path, methods=("GET",)):
    def decorator(func):
        ROUTES[path] = {
            "methods": methods,
            "handler": func
        }
        return func
    return decorator


@route("/hello")
def hello_handler(method, path, query):
    name = query.get("name", "Guest")
    age = query.get("age", "unknown")
    return "200 OK", f"<h1>Hello {name}, you are {age} years old!</h1>", "text/html"


@route("/api/time")
def time_handler(method, path, query):
    now = datetime.datetime.now().isoformat()
    return "200 OK", json.dumps({"time": now}), "application/json"


@route("/api/echo", methods=("POST",))
def echo_handler(method, path, params):
    return "200 OK", json.dumps(params), "application/json"


def parse_query(query_string):
    params = {}
    if query_string:
        pairs = query_string.split("&")
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value
    return params


def handle_client(client_socket, client_address):
    try:
        client_socket.settimeout(5)

        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = client_socket.recv(1024)
            if not chunk:
                return
            buffer += chunk

        header_bytes, _, remaining_bytes = buffer.partition(b"\r\n\r\n")
        header_text = header_bytes.decode(errors="ignore")
        header_lines = header_text.split("\r\n")
        request_line = header_lines[0]

        headers = {}
        for line in header_lines[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key.strip().lower()] = value.strip()

        content_length = int(headers.get("content-length", 0))

        if content_length > MAX_BODY_SIZE:
            response = build_http_response(
                "413 Payload Too Large",
                "<h1>413 Payload Too Large</h1>",
                "text/html"
            )
            client_socket.sendall(response)
            return

        body = remaining_bytes
        while len(body) < content_length:
            body += client_socket.recv(1024)
        body = body[:content_length]

        body_text = body.decode("utf-8", errors="strict")
        content_type = headers.get("content-type", "")

        if content_type.startswith("application/json"):
            try:
                post_params = json.loads(body_text) if body_text else {}
            except json.JSONDecodeError:
                response = build_http_response(
                    "400 Bad Request",
                    "<h1>400 Bad Request</h1>",
                    "text/html"
                )
                client_socket.sendall(response)
                return
        else:
            post_params = parse_query(body_text)

        try:
            method, full_path, version = request_line.split(" ")

            if "?" in full_path:
                path, query_string = full_path.split("?", 1)
            else:
                path = full_path
                query_string = ""

            query_params = parse_query(query_string)
        except ValueError:
            response = build_http_response(
                "400 Bad Request",
                "<h1>400 Bad Request</h1>",
                "text/html"
            )
            client_socket.sendall(response)
            return

        params = query_params if method == "GET" else post_params

        if path in ROUTES:
            if method in ROUTES[path]["methods"]:
                handler = ROUTES[path]["handler"]
                status, body, content_type = handler(method, path, params)
                response = build_http_response(status, body, content_type)
                client_socket.sendall(response)
                return
            else:
                allowed = ", ".join(ROUTES[path]["methods"])
                response = build_http_response(
                    "405 Method Not Allowed",
                    "<h1>405 Method Not Allowed</h1>",
                    "text/html",
                    extra_headers={"Allow": allowed}
                )
                client_socket.sendall(response)
                return

        if path == "/":
            requested_path = "index.html"
        else:
            requested_path = path.lstrip("/")
            if "." not in os.path.basename(requested_path):
                requested_path += ".html"

        safe_path = os.path.normpath(requested_path)
        filename = os.path.abspath(os.path.join(STATIC_DIR, safe_path))

        if not filename.startswith(STATIC_DIR):
            response = build_http_response(
                "403 Forbidden",
                "<h1>403 Forbidden</h1>",
                "text/html"
            )
            client_socket.sendall(response)
            return

        try:
            content_type = get_content_type(filename)

            if content_type.startswith("image"):
                with open(filename, "rb") as file:
                    body = file.read()
            else:
                with open(filename, "r", encoding="utf-8") as file:
                    body = file.read()

            response = build_http_response("200 OK", body, content_type)
        except FileNotFoundError:
            response = build_http_response(
                "404 Not Found",
                "<h1>404 Not Found</h1>",
                "text/html"
            )

        client_socket.sendall(response)

    finally:
        client_socket.close()


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    server_socket.settimeout(1)

    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
            except socket.timeout:
                continue

            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            thread.start()

    except KeyboardInterrupt:
        print("\nShutting down server...")

    finally:
        server_socket.close()
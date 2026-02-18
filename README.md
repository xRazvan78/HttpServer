# HTTP Server from Scratch (Python)

A minimal HTTP/1.1 server implemented from scratch using raw TCP sockets in Python.
No web frameworks and no built-in HTTP server libraries are used.

The purpose of this project is to understand how web servers and frameworks work internally,
including request parsing, routing, static file handling, and concurrency.

# Features

- Raw TCP socket-based server
- Manual HTTP request parsing (method, path, headers, body)
- Manual HTTP response construction
- Basic decorator-based routing system
- Query parameter parsing
- JSON request and response handling
- Static file serving from a `static` directory
- Directory traversal protection
- Request body size limiting (413 Payload Too Large)
- Proper error handling (400, 403, 404, 405, 413)
- Thread-per-request concurrency model
- Graceful shutdown with Ctrl+C support


# Tech Stack

- Python 3.x
- Standard library only (`socket`, `threading`, `json`, `os`, `datetime`)

# Notes

This project is intended for educational purposes and is not production-ready.

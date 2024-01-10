import logging
from http import server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run(server_class=server.HTTPServer, handler_class=server.BaseHTTPRequestHandler):
    """Run process.

    Args:
        server_class (_type_, optional): _description_. Defaults to server.HTTPServer.
        handler_class (_type_, optional): _description_. Defaults to server.BaseHTTPRequestHandler.
    """
    server_address = ("", 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


if __name__ == "__main__":
    run()

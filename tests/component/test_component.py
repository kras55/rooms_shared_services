import logging
import socket

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


def test_component():
    """Test component.

    Raises:
        ConnectionError: Connection failed.
    """
    port = 8000
    host = "main_component_run"
    timeout = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # presumably
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except Exception:
        logger.info("Connection failed")
        raise ConnectionError("Connection failed")
    else:
        sock.close()
        logger.info("Connection succeded")

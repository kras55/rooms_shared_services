import logging

from rooms_shared_services.src.logging.http_logger import get_logger


def test_default_logger():
    """Test default logger."""
    logger = get_logger(name=__name__, use_http=True, use_stream=True)
    assert isinstance(logger, logging.Logger)
    assert len(logger.handlers) == 2
    http_handler = logger.handlers[0]
    logger.info(http_handler)
    logger.info("Hello world")

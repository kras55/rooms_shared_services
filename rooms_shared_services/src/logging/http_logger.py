import logging
from logging.handlers import HTTPHandler

from rooms_shared_services.src.logging.settings import Settings


def get_logger(name: str, use_http: bool = False, use_stream: bool = True) -> logging.Logger:
    """Get default logger.

    Args:
        name (str): _description_
        use_http (bool): _description_. Defaults to False.
        use_stream (bool): _description_. Defaults to True.

    Returns:
        logging.Logger: _description_
    """
    logger = logging.getLogger(name)
    if use_http:
        settings = Settings()  # type: ignore
        http_handler = HTTPHandler(
            settings.host,
            settings.path,
            method="POST",
            secure=settings.secure,
            context=None,
        )
        http_handler.setLevel(logging.INFO)
        http_handle_format = logging.Formatter("%(levelname)s - %(message)s - %(asctime)s")
        http_handler.setFormatter(http_handle_format)
        logger.addHandler(http_handler)
    if use_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handle_format = logging.Formatter("%(process)s - %(message)s")
        stream_handler.setFormatter(stream_handle_format)
        logger.addHandler(stream_handler)
    return logger

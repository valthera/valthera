# logger_config.py

import logging
import sys

def setup_logger(
    name: str = "document_editor",
    log_file: str = "document_editor.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Sets up and returns a logger configured to log messages to both the console and a file.

    Parameters:
        name (str): The name of the logger.
        log_file (str): The filename for logging output.
        level (int): The logging level (default is logging.INFO).

    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler: log messages to a file.
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Stream handler: log messages to the console.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    stream_handler.setFormatter(stream_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

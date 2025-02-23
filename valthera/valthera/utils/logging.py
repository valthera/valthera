import logging


def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup a logger; can be used to log to a file."""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Example usage:
# logger = setup_logger('example_logger', 'example.log')
# logger.info('This is an info message')
# logger.error('This is an error message')

import logging
import sys

# Define a custom formatter to include more details if needed
LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
)


# Define a basic logging configuration function
def setup_logging(log_level: str = "INFO"):
    """Sets up basic stream logging.

    Args:
        log_level (str): The minimum log level to output (e.g., "INFO", "WARNING").
    """
    # Ensure valid log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers to avoid duplicate logs
    # if this is called multiple times (though ideally it's called once at startup)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create a handler for stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(numeric_level)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter(LOG_FORMAT)
    stream_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(stream_handler)

    # You can also add file handlers here if needed
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(formatter)
    # root_logger.addHandler(file_handler)

    logging.info(f"Logging configured with level {log_level.upper()}.")


# Example of how to get a logger in other modules:
# import logging
# logger = logging.getLogger(__name__)
# logger.info("This is an info message.")

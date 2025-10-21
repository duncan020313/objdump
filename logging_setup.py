import logging
import os
from tqdm import tqdm


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        # Get the original formatted message
        log_message = super().format(record)
        
        # Add color to the log level
        level_name = record.levelname
        if level_name in self.COLORS:
            colored_level = f"{self.COLORS[level_name]}{level_name}{self.RESET}"
            # Replace the level name in the message with the colored version
            log_message = log_message.replace(level_name, colored_level, 1)
        
        return log_message


class TqdmLogHandler(logging.StreamHandler):
    """Custom handler that redirects log output to tqdm.write."""
    
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)


def configure_logging(debug: bool = False) -> None:
    """Configure root logger for structured, concise output with colored log levels.

    Uses INFO by default; DEBUG if JI_DEBUG env var is set.
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Create a custom handler with colored formatter that uses tqdm.write
    handler = TqdmLogHandler()
    formatter = ColoredFormatter("%(levelname)s %(name)s:%(lineno)d: %(message)s")
    handler.setFormatter(formatter)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers to avoid duplicates
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    
    # Add our colored handler
    root_logger.addHandler(handler)



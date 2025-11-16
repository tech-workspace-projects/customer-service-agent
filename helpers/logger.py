import logging
import os
from logging.handlers import RotatingFileHandler
from threading import Lock


class Logger:
    """
    Singleton logger class that ensures only one logger instance exists throughout the application.
    Provides centralized logging with both file and console handlers.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """
        Ensures only one instance of the Logger class is created (Singleton pattern).

        Returns:
            Logger: The singleton Logger instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initializes the logger instance with file and console handlers.
        This method is only executed once due to the singleton pattern.
        """
        if self._initialized:
            return

        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create logger
        self.logger = logging.getLogger('ecommerce_chatbot')
        self.logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler with rotation (10MB max, keep 5 backup files)
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self._initialized = True

    def get_logger(self):
        """
        Returns the singleton logger instance.

        Returns:
            logging.Logger: The configured logger instance.
        """
        return self.logger

    def set_level(self, level: int):
        """
        Sets the logging level for the logger and all its handlers.

        Args:
            level (int): Logging level (e.g., logging.DEBUG, logging.INFO, logging.ERROR).
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

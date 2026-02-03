import logging
import logging.handlers
import os
from typing import Callable, Optional


class Logger:
    """Logger class implemented with Singleton pattern and dynamic method binding design."""

    _instance = None
    _initialized = False

    _LOG_LEVEL_METHODS = {'debug', 'info', 'warning', 'error', 'critical', 'exception'}

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance of the Logger class.

        Args:
            *args: Variable length positional arguments
            **kwargs: Variable length keyword arguments

        Returns:
            Logger: The singleton instance of the Logger class
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the logging system.

        This method sets up the root logger, configures its log level, clears any existing handlers,
        and loads configuration from the settings system.
        """
        if self._initialized:
            return
        self._initialized = True

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        self._configure_from_settings()

    def _configure_from_settings(self):
        """Read logging configuration from the settings system and apply it.

        The method builds handler specifications, clears existing handlers, and creates new handlers
        based on the configuration.
        """
        self._handler_registry = {'file': self._create_file_handler}
        handler_specs = self._build_handler_specs()

        # Clear all existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        for spec in handler_specs:
            handler = self._create_handler(spec)
            if handler:
                self.logger.addHandler(handler)

        self.logger.setLevel(logging.DEBUG)

    def _build_handler_specs(self) -> list[dict]:
        handler_specs = []
        handler_specs.append(
            {
                'type': 'file',
                'params': {
                    'file_path': "/var/log/ub-pkg-manager.log",
                    'max_bytes': 10485760,
                    'backup_count': 2,
                    'level': logging.DEBUG,
                    'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    'date_format': "%Y-%m-%d %H:%M:%S",
                },
            }
        )

        return handler_specs

    def _create_handler(self, spec: dict) -> Optional[logging.Handler]:
        """Abstract factory method for creating logging handlers.

        Dynamically creates the corresponding logging handler based on the handler type and parameters.

        Args:
            spec (dict): Handler specification containing 'type' and 'params' keys

        Returns:
            Optional[logging.Handler]: The created logging handler instance, or None if creation fails

        Raises:
            ValueError: If an unsupported handler type is specified
        """
        handler_type = spec['type']
        handler_params = spec['params']
        create_func = self._handler_registry.get(handler_type)
        if not create_func:
            raise ValueError(f"Unsupported log handler type: {handler_type}")

        return create_func(**handler_params)

    def _create_file_handler(self, **kwargs) -> logging.Handler:
        """Create a file logging handler with rotation support.

        This method creates a RotatingFileHandler that automatically rotates log files when they reach
        a specified size, keeping a configurable number of backup files.

        Args:
            **kwargs: Keyword arguments for the file handler
                file_path (str): Path to the log file
                max_bytes (int): Maximum size of a log file before rotation
                backup_count (int): Number of backup files to keep
                level (int): Logging level for the handler
                format (str): Log message format string
                date_format (str): Date format string for log messages

        Returns:
            logging.Handler: The created file logging handler
        """
        file_path = kwargs.get('file_path')

        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=kwargs.get('max_bytes'), backupCount=kwargs.get('backup_count'), encoding='utf-8'
        )

        handler.setLevel(kwargs.get('level', logging.DEBUG))
        formatter = logging.Formatter(kwargs.get('format'), kwargs.get('date_format'))
        handler.setFormatter(formatter)

        return handler

    def __getattr__(self, name: str) -> Callable:
        """Dynamically handle logging level method calls.

        When an attribute that doesn't exist is accessed, if the attribute name is a supported logging
        level method, this method returns a function that calls the corresponding method on the underlying logger.
        Otherwise, it raises an AttributeError.

        Args:
            name (str): The name of the attribute being accessed

        Returns:
            Callable: A function that calls the corresponding logging method on the underlying logger

        Raises:
            AttributeError: If the attribute name is not a supported logging level method
        """
        if name in self._LOG_LEVEL_METHODS:
            logger_method = getattr(self.logger, name)
            return lambda *args, **kwargs: logger_method(*args, **kwargs)

        raise AttributeError(f"Logger object has no attribute '{name}'")

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """Get a logger with the specified name.

        If an instance of the Logger class doesn't exist yet, it will be created first.
        If no name is provided, the root logger instance is returned.

        Args:
            name (Optional[str]): The name of the logger to get, or None for the root logger

        Returns:
            logging.Logger: The requested logger instance
        """
        if cls._instance is None:
            cls()

        return logging.getLogger(name) if name else cls._instance.logger

    def reload_config(self):
        """Reload logging configuration.

        This method clears all existing handlers and reloads the logging configuration from the settings system,
        allowing for dynamic updates to logging settings without restarting the application.
        """
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        self._configure_from_settings()


logger = Logger()

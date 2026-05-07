import logging
from logging.config import dictConfig
# to make condition on loggers variable/setup
from SettingsConfigDict import DevConfig, config

class EmailObfuscationFilter(logging.Filter):
    def __init__(self, name:str = "", obfuscate_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscate_length = obfuscate_length

    def obfuscated(self, email: str, obfuscated_length: int) -> str:
        characters = email[: obfuscated_length]
        first, last = email.split("@")
        return characters + ("*" * len(first) * obfuscated_length) + "@" + last

    """
    Custom filter to obfuscate email addresses in logs.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            record.email = self.obfuscated(record.email, self.obfuscate_length)
        return True

def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,  # Disable the existing/predefined loggers
            # setting up filters
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    # every string that is generated for a request so that it can be displayed in logs is uuid
                    # Universally Unique Identifier it is unique for every request
                    "uuid_length": 8 if config.ENV_STATE == "dev" else 32, # length of the uuid
                      "default_value": "-"  # if no uuid then it will be replaced with -
                },
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscate_length": 2 if isinstance(config, DevConfig) else 0,  # how many characters to show in email
                },
            },
            # Define/Setup all of the formatters
            "formatters": {
                # To display logs on console
                "console": {
                    "class": "logging.Formatter", 
                    "datefmt": "%Y-%m-%dT%H:%S", 
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s", # s at the end means that it is a string and d for integer
                },
                # To save logs in file
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%S",
                    "format": "%(asctime)s %(msecs)03d %(levelname)-8s %(correlation_id)s %(name)s %(lineno)d %(message)s", 
                    #  %(levelname)-8s -8s means that it will take 8 spaces for the level name and if it is less than 8 spaces it will be padded with space
                },
            },
            # Setup the handlers
            "handlers": {
                # Handler for console logging
                "default": {
                    "class": "rich.logging.RichHandler", # rich library a good library to display logs
                    "level": "DEBUG", # to which level the logs should be displayed
                    "formatter": "console", # which formatter should be used
                    "filters": ["correlation_id", "email_obfuscation"],  # add the filter to the handler
                },
                # Handler for file logging
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024 * 5,  # 5MB each file
                    "backupCount": 5,  # tell how many files should be kept id 3rd file is to created 1st one got deleted
                    "encoding": "utf8",
                    "filters": ["correlation_id","email_obfuscation"],  # add the filter to the handler
                },
            },
            # Setup the loggers
            "loggers": {
                "storeapi": {
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,  # mot send any log to root logger --> root.storeapi.routers.post
                },
                # Setting up the loggers for imported/buildin libraries
                "uvicorn": {
                    "handlers": ["default", "rotating_file"], # add the handlers tells where to do logs
                    "level": "INFO",
                },
                "databases": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },
                "aiosqlite": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },
            },
        }
    )

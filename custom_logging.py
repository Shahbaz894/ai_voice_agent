import logging
import os


class VoiceAgentLogger:

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self.logger = logging.getLogger("VoiceAgent")
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # File handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, "voice_agent.log")
        )
        file_handler.setFormatter(formatter)

        # Error file handler
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, "error.log")
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

from pydantic import BaseSettings


class CronSettings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "%(asctime)s :: %(levelname)s :: %(funcName)s :: %(message)s"
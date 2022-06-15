from pydantic import BaseSettings

class RedisSettings(BaseSettings):

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0


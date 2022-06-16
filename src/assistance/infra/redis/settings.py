from pydantic import BaseSettings

class RedisSettings(BaseSettings):
    """
        Redis settings. see
        https://github.com/kubernetes/kubernetes/issues/60099
        https://www.pedidos.econo.unlp.edu.ar/issues/22743
    """
    redis_host: str = "assistance_redis"
    redis_port: int = 6379
    redis_db: int = 0


from pydantic import BaseSettings


class GoogleSettings(BaseSettings):
    google_user: str = 'sistemas@econo.unlp.edu.ar'
    google_domain: str = 'econo.unlp.edu.ar'
    credentials_file: str = 'credentials/credentials.json'
    google_repo: str = "MOCK"

    google_redis_host: str = "assistance_redis"
    google_redis_port: int = 6379
    google_redis_db: int = 0
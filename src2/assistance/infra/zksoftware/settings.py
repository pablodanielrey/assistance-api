
from pydantic import BaseSettings


class ZkSettings(BaseSettings):
    ip: str = '127.0.0.1'
    port: int = 4370 
    timeout: int = 5
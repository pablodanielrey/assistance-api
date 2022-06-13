
from pydantic import BaseSettings


class ZkSettings(BaseSettings):
    ip: str = '127.0.0.1'
    port: int = 4370 
    timeout: int = 5
    ommit_ping: bool = True
    force_udp: bool = False
    verbose: bool = False
from pydantic import BaseSettings


class GoogleSettings(BaseSettings):
    google_user: str = 'sistemas@econo.unlp.edu.ar'
    credentials_file: str = 'credentials/credentials.json'


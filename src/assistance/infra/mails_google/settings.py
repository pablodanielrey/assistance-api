from pydantic_settings import BaseSettings

class MailsSettings(BaseSettings):

    from_email: str
    message: str
    subject_prefix: str
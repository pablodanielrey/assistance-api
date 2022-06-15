from pydantic import BaseModel, validator
import datetime


class AttLog(BaseModel):
    uid: int
    user_id: str
    timestamp: datetime.datetime
    status: int
    punch: int

    @validator('timestamp', pre=True)
    def timestamp_conversion(cls, t):
        return t

    class Config:
        orm_mode = True
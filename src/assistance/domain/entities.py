import datetime
from pydantic import BaseModel


class AttLog(BaseModel):
    date : datetime.date
    time: datetime.time
    dni: str


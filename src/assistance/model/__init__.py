import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model_utils import Base
from .entities import *

port = os.environ.get('ASSISTANCE_DB_PORT', 5432)

engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
    os.environ['ASSISTANCE_DB_USER'],
    os.environ['ASSISTANCE_DB_PASSWORD'],
    os.environ['ASSISTANCE_DB_HOST'],
    port,
    os.environ['ASSISTANCE_DB_NAME']
), echo=True)
Session = sessionmaker(bind=engine)



from .AssistanceModel import AssistanceModel

__all__ = [
    'AssistanceModel'
]

def crear_tablas():
    Base.metadata.create_all(engine)

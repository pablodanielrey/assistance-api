import os
import contextlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model_utils import Base
from .entities import *

port = os.environ.get('ASSISTANCE_DB_PORT', 5432)

@contextlib.contextmanager
def obtener_session():
    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_HOST'],
        port,
        os.environ['ASSISTANCE_DB_NAME']
    ), echo=True)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()



from .AssistanceModel import AssistanceModel

__all__ = [
    'AssistanceModel'
]

def crear_tablas():
    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_HOST'],
        port,
        os.environ['ASSISTANCE_DB_NAME']
    ), echo=True)
    Base.metadata.create_all(engine)
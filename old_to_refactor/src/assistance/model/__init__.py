import os
import contextlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model_utils import Base

@contextlib.contextmanager
def obtener_session():
    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
        os.environ['ASSISTANCE_DB_USER'],
        os.environ['ASSISTANCE_DB_PASSWORD'],
        os.environ['ASSISTANCE_DB_HOST'],
        os.environ.get('ASSISTANCE_DB_PORT', 5432),
        os.environ['ASSISTANCE_DB_NAME']
    ), echo=False)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
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
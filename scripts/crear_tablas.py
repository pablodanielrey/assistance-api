
if __name__ == '__main__':

    import os
    from sqlalchemy import create_engine
    from model_utils import Base
    from .entities import *

    def crear_tablas():
        engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
            os.environ['ASSISTANCE_DB_USER'],
            os.environ['ASSISTANCE_DB_PASSWORD'],
            os.environ['ASSISTANCE_DB_HOST'],
            os.environ.get('ASSISTANCE_DB_PORT', 5432),
            os.environ['ASSISTANCE_DB_NAME']
        ), echo=True)
        Base.metadata.create_all(engine)    

    crear_tablas()

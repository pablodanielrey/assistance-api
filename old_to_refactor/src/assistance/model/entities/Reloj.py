from sqlalchemy import Column, String, ForeignKey, Boolean, Date, Integer
from sqlalchemy.orm import relationship
from model_utils import Base

class Reloj(Base):

    __tablename__ = 'reloj'

    nombre = Column(String)
    descripcion = Column(String)
    modelo = Column(String)
    marca = Column(String)
    ip = Column(String)
    puerto = Column(Integer)
    mascara = Column(String)
    router = Column(String)
    algoritmo = Column(String)
    zona_horaria = Column(String)
    activo = Column(Boolean)
    url_api = Column(String)

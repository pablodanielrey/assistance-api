from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from model_utils import Base


import json
import requests

class Usuario(Base):

    __tablename__ = 'usuario'

    dni = Column(String, unique=True)
    horarios = relationship('Horario', back_populates='horario')

    def resolveUser(self):
        ''' se hace la llamada rest a la api de usuarios '''
        r = requests.get('http://usuarios.econo.unlp.edu.ar/users/api/v1.0/usuarios/{}'.format(self.id))
        if r.ok:
            return r.json()
        else:
            return None

import os
#from dotenv import load_dotenv
#load_dotenv()

"""
    ###############
    para la cache de usuarios
"""
from model_utils.API import API
from model_utils.UserCache import UserCache
from model_utils.UsersAPI import UsersAPI

REDIS_HOST = os.environ.get('TELEGRAM_BOT_REDIS')
REDIS_PORT = 30001

OIDC_URL = os.environ['OIDC_URL']
OIDC_CLIENT_ID = os.environ['OIDC_CLIENT_ID']
OIDC_CLIENT_SECRET = os.environ['OIDC_CLIENT_SECRET']

USERS_API = os.environ['USERS_API_URL']

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

_API = API(url=OIDC_URL, 
              client_id=OIDC_CLIENT_ID, 
              client_secret=OIDC_CLIENT_SECRET, 
              verify_ssl=VERIFY_SSL)

_USERS_API = UsersAPI(api_url=USERS_API, api=_API)

#cache_usuarios = UserCache(host=REDIS_HOST, 
#                            port=REDIS_PORT, 
#                            user_getter=_USERS_API._get_user_uuid,
#                            users_getter=_USERS_API._get_users_uuid,
#                            user_getter_dni=_USERS_API._get_user_dni)

api = _API
token = api._get_token()

#usuario = cache_usuarios.obtener_usuario_por_dni('23106377', token=token)
#
#print("ciudad {}".format(usuario["ciudad"]))
#print("dirty {}".format(usuario["dirty"]))
#print("legajo {}".format(usuario["legajo"]))
#print("avatar {}".format(usuario["avatar"]))
#print("id {}".format(usuario["id"]))
#print("creado {}".format(usuario["creado"]))
#print("eliminado {}".format(usuario["eliminado"]))
#print("direccion {}".format(usuario["direccion"].encode('utf-8')))
#print("nacimiento {}".format(usuario["nacimiento"]))
#print("mails {}".format(usuario["mails"]))
#print("genero {}".format(usuario["genero"]))
#print("actualizado {}".format(usuario["actualizado"]))
#print("apellido {}".format(usuario["apellido"]))
#print("pais {}".format(usuario["pais"]))
#print("nombre {}".format(usuario["nombre"]))
#print("google {}".format(usuario["google"]))
#print("dni {}".format(usuario["dni"]))
#print("tipo {}".format(usuario["tipo"]))
#print("telefonos {}".format(usuario["telefonos"]))

usuarioBase = _USERS_API._get_user_dni(23106377, token=token)

print(usuarioBase)



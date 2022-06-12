import os
import logging
import requests

import oidc
from oidc.oidc import ClientCredentialsGrant

class API:

    def __init__(self, 
                 url=os.environ['OIDC_URL'], 
                 client_id=os.environ['OIDC_CLIENT_ID'], 
                 client_secret=os.environ['OIDC_CLIENT_SECRET'],
                 verify_ssl=bool(int(os.environ.get('VERIFY_SSL',0)))):
        self.oidc_url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.verify_ssl = verify_ssl

    def _get_token(self):
        ''' obtengo un token mediante el flujo client_credentials para poder llamar a la api de usuarios '''
        grant = ClientCredentialsGrant(self.oidc_url, self.client_id, self.client_secret, verify=self.verify_ssl)
        token = grant.get_token(grant.access_token())
        if not token:
            raise Exception()
        return token

    def get(self, api, params=None, token=None):
        if not token:
            token = self._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        logging.debug(params)
        if params:
            r = requests.get(api, verify=self.verify_ssl, headers=headers, params=params)
        else:
            r = requests.get(api, verify=self.verify_ssl, headers=headers, allow_redirects=False)
        logging.debug(r)
        return r

    def post(self, api, data=None, token=None):
        if not token:
            token = self._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        logging.debug(data)
        r = requests.post(api, verify=self.verify_ssl, headers=headers, json=data)
        logging.debug(r)
        return r

    def put(self, api, data=None, token=None):
        if not token:
            token = self._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        logging.debug(data)
        r = requests.put(api, verify=self.verify, headers=headers, json=data)
        logging.debug(r)
        return r

    def delete(self, api, token=None):
        if not token:
            token = self._get_token()

        ''' se deben cheqeuar intentos de login, y disparar : SeguridadError en el caso de que se haya alcanzado el máximo de intentos '''
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        logging.debug(api)
        r = requests.delete(api, verify=self.verify, headers=headers)
        logging.debug(r)
        return r
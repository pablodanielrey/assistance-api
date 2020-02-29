
class UsersAPI:

    def __init__(self, api_url, api):
        self.url = api_url
        self.api = api

    def _get_all_uids(self, token=None):
        query = '{}/usuarios/uids'.format(self.url)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        usr = r.json()
        return usr

    def _get_user_uuid(self, uuid, token=None):
        query = '{}/usuarios/{}'.format(self.url, uuid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        data = r.json()
        if type(data) == list:
            if len(data) > 0:
                return data[0]
            return None
        return data

    def _get_users_uuid(self, uuids=[], token=None):
        uids = '+'.join(uuids)
        query = '{}/usuarios/{}'.format(self.url, uids)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        data = r.json()
        if type(data) == list:
            return data
        return [data]

    def _get_user_dni(self, dni, token=None):
        query = '{}/usuario_por_dni/{}'.format(self.url, dni)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        data = r.json()
        if type(data) == list:
            if len(data) <= 0:
                return None
            return data[0]
        return data

    def _search_user(self, search, token=None):
        params = {
            'q':search
        }
        query = '{}/usuario'.format(self.url)
        r = self.api.get(query, params=params, token=token)
        if not r.ok:
            return None
        data = r.json()
        if type(data) == list:
            if len(data) > 0:
                return data[0]
            return None
        return data

    def _search_users(self, search, token=None):
        params = {
            'q':search
        }
        query = '{}/usuarios'.format(self.url)
        r = self.api.get(query, params=params, token=token)
        if not r.ok:
            return []
        users = r.json()
        if type(users) == list:
            return users
        return [users]
import redis

class LugaresAPI:

    def __init__(self, api_url, api):
        self.url = api_url
        self.api = api

    def _get_lugar_lid(self, lid, token=None):
        query = '{}/lugares/{}'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lid = r.json()
        if lid:
            return lid
        return None

    def _get_sublugares_lid(self, lid, token=None):
        query = '{}/lugares/{}/sublugares'.format(self.url, lid)
        r = self.api.get(query, token=token)
        if not r.ok:
            return None
        lids = r.json()
        if lids and len(lids) > 0:
            return lids
        return None


class LugaresGetters:
    def __init__(self, lugares_api):
        self.api = lugares_api

    def obtener_lugar_por_id(self, lid, token=None):
        return self.api._get_lugar_lid(lid, token)

    def obtener_sublugares_por_lugar(self, lid, token=None):
        return self.api._get_sublugares_lid(lid, token)


class LugaresCache:

    def __init__(self, host, port, getters, prefijo='_lugares_', timeout=60 * 60 * 24 * 7):
        self.redis_ = redis.StrictRedis(host=host, port=port, decode_responses=True)
        self.prefijo = prefijo
        self.timeout = timeout
        self.getters = getters

    def setear_lugar(self, lugar):
        uk = '{}{}{}'.format(self.prefijo, 'datos', lugar['id'])
        self.redis_.hmset(uk, lugar)
        self.redis_.expire(uk, self.timeout)

    def obtener_lugar_por_id(self, lid, token=None):
        uk = '{}{}{}'.format(self.prefijo, 'datos', lid)
        l = self.redis_.hgetall(uk)
        if len(l.keys()) > 0:
            return l
        l = self.getters.obtener_lugar_por_id(lid, token)
        if not l:
            return None
        self.setear_lugar(l)
        return l

    def setear_sublugares_por_lugar_id(self, lid, lids=[]):
        uk = '{}{}{}'.format(self.prefijo, 'sublugares', lid)
        for l in lids:
            self.redis_.lpush(uk, l)
        self.redis_.expire(uk, self.timeout)

    def obtener_sublugares_por_lugar_id(self, lid):
        uk = '{}{}{}'.format(self.prefijo, 'sublugares', lid)
        if self.redis_.exists(uk):
            return self.redis_.lrange(uk, 0, -1)
        lids = self.getters.obtener_sublugares_por_lugar(lid)
        self.setear_sublugares_por_lugar_id(lid, lids)
        return lids    


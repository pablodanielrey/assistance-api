import redis

class AssistanceCache:

    def __init__(self, host, port, prefijo='_assistance_', timeout=60 * 60 * 24 * 7):
        self.redis_ = redis.StrictRedis(host=host, port=port, decode_responses=True)
        self.prefijo = prefijo
        self.timeout = timeout
 
    @classmethod
    def _codificar_para_redis(cls, d):
        d2 = {}
        for k in d.keys():
            if d[k] is None:
                d2[k] = 'none_existentvalue'
            elif d[k] == False:
                d2[k] = 'false_existentvalue'
            elif d[k] == True:
                d2[k] = 'true_existentvalue'
            else:
                d2[k] = d[k]
        return d2

    @classmethod
    def _decodificar_desde_redis(cls, d):
        d2 = {}
        for k in d.keys():
            if d[k] == 'none_existentvalue':
                d2[k] = None
            elif d[k] == 'false_existentvalue':
                d2[k] = False
            elif d[k] == 'true_existentvalue':
                d2[k] = True
            else:
                d2[k] = d[k]
        return d2
    
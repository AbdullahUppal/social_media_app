import redis


class Cache:

    @staticmethod
    def __init__():
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    @staticmethod
    def close_cache(self):
        self.r

    def get_response(self, key:str): 
        res = self.r.get(key)
        return res 

    def set_response(self, key:str, response:dict):
        self.r.hset(key, mapping=response, ex=600)


    
    
    

    
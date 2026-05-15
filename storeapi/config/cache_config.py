from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import redis


r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def close_cache():
    r.close()

def get_response( key:str): 
    res = r.get(key)
    return res 

def set_response(key:str, response:dict):
    r.hset(key, mapping=response, ex=60)

class cache_middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        response = get_response(request.body)

    
    
    

    
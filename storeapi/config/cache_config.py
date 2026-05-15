import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def close_cache():
    r.close()


def get_response(key: str):
    res = r.get(key)
    return res


def set_response(key: str, response: dict):
    r.hset(key, mapping=response, ex=60)


class cache_middleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        client_ip = f"{request.client.host}_" if request.client.host else None
        method = f"{request.method}_" if request.method == "GET" else None
        path = f"{request.url.path}_" if request.url.path else None
        path_params = f"{request.path_params}_" if request.path_params else None
        query_params = f"{request.query_params}" if request.query_params else None
        try:
            body_params = await request.json()
        except Exception:
            body_params = None
        key = client_ip + method + path + path_params + query_params + body_params
        cache_response = get_response(key=key)

        if cache_response:
            return cache_response

        response = await call_next(request)
        set_response(key=key, response=response)
        return response

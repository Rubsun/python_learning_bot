from src.metrics_init import REQUESTS_TOTAL
from fastapi import Request

class RequestCountMiddleware:
    async def __call__(self, request: Request, call_next):
        REQUESTS_TOTAL.labels(method=request.method, path=request.url.path).inc()
        response = await call_next(request)
        return response

from prometheus_client import Counter, Histogram
import time
from functools import wraps

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

def track_request(endpoint):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = getattr(response, 'status_code', 200)
                return response
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(method='POST', endpoint=endpoint, status=str(status)).inc()
                REQUEST_LATENCY.labels(method='POST', endpoint=endpoint).observe(duration)
        return wrapper
    return decorator
import time
from prometheus_client import Counter, Histogram
from functools import wraps


REQUESTS = Counter('requests_total', 'Total number of requests')
DB_FETCH_REQUESTS = Counter('db_fetch_requests_total', 'Total number of requests at db')
DB_FETCH_PROCESSING_TIME = Histogram('db_fetch_processing_time', 'Request processing time (s)')
INTEGRATION_METHOD_DURATION = Histogram('integration_method_duration_seconds', 'Time spent in integration methods')


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        duration = time.monotonic() - start_time
        INTEGRATION_METHOD_DURATION.observe(duration)
        return result

    return wrapper

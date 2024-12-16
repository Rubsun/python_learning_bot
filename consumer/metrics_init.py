import time
from functools import wraps

from prometheus_client import CollectorRegistry, Counter, Histogram

registry = CollectorRegistry()

INTEGRATION_METHOD_DURATION = Histogram(
    'integration_method_duration_seconds', 'Time spent in integration methods', registry=registry
)
REQUESTS = Counter('requests_total', 'Total number of requests', registry=registry)

DB_FETCH_REQUESTS = Counter('db_fetch_requests_total', 'Total number of requests at db', registry=registry)
DB_FETCH_PROCESSING_TIME = Histogram('db_fetch_processing_time', 'Request processing time (s)', registry=registry)


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        duration = time.monotonic() - start_time
        INTEGRATION_METHOD_DURATION.observe(duration)
        return result

    return wrapper

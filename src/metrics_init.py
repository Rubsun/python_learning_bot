from prometheus_client import Counter, Histogram
import time
from functools import wraps

REQUESTS_TOTAL = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'path'])
INTEGRATION_METHOD_DURATION = Histogram('integration_method_duration_seconds', 'Time spent in integration methods')
RABBITMQ_MESSAGES_PRODUCED = Counter('rabbitmq_messages_produced_total', 'Total messages produced to RabbitMQ')
RABBITMQ_MESSAGES_CONSUMED = Counter('rabbitmq_messages_consumed_total', 'Total messages consumed from RabbitMQ')


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        duration = time.monotonic() - start_time
        INTEGRATION_METHOD_DURATION.observe(duration)
        return result

    return wrapper

import logging.config
import os
from contextlib import suppress

import yaml
from starlette_context import context
from starlette_context.errors import ContextDoesNotExistError
from starlette_context.header_keys import HeaderKeys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
with open(f'{BASE_DIR}/config/logging.conf.yml', 'r') as f:
    LOGGING_CONFIG = yaml.full_load(f)


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        with suppress(ContextDoesNotExistError):
            if corr_id := context.get(HeaderKeys.correlation_id, None):
                return '[%s] %s' % (corr_id, super().format(record))

        return super().format(record)


logger = logging.getLogger('backend_logger')
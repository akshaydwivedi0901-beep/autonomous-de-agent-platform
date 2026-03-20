import time
import logging

logger = logging.getLogger("ai-platform")


def track_request(func):

    def wrapper(*args, **kwargs):

        start = time.time()

        result = func(*args, **kwargs)

        latency = time.time() - start

        logger.info(f"Request latency: {latency}")

        return result

    return wrapper
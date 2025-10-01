# test_config.py
import os

# Test configuration
class TestConfig:
    TESTING = True
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_ALWAYS_EAGER = True  # Execute tasks synchronously in tests
    CELERY_TASK_ALWAYS_EAGER = True  # Alternative setting name
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Propagate exceptions in eager mode
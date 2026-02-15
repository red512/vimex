import requests
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from celery import Celery


# Initialize Flask
app = Flask(__name__)
CORS(app)


# Configure Celery
app.config['broker_url'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['result_backend'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')


def make_celery():
    """Create Celery instance with lazy configuration"""
    celery = Celery(
        app.name,
        broker=app.config['broker_url'],
        backend=app.config['result_backend']
    )

    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        
        # CRITICAL FIX: Disable ACK emulation in Redis transport
        broker_transport_options={
            'ack_emulation': False,
            'visibility_timeout': 3600,
        },
        
        result_backend_transport_options={
            'retry_policy': {
                'timeout': 5.0
            }
        },
        
        # Disable acknowledgments to prevent QoS tracking
        task_acks_late=False,
        worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=False,
        
        # Optional: Set to True if you don't need task results
        task_ignore_result=False,
    )
    celery.conf.update(app.config)

    return celery


# Initialize Celery
celery = make_celery()


# OpenWeatherMap API key
API_KEY = os.environ.get("API_KEY")


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def fetch_weather_data(self, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)  # Add timeout
        data = response.json()
        
        if response.status_code == 200:
            weather_data = {
                "city": city,
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"]
            }
            logger.info(f"Successfully retrieved weather data for {city}")
            return {"status": "success", "weather": weather_data}
        else:
            logger.error(f"Error retrieving weather data for {city}: {data.get('message', 'Unknown error')}")
            return {"status": "error", "error": data.get("message", "Unknown error")}
            
    except requests.Timeout:
        logger.error(f"Timeout while fetching weather for {city}")
        raise self.retry(countdown=60)  # Retry after 60 seconds
        
    except Exception as e:
        logger.exception(f"Exception while processing request: {str(e)}")
        # Retry up to 3 times with exponential backoff
        raise self.retry(countdown=60 * (self.request.retries + 1))


def check_redis_connection():
    """Check if Redis is available"""
    try:
        # Try to ping Redis with a short timeout
        import redis
        r = redis.Redis.from_url(app.config['broker_url'], socket_timeout=2, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception:
        return False


@app.route('/health')
def health_check():
    redis_status = check_redis_connection()

    response = {
        "status": "healthy",
        "redis": "connected" if redis_status else "disconnected"
    }

    # Return 200 even if Redis is down - the app itself is healthy
    return jsonify(response), 200


@app.route('/')
def get_weather():
    city = request.args.get('city', 'New York')

    try:
        # Submit task to queue
        task = fetch_weather_data.delay(city)

        return jsonify({
            "message": "Request accepted",
            "task_id": task.id,
            "status_url": f"/status/{task.id}"
        }), 202
    except Exception as e:
        logger.error(f"Failed to submit task: {str(e)}")
        return jsonify({
            "error": "Service temporarily unavailable",
            "message": "Queue service is not available"
        }), 503


@app.route('/status/<task_id>')
def get_status(task_id):
    task = fetch_weather_data.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return jsonify({"status": "pending", "message": "Task is waiting in queue"}), 202
    
    elif task.state == 'RETRY':
        return jsonify({"status": "retrying", "message": "Task is being retried"}), 202
    
    elif task.state == 'FAILURE':
        return jsonify({"status": "failed", "error": str(task.info)}), 500
    
    elif task.ready():
        result = task.get()
        if result["status"] == "success":
            return jsonify({"status": "completed", "result": result["weather"]}), 200
        return jsonify({"status": "failed", "error": result["error"]}), 400
    
    return jsonify({"status": "processing"}), 202


if __name__ == '__main__':
    app.run()





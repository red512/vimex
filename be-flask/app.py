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
    """Create Celery instance with redis-py compatible configuration"""
    celery = Celery(
        'weather_app',
        broker=app.config['broker_url'],
        backend=app.config['result_backend']
    )

    # Configuration that works with redis-py 5.x and avoids QoS issues
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_ignore_result=True,
        worker_hijack_root_logger=False,
        worker_log_color=False,
        # Properly disable QoS to avoid hset issues
        worker_prefetch_multiplier=1,  # Use 1 instead of 0 for better compatibility
        task_acks_late=False,           # Don't use late acks
        worker_disable_rate_limits=True,
        # Additional settings for stability
        broker_transport_options={
            'priority_steps': list(range(10)),
            'sep': ':',
            'queue_order_strategy': 'priority',
        }
    )

    return celery

# Initialize Celery
celery = make_celery()

# OpenWeatherMap API key
API_KEY = os.environ.get("API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, acks_late=False, ignore_result=True)
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

@app.route('/queue/add', methods=['POST'])
def add_tasks_to_queue():
    """Add multiple tasks to queue for KEDA testing"""
    try:
        data = request.get_json() or {}
        num_tasks = data.get('num_tasks', 1)
        city_prefix = data.get('city_prefix', 'TestCity')
        
        task_ids = []
        for i in range(num_tasks):
            city = f"{city_prefix}_{i+1}"
            task = fetch_weather_data.delay(city)
            task_ids.append(task.id)
            logger.info(f"✅ Queued task {task.id} for city: {city}")
        
        return jsonify({
            "message": f"Successfully queued {num_tasks} tasks",
            "task_ids": task_ids
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Failed to queue tasks: {str(e)}")
        return jsonify({"error": "Failed to queue tasks", "details": str(e)}), 500

@app.route('/queue/status')
def get_queue_status():
    """Get current queue status for monitoring"""
    try:
        import redis
        r = redis.Redis.from_url(app.config['broker_url'])
        
        queue_length = r.llen('celery')
        
        return jsonify({
            "queue_length": queue_length,
            "queue_name": "celery",
            "redis_connected": True
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        return jsonify({
            "queue_length": 0,
            "queue_name": "celery", 
            "redis_connected": False,
            "error": str(e)
        }), 500

@celery.task(bind=True)
def task_failure_handler(self, exc, task_id, args, kwargs, einfo):
    """Handle task failures by logging the error and skipping the task."""
    logger.error(f"Task {task_id} failed with error: {exc}")
    logger.error(f"Arguments: {args}, Keyword Arguments: {kwargs}")
    logger.error(f"Traceback: {einfo}")

# Attach the failure handler to the Celery worker
celery.conf.task_failure_handler = task_failure_handler

if __name__ == '__main__':
    app.run()


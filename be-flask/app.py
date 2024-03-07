import requests
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for your app

# OpenWeatherMap API key
API_KEY = os.environ.get("API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/')
def get_weather():
    city = request.args.get('city', 'New York')  # Default to New York if city parameter is not provided
    
    # OpenWeatherMap API endpoint
    # Request temperature in Celsius
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        # Make API request
        response = requests.get(url)
        data = response.json()

        # Extract relevant weather information
        if response.status_code == 200:
            weather_data = {
                "city": city,
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"]
            }

            # Log success
            logger.info(f"Successfully retrieved weather data for {city}")

            return jsonify({"message": "Success", "weather": weather_data}), 200
        else:
            # Log error
            logger.error(f"Error retrieving weather data for {city}: {data.get('message', 'Unknown error')}")

            return jsonify({"message": "Error", "error": data.get("message", "Unknown error")}), response.status_code
    except Exception as e:
        # Log exception
        logger.exception(f"Exception while processing request: {str(e)}")

        return jsonify({"message": "Error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run()

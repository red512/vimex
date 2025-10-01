# tests/test_unit.py
import unittest
from unittest.mock import patch, MagicMock
import os
import json

# Set test environment variables before importing app
os.environ['task_always_eager'] = 'True'
os.environ['task_eager_propagates'] = 'True'

from app import app, celery


class TestApp(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['task_always_eager'] = True
        app.config['task_eager_propagates'] = True
        celery.conf.update(app.config)
        self.app = app.test_client()

    @patch('app.fetch_weather_data.delay')
    def test_home_route(self, mock_delay):
        # Mock the Celery task to avoid Redis dependency
        mock_task = MagicMock()
        mock_task.id = 'test-task-id-123'
        mock_delay.return_value = mock_task

        response = self.app.get('/')
        self.assertEqual(response.status_code, 202)

        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('task_id', data)
        self.assertIn('status_url', data)
        self.assertEqual(data['message'], 'Request accepted')
        self.assertEqual(data['task_id'], 'test-task-id-123')

        # Verify the task was called with default city
        mock_delay.assert_called_once_with('New York')

    @patch('app.fetch_weather_data.delay')
    def test_home_route_with_custom_city(self, mock_delay):
        # Mock the Celery task
        mock_task = MagicMock()
        mock_task.id = 'test-task-id-456'
        mock_delay.return_value = mock_task

        response = self.app.get('/?city=London')
        self.assertEqual(response.status_code, 202)

        data = json.loads(response.data)
        self.assertEqual(data['task_id'], 'test-task-id-456')

        # Verify the task was called with specified city
        mock_delay.assert_called_once_with('London')

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    @patch('app.fetch_weather_data.AsyncResult')
    def test_status_pending(self, mock_async_result):
        # Mock pending task
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task

        response = self.app.get('/status/test-task-id')
        self.assertEqual(response.status_code, 202)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'pending')

    @patch('app.fetch_weather_data.AsyncResult')
    def test_status_completed(self, mock_async_result):
        # Mock completed task
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.ready.return_value = True
        mock_task.get.return_value = {
            "status": "success",
            "weather": {
                "city": "New York",
                "temperature": 25,
                "humidity": 60,
                "description": "clear sky"
            }
        }
        mock_async_result.return_value = mock_task

        response = self.app.get('/status/test-task-id')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'completed')
        self.assertIn('result', data)
        self.assertEqual(data['result']['city'], 'New York')


if __name__ == '__main__':
    unittest.main()





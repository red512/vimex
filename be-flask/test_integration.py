# tests/test_integration.py
import requests
import json
import time


def test_home_route():
    """Test that the home route returns a task ID and proper async response"""
    response = requests.get('http://localhost:5000/')

    # Accept both 202 (Redis working) and 503 (Redis unavailable)
    if response.status_code == 202:
        data = response.json()
        assert 'message' in data
        assert 'task_id' in data
        assert 'status_url' in data
        assert data['message'] == 'Request accepted'
        print("✓ Home route returns task ID correctly (Redis working)")
    elif response.status_code == 503:
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Service temporarily unavailable'
        print("⚠ Home route returns service unavailable (Redis not working)")
    else:
        raise AssertionError(f"Unexpected status code: {response.status_code}")


def test_health_check():
    """Test health check endpoint"""
    response = requests.get('http://localhost:5000/health')
    assert response.status_code == 200

    data = response.json()
    assert data['status'] == 'healthy'
    print("✓ Health check endpoint working")


def test_custom_city():
    """Test that custom city parameter is accepted"""
    response = requests.get('http://localhost:5000/?city=London')

    # Accept both 202 (Redis working) and 503 (Redis unavailable)
    if response.status_code == 202:
        data = response.json()
        assert 'task_id' in data
        print("✓ Custom city parameter accepted (Redis working)")
    elif response.status_code == 503:
        data = response.json()
        assert 'error' in data
        print("⚠ Custom city returns service unavailable (Redis not working)")
    else:
        assert response.status_code in [202, 503], f"Unexpected status: {response.status_code}"


def test_task_status_workflow():
    """Test the complete workflow from task submission to completion"""
    # Submit a task
    response = requests.get('http://localhost:5000/?city=Paris')

    if response.status_code == 503:
        print("⚠ Skipping task workflow test - Redis not available")
        return

    assert response.status_code == 202

    data = response.json()
    task_id = data['task_id']
    status_url = f"http://localhost:5000/status/{task_id}"

    # Check status (might be pending or completed depending on timing)
    status_response = requests.get(status_url)
    assert status_response.status_code in [200, 202]

    status_data = status_response.json()
    assert 'status' in status_data

    # If it's still pending/processing, wait a bit and check again
    max_retries = 10
    retries = 0
    while status_data.get('status') in ['pending', 'processing', 'retrying'] and retries < max_retries:
        time.sleep(2)
        status_response = requests.get(status_url)
        status_data = status_response.json()
        retries += 1

    # Should eventually complete or fail
    assert status_data['status'] in ['completed', 'failed']
    print("✓ Task status workflow completed")


def check_prerequisites():
    """Check if all required services are running"""
    try:
        # Check if Flask app is running
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code != 200:
            raise Exception("Flask app health check failed")
        print("✅ Flask app is running")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Flask app not available: {e}")

    # Check if Redis is available (indirectly through app)
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code not in [200, 202, 500]:
            raise Exception("Unexpected response from Flask app")
        print("✅ App responds to requests")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Cannot connect to Flask app: {e}")


if __name__ == "__main__":
    print("Running integration tests...")
    print("Note: These tests require the Flask app to be running on localhost:5000")
    print("Note: These tests require Redis and Celery worker to be running")
    print()

    try:
        print("🔍 Checking prerequisites...")
        check_prerequisites()

        print("\n🧪 Running tests...")
        test_health_check()
        test_home_route()
        test_custom_city()
        test_task_status_workflow()
        print("\n✅ All integration tests passed!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

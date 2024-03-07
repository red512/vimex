# tests/test_integration.py
import requests


def test_home_route():
    response = requests.get('http://localhost:5000/')
    assert response.status_code == 200
    assert b'"message":"Success"' in response.content
    assert b'"city":"New York"' in response.content
    print("integration tests passed")

test_home_route()

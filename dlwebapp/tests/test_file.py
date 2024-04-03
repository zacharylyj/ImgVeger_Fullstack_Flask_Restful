import pytest
from application import app, db
from io import BytesIO
import json

def test_endpoint(test_client):
    response = test_client.get('/api/test')
    assert response.status_code == 200
    assert b'Hello from the API!' in response.data

def test_signup_new(test_client):
    response = test_client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'test'
    })
    assert response.status_code == 201
    assert 'Account created successfully!' in response.get_json()['message']

def test_repeat_signup_existing(test_client):
    response = test_client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'test'
    })
    assert response.status_code == 400
    assert 'Email already in use. Please use another email.' in response.get_json()['message']

def test_signin_valid(test_client):
    response = test_client.post('/api/signin', json={
        'email': 'test@example.com',
        'password': 'test'
    })
    assert response.status_code == 200
    assert 'Login successful' in response.get_json()['message']

def test_signin_invalid_password(test_client):
    response = test_client.post('/api/signin', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'Invalid email or password' in response.get_json()['message']

def test_signin_non_exisiting(test_client):
    response = test_client.post(
        "/api/signin", json={"email": "nottest@gmail.com", "password": "password"}
    )

    assert response.status_code == 401
    assert response.json["message"] == "Invalid email or password"

def test_index_unauthorized(test_client):
    login_response = test_client.post('/api/signin', json={
        'email': 'test@example.com',
        'password': 'wrong'
    })
    assert login_response.status_code == 401
    assert 'Invalid email or password' in login_response.get_json()['message']

    response = test_client.post('/api/home', content_type='multipart/form-data', data={
    })
    if response.is_json:
        assert response.status_code == 401
        assert 'Unauthorized' in response.get_json().get('message', '')

def test_index_authorized_no_inputs(test_client):
    login_response = test_client.post('/api/signin', json={
        'email': 'test@example.com',
        'password': 'test'
    })
    assert login_response.status_code == 200
    assert 'Login successful' in login_response.get_json()['message']

    response = test_client.post('/api/home', json={})

    assert response.status_code == 422
    assert "Request must be JSON with 'model_choice'." in response.get_json()['error']

def test_index_authorized_no_img(test_client):
    login_response = test_client.post('/api/signin', json={
        'email': 'test@example.com',
        'password': 'test'
    })
    assert login_response.status_code == 200
    assert 'Login successful' in login_response.get_json()['message']

    response = test_client.post('/api/home', json={'model_choice': '31x31'})

    assert response.status_code == 422
    assert "No selected file" in response.get_json()['error']

def test_add_history_entry(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'test@example.com',
        'predictions': 1,
        'model_choice': '31x31',
    })
    assert response.status_code == 201
    assert response.json["message"] == "Added History Entry!"

def test_add_history_entry2(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'test@example.com',
        'predictions': 13,
        'model_choice': '128x128',
    })
    assert response.status_code == 201
    assert response.json["message"] == "Added History Entry!"

def test_add_history_entry3(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'test@example.com',
        'predictions': 3,
        'model_choice': '31x31',
    })
    assert response.status_code == 201
    assert response.json["message"] == "Added History Entry!"

def test_add_history_entry_invalid(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'test@example.com',
        'predictions': 16,
        'model_choice': '80x80',
    })
    assert response.status_code == 403
    assert response.json["error"] == "Data Selected Not Supported"

def test_add_history_entry_invalid2(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'jace@example.com',
        'predictions': -2,
        'model_choice': '128x128',
    })
    assert response.status_code == 403
    assert response.json["error"] == "Data Selected Not Supported"

def test_add_history_entry_invalid3(test_client):
    response = test_client.post("/api/addtestdata", json={
        'user_id': 'jace@example.com',
        'predictions': -2,
        'model_choice': '128x128',
    })
    assert response.status_code == 403
    assert response.json["error"] == "Data Selected Not Supported"

def test_remove_existing_entry(test_client):
    id = test_client.post("/api/get_largest_id").json["id"]
    response = test_client.post(f"/api/remove/{id}")

    assert response.status_code == 200
    assert response.json["status"] == "success"

@pytest.mark.xfail(reason="Account does not exist/ User will never be able to do this")
def test_account_delete_invalid(test_client):
    response = test_client.post("/api/delete_account", json={"email": "notuat@gmail.com"})

    assert response.status_code == 200
    assert response.json["status"] == "success"

def test_account_delete_valid(test_client):
    response = test_client.post("/api/delete_account", json={"email": "test@example.com"})

    assert response.status_code == 200
    assert response.json["status"] == "success"

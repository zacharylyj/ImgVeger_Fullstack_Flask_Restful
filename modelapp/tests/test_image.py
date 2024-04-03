import pytest
import json
import requests
import numpy as np


def test_tf_serving31():
    response = requests.get("https://cnn-model-app-testsite.onrender.com/v1/models/CNN31x31")
    status = response.json()

    assert response.status_code == 200
    assert status == {
        "model_version_status": [
            {
                "version": "1",
                "state": "AVAILABLE",
                "status": {
                    "error_code": "OK",
                    "error_message": ""
                }
            }
        ]
    }

def test_tf_serving128():
    response = requests.get("https://cnn-model-app-testsite.onrender.com/v1/models/CNN128x128")
    status = response.json()

    assert response.status_code == 200
    assert status == {
        "model_version_status": [
            {
                "version": "1",
                "state": "AVAILABLE",
                "status": {
                    "error_code": "OK",
                    "error_message": ""
                }
            }
        ]
    }

def create_blank(target_size):
    image_array = np.zeros((target_size[0], target_size[1], 1), dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)
    return image_array


def test_cnn_model_pred31():
    url = 'https://cnn-model-app.onrender.com/v1/models/CNN31x31:predict'
    target_size = (31, 31)
    image_data = create_blank(target_size)
    data = json.dumps({"signature_name": "serving_default", "instances": image_data.tolist()})
    response = requests.post(url, data=data)
    prediction = response.json()

    assert response.status_code == 200
    assert 'predictions' in prediction

def test_cnn_model_pred128():
    url = 'https://cnn-model-app.onrender.com/v1/models/CNN128x128:predict'
    target_size = (128, 128)
    image_data = create_blank(target_size)
    data = json.dumps({"signature_name": "serving_default", "instances": image_data.tolist()})
    response = requests.post(url, data=data)
    prediction = response.json()

    assert response.status_code == 200
    assert 'predictions' in prediction

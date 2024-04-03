from flask import Blueprint, jsonify
from application import app
from application import db
from application import login_manager
from application import bcrypt
from application.models import User
from application.models import History
from application.forms import SignUpForm, SignInForm, PredictionForm, ChangePasswordForm, BulkPredictionForm
from datetime import datetime
from flask_login import UserMixin, login_user, login_required, current_user, logout_user
from flask import render_template, request, flash, url_for, redirect, jsonify, current_app, send_file
from sqlalchemy import desc, or_
from wtforms.validators import (
    Length,
    InputRequired,
    ValidationError,
    NumberRange,
    DataRequired,
    EqualTo,
    Email,
    Length,
    Optional,
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import shutil
import base64
import requests
import tempfile
import numpy as np
import pandas as pd
import zipfile
import json
import os
import io
import csv

class_labels = {
        0: 'Bean',
        1: 'Bitter_Gourd',
        2: 'Bottle_Gourd',
        3: 'Brinjal',
        4: 'Broccoli',
        5: 'Cabbage',
        6: 'Capsicum',
        7: 'Carrot',
        8: 'Cauliflower',
        9: 'Cucumber',
        10: 'Papaya',
        11: 'Potato',
        12: 'Pumpkin',
        13: 'Radish',
        14: 'Tomato'
    }

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Define the Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_highest_index(arr):
    max_val = float('-inf')
    max_index = -1
    for i, val in enumerate(arr):
        if val > max_val:
            max_val = val
            max_index = i
    return max_index, class_labels[max_index]

def prepare_image(image_path, size=(31, 31)):
    img = Image.open(image_path).convert('L')
    img = img.resize(size, Image.Resampling.LANCZOS)
    img_array = np.array(img) / 255.0
    img_array = img_array.reshape((1, size[0], size[1], 1))
    return img_array.tolist()

def make_prediction(prepared_image, model_url):
    data = json.dumps({"signature_name": "serving_default", "instances": prepared_image})
    headers = {"content-type": "application/json"}
    response = requests.post(model_url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json()['predictions'][0]
    else:
        app.logger.error(f"Failed to make prediction, status code: {response.status_code}, response: {response.text}")
        return None
    
def get_label(form, field):
    field_data = getattr(form, field).data
    return next(
        (label for value, label in getattr(form, field).choices if value == field_data),
        None,
    )

def add_entry(new_entry):
    try:
        db.session.add(new_entry)
        db.session.commit()
        return new_entry.id
    except Exception as error:
        db.session.rollback()
        flash(error, "danger")

def get_entries(email, search_term):
    try:
        query = db.select(History).where(History.user_id == email)
        reverse_search_terms = [key for key, value in class_labels.items() if search_term.lower() in value.lower()]

        if search_term:
            search_filter = or_(
                History.model_used.contains(search_term),
                History.image_path.contains(search_term),
                History.creation_time.contains(search_term),
                History.prediction.in_(reverse_search_terms) if reverse_search_terms else False
            )
            query = query.where(search_filter)
        entries = (
            db.session.execute(
                query.order_by(desc(History.id))
            )
            .scalars()
            .all()
        )
        return entries
    except Exception as e:
        flash(f"An error occurred: {e}")
        return []

def remove_entry(id):
    try:
        entry = db.get_or_404(History, id)
        db.session.delete(entry)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash(error, "danger")
        return 0

def get_user(email):
    try:
        user = (
            db.session.execute(db.select(User).where(User.email == email))
            .scalars()
            .first()
        )
        return user
    except Exception as e:
        flash(f"An error occurred: {e}")
        return None
@api_bp.route('/test', methods=['GET'])
def example():
    return jsonify({'message': 'Hello from the API!'})

@api_bp.route("/remove/<int:id>", methods=["POST"])
def api_remove_entry(id):
    try:
        result = remove_entry(id)
        if result == 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Entry not found or failed to delete",
                    }
                ),
                404,
            )
        else:
            return (
                jsonify({"status": "success", "message": "Entry deleted successfully"}),
                200,
            )
    except Exception:
        return jsonify({"status": "error", "message": "Server Error"}), 500


def remove_entry(id):
    try:
        entry = db.get_or_404(History, id)
        db.session.delete(entry)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash(error, "danger")
        return jsonify({'message': f'Error {error}', 'user_id': id}), 500

@api_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and bcrypt.check_password_hash(user.password, data.get('password')):
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
    

@api_bp.route('/signup', methods=['POST'])
def api_signup(data=None):
    if data is None:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        print(data)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"status": "error", "message": "Email already in use. Please use another email."}), 400

        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
            return (
                jsonify(
                    {"status": "success", "message": "Account created successfully!"}
                ),
                201,
            )
        except Exception:
            return jsonify({"status": "error", "message": "Server Error"}), 500
    return jsonify({"status": "error", "message": "Invalid data"}), 400


@api_bp.route("/home", methods=["POST"])
@login_required
def api_home():
    response = {}
    data = request.get_json() or {}
    email = current_user.email
    model_choice = data.get('model_choice')

    if not model_choice:
        return jsonify({"error": "Request must be JSON with 'model_choice'."}), 422

    file = data.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No selected file"}), 422
    
    if file and model_choice:
        return jsonify({"message": "Data Accepted"}), 200

    filename = secure_filename(file.filename)
    last_id = db.session.query(db.func.max(History.id)).scalar()
    new_id = 1 if last_id is None else last_id + 1
    filename = f"{new_id}_{filename}"

    file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
    if not os.path.exists(app.config['HISTORY_FOLDER']):
        os.makedirs(app.config['HISTORY_FOLDER'])
    file.save(file_path)

    try:
        if model_choice == '31x31':
            image_data = prepare_image(file_path, size=(31, 31))
            model_url = 'https://cnn-model-app.onrender.com/v1/models/CNN31x31:predict'
        else:
            image_data = prepare_image(file_path, size=(128, 128))
            model_url = 'https://cnn-model-app.onrender.com/v1/models/CNN128x128:predict'
    except Exception as e:
        return jsonify({"error": f"Error preparing image: {str(e)}"}), 500

    try:
        prediction, prediction_text = get_highest_index(make_prediction(image_data, model_url))
    except Exception as e:
        return jsonify({"error": f"Error making prediction: {str(e)}"}), 500


    new_entry = History(user_id=email, model_used=model_choice, prediction=prediction, image_path=filename)
    try:
        db.session.add(new_entry)
        db.session.commit()
        response['message'] = 'Prediction made successfully!'
        response['prediction_text'] = prediction_text
        response['model_used'] = model_choice
        response['image_path'] = f'history/{filename}'
    except Exception as e:
        db.session.rollback()
        response['error'] = f"An error occurred saving the prediction: {str(e)}"
        return jsonify(response), 500

    return jsonify(response), 200


@api_bp.route('/history', methods=['GET'])
@login_required
def history():
    user_id = current_user.id
    entries = History.query.filter_by(user_id=user_id).all()
    history_data = [{'id': entry.id, 'model_used': entry.model_used, 'prediction': entry.prediction, 'image_path': entry.image_path} for entry in entries]
    return jsonify({'history': history_data}), 200

@api_bp.route('/account/delete', methods=['POST'])
@login_required
def deleteuser():
    user = current_user
    remove_user(user)
    return jsonify({'message': 'Password changed successfully'}), 200

def remove_user(user):
    try:
        entry = db.get_or_404(User, user)
        db.session.delete(entry)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash(error, "danger")
        return jsonify({'message': f'Error {error}', 'user_id': id}), 500

@api_bp.route('/account/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    user = current_user
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not bcrypt.check_password_hash(user.password, current_password):
        return jsonify({'message': 'Current password is incorrect'}), 401
    
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200

@api_bp.route('/get_largest_id', methods=["GET", "POST"])
def get_largest_id():
    result = db.session.query(db.func.max(History.id)).scalar()
    return jsonify({"id": result}), 200

@api_bp.route('/addtestdata', methods=["GET", "POST"])
def add_data():
    data = request.get_json()
    email = data.get('user_id')
    model_choice = data.get('model_choice')
    prediction = data.get('predictions')
    if model_choice != "31x31" and model_choice != "128x128":
        return jsonify({'error': 'Data Selected Not Supported'}), 403
    if prediction<0 or prediction>15:
        return jsonify({'error': 'Data Selected Not Supported'}), 403
    new_entry = History(user_id=email, model_used=model_choice, prediction=prediction, image_path='test.jpg')
    db.session.add(new_entry)
    try:
        db.session.commit()
        return jsonify({'message': 'Added History Entry!'}), 201
    except Exception:
            return jsonify({"status": "error", "message": "Server Error"}), 500

@api_bp.route("/delete_account", methods=["POST"])
def api_delete_account(data=None):
    if data is None:
        data = request.get_json()
    user_email = data["email"]
    user = User.query.filter_by(email=user_email).first()

    if user:
        db.session.delete(user)
        db.session.commit()
        return (
            jsonify({"status": "success", "message": "Account deleted successfully"}),
            200,
        )
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404

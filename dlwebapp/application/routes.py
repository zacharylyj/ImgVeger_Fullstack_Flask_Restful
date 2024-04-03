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
from sqlalchemy import desc, or_, func
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

# Handles http://127.0.0.1:5000/test
@app.route("/test")
def test():
    return "<h1>server is up!</h1>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('signin'))

# Handles http://127.0.0.1:5000/signin
@app.route("/", methods=["GET", "POST"])
@app.route("/signin", methods=["GET", "POST"])
def signin():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect("/home")
            else:
                flash("Password is incorrect")
        else:
            flash("Email is not found")
    return render_template("signin.html", title="Sign In", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already in use.\nPlease sign in or use another email.")
            return render_template("signup.html", form=form)

        hashed_password = bcrypt.generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            flash(f"An error occurred: {e}")
            return render_template("signup.html", form=form)

        flash("Account created successfully!\nPlease sign in.")
        return redirect(url_for("signin"))

    return render_template("signup.html", form=form)


@app.route("/index", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@login_required
def index_page():
    filename = 'images/logo.png'
    try:
        email = current_user.email
    except Exception as e:
        print(e)
        data = request.get_json()
        email = data["email"]
    form = PredictionForm()
    if form.validate_on_submit():
        model_choice = form.model_choice.data
        file = form.image.data
        filename = secure_filename(file.filename)
        
        last_id = db.session.query(db.func.max(History.id)).scalar()
        new_id = 1 if last_id is None else last_id + 1
        
        filename = f"{new_id}_{filename}"
        
        file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
        if not os.path.exists(app.config['HISTORY_FOLDER']):
            os.makedirs(app.config['HISTORY_FOLDER'])
        file.save(file_path)
        if model_choice == '31x31':
            image_data = prepare_image(file_path, size=(31, 31))
            model_url = 'https://cnn-model-app.onrender.com/v1/models/CNN31x31:predict'
        else:  # For 128x128 model
            image_data = prepare_image(file_path, size=(128, 128))
            model_url = 'https://cnn-model-app.onrender.com/v1/models/CNN128x128:predict'
        image_data = prepare_image(file_path)  
        
        prediction, prediction_text = get_highest_index(make_prediction(image_data, model_url))
        
        new_entry = History(user_id=email, model_used=model_choice, prediction=prediction, image_path=filename)
        db.session.add(new_entry)
        try:
            db.session.commit()
            flash('Prediction made successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}")
        print(filename, prediction_text)
        return render_template("index.html", title="Home", form=form, user_email=email, image_path='history/'+filename, prediction_text=prediction_text, model_used=model_choice)
    return render_template("index.html", title="Home", form=form, user_email=email)

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


@app.route("/history")
@login_required
def history_page():
    search_term = request.args.get('search', '')
    model_filter = request.args.get('model_filter', '') 
    date_filter = request.args.get('date_filter', '')
    sort_direction = request.args.get('sort', 'desc') 

    try:
        email = current_user.email
    except Exception as e:
        print(e)
        data = request.get_json()
        email = data["email"]

    entries = get_entries(email, search_term, model_filter, date_filter, sort_direction)
    for entry in entries:
        entry.prediction_label = class_labels.get(entry.prediction, "Unknown")

    return render_template(
        "history.html",
        title="History",
        entries=entries,
        user_email=email,
        search_term=search_term,
        model_filter=model_filter,
        date_filter=date_filter,
        sort_direction=sort_direction,
        index=True,
    )

def get_entries(email, search_term, model_filter, date_filter, sort_direction):
    try:
        query = db.select(History).where(History.user_id == email)
        reverse_search_terms = [key for key, value in class_labels.items() if search_term.lower() in value.lower()]

        if search_term:
            search_filter = or_(
                History.model_used.contains(search_term),
                History.image_path.contains(search_term),
                History.prediction.in_(reverse_search_terms) if reverse_search_terms else False
            )
            query = query.where(search_filter)
            
        if model_filter in ["128x128", "31x31"]: 
            query = query.where(History.model_used.contains(model_filter))  

        if date_filter:
            date_object = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.where(func.date(History.creation_time) == date_object)

        if sort_direction == 'asc':
            query = query.order_by(History.id.asc())
        else:
            query = query.order_by(History.id.desc())

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


@app.route("/remove", methods=["POST"])
def remove():
    req = request.form
    id = req["id"]
    remove_entry(id)
    return redirect("/history")


def remove_entry(id):
    try:
        entry = db.get_or_404(History, id)
        db.session.delete(entry)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash(error, "danger")
        return 0


@app.route("/account", methods=["GET", "POST"])
def account_page():
    try:
        email = current_user.email
    except Exception as e:
        print(e)
        data = request.get_json()
        email = data["email"]
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = get_user(email)

        # Check for current password correctness
        if user and bcrypt.check_password_hash(
            user.password, form.current_password.data
        ):
            # Change password if 'Change Password' button is clicked
            if form.submit_change.data:
                user.password = bcrypt.generate_password_hash(form.new_password.data)
                db.session.commit()
                flash("Password changed successfully.")
            # Delete account if 'Delete Account' button is clicked
            elif form.submit_delete.data:
                db.session.delete(user)
                db.session.commit()
                flash("Account deleted.")
        else:
            flash("Incorrect current password.")
        return redirect("/signin")

    return render_template(
        "account.html",
        title="Account",
        user_email=email,
        form=form,
        index=True,
    )


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


@app.route("/bulk", methods=["GET", "POST"])
@login_required
def bulk_predict():
    try:
        email = current_user.email
    except Exception as e:
        print(e)
        data = request.get_json()
        email = data["email"]
    form = BulkPredictionForm()
    if form.validate_on_submit():
        model_choice = form.model_choice.data
        zip_file = form.upload.data
        zip_filename = secure_filename(zip_file.filename)
        
        temp_dir = os.path.join(app.config['TEMP_FOLDER'], "bulk")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        zip_path = os.path.join(temp_dir, zip_filename)
        zip_file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        predictions = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg')):
                    last_id = db.session.query(db.func.max(History.id)).scalar()
                    new_id = 1 if last_id is None else last_id + 1
                    filename = f"{new_id}_{file}"
                    db_file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
                    if not os.path.exists(app.config['HISTORY_FOLDER']):
                        os.makedirs(app.config['HISTORY_FOLDER'])
                    file_path = os.path.join(root, file)
                    image_data = prepare_image(file_path, size=(31, 31) if model_choice == '31x31' else (128, 128))
                    model_url = f'https://cnn-model-app.onrender.com/v1/models/CNN{model_choice}:predict'
                    prediction, prediction_text = get_highest_index(make_prediction(image_data, model_url))
                    predictions.append((file, prediction_text))
                    shutil.copy(file_path, db_file_path)
                    new_entry = History(user_id=email, model_used=model_choice, prediction=prediction, image_path=filename)
                    db.session.add(new_entry)
                    try:
                        db.session.commit()
                        flash('Prediction made successfully!')
                    except Exception as e:
                        db.session.rollback()
                        flash(f"An error occurred: {e}")
        shutil.rmtree(temp_dir)
        return render_template("bulk_results.html", title="Bulk Results",predictions=predictions, user_email=email)
    return render_template("bulk.html", title="Bulk", form=form, user_email=email)
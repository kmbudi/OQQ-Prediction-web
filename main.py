# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
import sys
import pickle
from datetime import datetime
import numpy as np
import pandas as pd
from sys import exit

from flask import Flask, request, jsonify, render_template
from flask_migrate import Migrate
from flask_minify import Minify

from apps.config import config_dict
from apps import create_app, db

# 1. Alias import Firebase db agar tidak bentrok dengan SQLAlchemy db
from firebase_admin import db as firebase_db, credentials, initialize_app

# 2. Inisialisasi Firebase Admin (Pastikan file serviceAccountKey.json dan URL-nya benar)
# cred = credentials.Certificate("serviceAccountKey.json")
# initialize_app(cred, {
#     'databaseURL': 'https://your-firebase-db.firebaseio.com/'
# })

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)
Migrate(app, db)

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.info('DEBUG             = ' + str(DEBUG))
    app.logger.info('Page Compression = ' + ('FALSE' if DEBUG else 'TRUE'))
    app.logger.info('DBMS              = ' + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info('ASSETS_ROOT       = ' + app_config.ASSETS_ROOT)

# 3. Path model yang aman
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'models', 'OQQ_model.sav')

with open(model_path, 'rb') as file:
    model = pickle.load(file)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.form
    # Gunakan firebase_db
    ref = firebase_db.reference('Dataprediksi')
    
    tanggal_str = data.get('tanggal')
    tanggal_prediksi = datetime.strptime(tanggal_str, "%m/%d/%Y").isoformat()
    
    air_flow_267 = float(data.get('air_flow_267'))
    float_level_47 = float(data.get('float_level_47'))
    iron_feed = float(data.get('iron_feed'))
    amina_flow = float(data.get('amina_flow'))
    ore_pulp_ph = float(data.get('ore_pulp_ph'))
    ore_pulp_density = float(data.get('ore_pulp_density'))

    input_data = np.array([[air_flow_267, float_level_47, iron_feed, amina_flow, ore_pulp_ph, ore_pulp_density]])

    prediction = model.predict(input_data)

    prediction_data = {
        'tanggal_prediksi': tanggal_prediksi,
        'air_flow_267': air_flow_267,
        'float_level_47': float_level_47,
        'iron_feed': iron_feed,
        'amina_flow': amina_flow,
        'ore_pulp_ph': ore_pulp_ph,
        'ore_pulp_density': ore_pulp_density,
        'hasil_predict': float(prediction[0])
    }
    
    new_prediction_ref = ref.push()
    new_prediction_ref.set(prediction_data)

    return render_template('prediksi.html', result=prediction[0])


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    ref = firebase_db.reference('feedback')
    message = request.form['message']

    feedback_data = {
        'message': message
    }

    new_feedback_ref = ref.push()
    new_feedback_ref.set(feedback_data)

    return render_template('prediksi.html', success=True)

if __name__ == "__main__":
    app.run()

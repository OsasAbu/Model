#!/usr/bin/env python
# coding: utf-8

# In[3]:


get_ipython().system('pip install pycaret')
from flask import Flask,request, url_for, redirect, render_template, jsonify
from pycaret.regression import *
import pandas as pd
import pickle
import numpy as np
# Initalise the Flask app
app = Flask(__name__)


# In[20]:


get_ipython().system('pip install keras')
get_ipython().system('pip install tensorflow')


# In[21]:


from keras.models import load_model


# In[30]:


# Load the pre-trained model
model = load_model('C:\\Users\\oabu\\Downloads\\model.h5')


# In[32]:


from datetime import datetime

@app.route('/predict', methods=['POST'])
def predict():
    int_features = [x for x in request.form.values()]
    date_string = request.form['date']

    try:
        # Attempt to parse the input as a date
        date = datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return render_template('home.html', pred='Invalid date format. Please use YYYY-MM-DD format.')

    # Add the date to the input features
    int_features.append(date)

    final = np.array(int_features)
    data_unseen = pd.DataFrame([final], columns=cols + ['date'])

    # Perform prediction using the model
    prediction = predict_model(model, data=data_unseen, round=0)
    prediction = int(prediction.Label[0])

    return render_template('home.html', pred='Expected Bill will be {}'.format(prediction))


# In[ ]:





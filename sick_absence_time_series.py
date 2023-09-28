# -*- coding: utf-8 -*-
"""Sick Absence  Time series.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1u9sa876kFZvTd-Pif4Ld-b2GU1MDOMPj
"""

!pip install prophet

import pandas
from matplotlib import pyplot
data = pandas.read_csv('Sick Data.csv')
data.shape

data.info()

#Data wrangling to count and group sick absence
training_data = data.groupby('operational_date')['EmployeeNumber'].count().reset_index()
training_data = training_data.rename(columns={
    'operational_date': 'Date',
    'EmployeeNumber': 'Sick_Absence_Count'
})
training_data.shape

training_data

#Data wrangling to filter by GarageName
training_data1 = data[data['GarageName'] == 'Holloway'].groupby('operational_date')['EmployeeNumber'].count().reset_index()
training_data1 = training_data1.rename(columns={
    'operational_date': 'Date',
    'EmployeeNumber': 'Sick_Absence_Count'
})
training_data1.shape

# Using plotly.express
import plotly.express as px
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Scatter(x=training_data['Date'], y=training_data['Sick_Absence_Count'], name='Sick_Absence_Count', line=dict(color='blue')))


fig.update_layout(title='Count of Sick Absence Over Time',
                  xaxis_title='Date',
                  yaxis_title='Count')

fig.show()

import prophet

from sklearn.metrics import mean_absolute_error

from sklearn.model_selection import train_test_split
import matplotlib.pyplot
training_data.rename(columns={'Date': 'ds', 'Sick_Absence_Count': 'y'}, inplace=True)
train_data = training_data.sample(frac=0.8, random_state=10)
validation_data = training_data.drop(train_data.index)

print(f'training data size : {train_data.shape}')
print(f'validation data size : {validation_data.shape}')

train_data = train_data.reset_index()
validation_data = validation_data.reset_index()

from prophet import Prophet
model = Prophet()
model.fit(train_data)

prediction = model.predict(pandas.DataFrame({'ds':validation_data['ds']}))
y_actual = validation_data['y']
y_predicted = prediction['yhat']
y_predicted = y_predicted.astype(int)
mean_absolute_error(y_actual, y_predicted)

from plotly.subplots import make_subplots
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=validation_data['ds'], y=y_actual, name="actual targets"),
    secondary_y=False,)
fig.add_trace(
    go.Scatter(x=validation_data['ds'], y=y_predicted, name="predicted targets"),
    secondary_y=True,)
fig.update_layout(
    title_text="Actual vs Predicted Targets")
fig.update_xaxes(title_text="Timeline")
fig.update_yaxes(title_text="actual targets", secondary_y=False)
fig.update_yaxes(title_text="predicted targets", secondary_y=True)
fig.show()

from prophet.diagnostics import cross_validation
df_cv = cross_validation(model, initial='1460 days', period='30 days', horizon='180 days')
df_cv.head()

from prophet.diagnostics import performance_metrics
df_p = performance_metrics(df_cv)
df_p.head()

import itertools
import numpy as np
import pandas as pd
from prophet.diagnostics import cross_validation
from prophet.diagnostics import performance_metrics


param_grid = {
    'changepoint_prior_scale': [0.5, 0.6,0.7,0.8,0.9,1.0],
    'seasonality_prior_scale': [0.001, 0.002,0.003,0.004,0.005],
}



# Generate all combinations of parameters
all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
rmses = []  # Store the RMSEs for each params here

# Use cross validation to evaluate all parameters
for params in all_params:
    m = Prophet(**params).fit(train_data)  # Fit model with given params
    df_cv = cross_validation(m,  initial='1460 days', period='30 days', horizon='180 days',  parallel="processes")
    df_p = performance_metrics(df_cv, rolling_window=1)
    rmses.append(df_p['rmse'].values[0])

# Find the best parameters
tuning_results = pd.DataFrame(all_params)
tuning_results['rmse'] = rmses
print(tuning_results)

best_params = all_params[np.argmin(rmses)]
print(best_params)

best_model = Prophet(changepoint_prior_scale=0.5,seasonality_prior_scale=0.005)
best_model.fit(train_data)

# Make forecasts for the next 6 months
future = best_model.make_future_dataframe(periods=6, freq='MS')
forecast = best_model.predict(future)

fig = model.plot(forecast, xlabel='Date', ylabel='Value', plot_cap=False)
pyplot.title('Forecast for the Next 6 Months')
pyplot.xlim(pd.Timestamp('2023-08-01'), pd.Timestamp('2024-01-01'))  # Adjust the date range
pyplot.ylim(50,150)

pyplot.show()

model.plot_components(forecast)

#Random Forest

#Data wrangling to count and group sick absence
training_data = data.groupby('operational_date')['EmployeeNumber'].count().reset_index()
training_data = training_data.rename(columns={
    'operational_date': 'Date',
    'EmployeeNumber': 'Sick_Absence_Count'
})
training_data.shape

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from matplotlib import pyplot as plt

training_data['Date'] = pd.to_datetime(training_data['Date'], format='%d/%m/%Y')
training_data.set_index('Date', inplace=True)

# Add lagged features
for i in range(1, 8):
    training_data[f'Sick_Absence_Count_Lag_{i}'] = training_data['Sick_Absence_Count'].shift(i)

# Drop missing values
training_data.dropna(inplace=True)

# Split the data into features and target
X = training_data.drop('Sick_Absence_Count', axis=1)
y = training_data['Sick_Absence_Count']

# Initialize the model
model = RandomForestRegressor(n_estimators=100)

# Fit the model
model.fit(X, y)

# Number of forecast steps (assuming daily data)
forecast_steps = 6 * 30

# Initialize the forecast list
forecast = []

# Initialize the lagged values with the most recent observations
last_row = training_data.drop('Sick_Absence_Count', axis=1).iloc[-1]

# Loop through the forecast period
for _ in range(forecast_steps):
    prediction = model.predict([last_row.values])
    forecast.append(prediction)

    # Update lagged values
    for i in range(7, 1, -1):
        last_row[f'Sick_Absence_Count_Lag_{i}'] = last_row[f'Sick_Absence_Count_Lag_{i-1}']
    last_row['Sick_Absence_Count_Lag_1'] = prediction

# Plot the forecast for the next 6 months
forecast_dates = pd.date_range(start='2023-08-01', periods=forecast_steps, freq='D')
plt.plot(forecast_dates, forecast, label='Forecast', color='blue')
plt.xlabel('Date')
plt.ylabel('Sick Absence Count')
plt.title('Random Forest Forecast for the Next 6 Months')
plt.grid(True)
plt.legend()
plt.show()

import pandas as pd
from sklearn.model_selection import train_test_split

# Assuming you have a DataFrame 'training_data' with 'Sick_Absence_Count' column and lagged features

# Create lagged features
lags = 7  # Example lag value
for i in range(1, lags + 1):
    training_data[f'Sick_Absence_Count_Lag_{i}'] = training_data['Sick_Absence_Count'].shift(i)

# Drop missing values due to lag
training_data.dropna(inplace=True)

# Define features (lagged values) and target variable
X = training_data.drop('Sick_Absence_Count', axis=1)
y = training_data['Sick_Absence_Count']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Define the parameter grid for Grid Search
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# Initialize the Random Forest Regressor
rf = RandomForestRegressor(random_state=42)

# Initialize GridSearchCV
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid,
                           scoring='neg_mean_squared_error', cv=5)

# Fit the Grid Search to the data
grid_search.fit(X_train, y_train)  # Make sure to replace X_train and y_train with your data

# Get the best parameters and best model
best_params = grid_search.best_params_
best_rf_model = grid_search.best_estimator_

# Predict on the test set using the best model
y_pred = best_rf_model.predict(X_test)  # Replace X_test with your test data

# Calculate RMSE
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print("Root Mean Squared Error:", rmse)

# You can also print the best parameters found by Grid Search
print("Best Parameters:", best_params)

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error


training_data['Date'] = pd.to_datetime(training_data['Date'], format='%d/%m/%Y')
training_data.set_index('Date', inplace=True)

# Add lagged features
for i in range(1, 8):
    training_data[f'Sick_Absence_Count_Lag_{i}'] = training_data['Sick_Absence_Count'].shift(i)

# Drop missing values
training_data.dropna(inplace=True)

# Split the data into features and target
X = training_data.drop('Sick_Absence_Count', axis=1)
y = training_data['Sick_Absence_Count']

# Set the random seed for reproducibility
np.random.seed(42)

# Instantiate the Random Forest model with the best parameters
best_params = {'max_depth': None, 'min_samples_leaf': 1, 'min_samples_split': 2, 'n_estimators': 300}
model = RandomForestRegressor(**best_params, random_state=42)

# Fit the model
model.fit(X, y)

# Number of forecast steps (assuming daily data)
forecast_steps = 6 * 30

# Initialize the forecast list
forecast = []

# Initialize the lagged values with the most recent observations
last_row = training_data.drop('Sick_Absence_Count', axis=1).iloc[-1]

# Loop through the forecast period
for _ in range(forecast_steps):
    prediction = model.predict([last_row.values])
    forecast.append(prediction)

    # Update lagged values
    for i in range(7, 1, -1):
        last_row[f'Sick_Absence_Count_Lag_{i}'] = last_row[f'Sick_Absence_Count_Lag_{i-1}']
    last_row['Sick_Absence_Count_Lag_1'] = prediction

# Calculate RMSE
test_actual = training_data['Sick_Absence_Count'][-forecast_steps:]
rmse = np.sqrt(mean_squared_error(test_actual, forecast))
print("Root Mean Squared Error:", rmse)

# Plot the forecast for the next 6 months
forecast_dates = pd.date_range(start='2023-08-01', periods=forecast_steps, freq='D')
plt.plot(forecast_dates, forecast, label='Forecast', color='blue')
plt.xlabel('Date')
plt.ylabel('Sick Absence Count')
plt.title('Random Forest Forecast for the Next 6 Months')
plt.grid(True)
plt.legend()
plt.ylim(100,200)
plt.show()

#LSTM

#Data wrangling to count and group sick absence
training_data = data.groupby('operational_date')['EmployeeNumber'].count().reset_index()
training_data = training_data.rename(columns={
    'operational_date': 'Date',
    'EmployeeNumber': 'Sick_Absence_Count'
})
training_data.shape

from scalecast.Forecaster import Forecaster
f = Forecaster(
y=training_data['Sick_Absence_Count'],
current_dates=training_data['Date'])

#Checking for staionarity
stat, pval, _, _, _, _ = f.adf_test(full_res=True)
print(stat)
print(pval)

f.plot_pacf(lags=26)
plt.show()

!pip install tensorflow

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, losses, regularizers, optimizers, callbacks
from sklearn.model_selection import train_test_split


# Extract the 'Sick_Absence_Count' column as the target variable
y = training_data['Sick_Absence_Count'].values

# Normalize the target variable (scaling between 0 and 1)
scaler = MinMaxScaler()
y_scaled = scaler.fit_transform(y.reshape(-1, 1))

# Define a function to create input sequences and labels
def create_sequences(data, seq_length):
    sequences = []
    target = []
    for i in range(len(data) - seq_length):
        seq = data[i:i+seq_length]
        label = data[i+seq_length]
        sequences.append(seq)
        target.append(label)
    return np.array(sequences), np.array(target)

# Define the sequence length (6  months)
sequence_length = 6

# Create input sequences and labels
X, y = create_sequences(y_scaled, sequence_length)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train = tf.convert_to_tensor(X_train, dtype=tf.float32)
X_test = tf.convert_to_tensor(X_test, dtype=tf.float32)
y_train = tf.convert_to_tensor(y_train, dtype=tf.float32)
y_test = tf.convert_to_tensor(y_test, dtype=tf.float32)

# Create an LSTM model
model = keras.Sequential([
    layers.LSTM(50, activation='relu', input_shape=(sequence_length, 1)),
    layers.Dense(1)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
history = model.fit(X_train, y_train, epochs=50, batch_size=64, validation_data=(X_test, y_test))

# Prepare data for forecasting
last_date = training_data['Date'].max()  # Get the last date in the data
future_dates = pd.date_range(last_date, periods=6, freq='M')  # Create 6 future months
future_months = future_dates.strftime('%B %Y')  # Format the future months
repeats = 10
# Create sequences for forecasting
X_future = []
for i in range(1, sequence_length + 1):
    X_future.append(y_scaled[-i:])
X_future = np.array(X_future)
# Pad sequences to have the same length
max_sequence_length = max(len(seq) for seq in X_future)
X_future = [np.pad(seq, ((0, max_sequence_length - len(seq)), (0, 0)), 'constant') for seq in X_future]

# Convert to TensorFlow tensor
X_future = tf.constant(X_future, dtype=tf.float32)

# Make forecasts for the next 6 months
forecasts = []
# Extend the forecasting for 6 more months (August 2023 to January 2024)
extended_forecast_months = [
    "August 2023", "September 2023", "October 2023",
    "November 2023", "December 2023", "January 2024"
]

# Calculate forecasts for the next 6 months
for month in extended_forecast_months:
    forecast = model.predict(X_future)
    forecasts.append(forecast[0, 0])  # Extract the forecasted value
    # Update X_future with the new forecast and shift the rest of the values
    X_future = np.roll(X_future, shift=-1)
    X_future[-1, -1, 0] = forecast[0, 0]

# Inverse transform the forecasts to get the original scale
forecasts_original_scale = scaler.inverse_transform(np.array(forecasts).reshape(-1, 1))

# Print the forecasts for the extended period in the original scale
for month, forecast in zip(extended_forecast_months, forecasts_original_scale):
    print(f"Forecast for {month}: {forecast[0]:.2f}")

import matplotlib.pyplot as plt


# Plot the training and validation loss over epochs
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training and Validation Loss Over Epochs')
plt.legend()
plt.show()

import matplotlib.pyplot as plt

# Assuming forecasts is a list containing the forecasted values for the next 6 months
# and future_months is a list containing the corresponding month-year labels

plt.figure(figsize= (10,5))
# Plot the forecast for the next 6 months
plt.plot(extended_forecast_months, forecasts_original_scale, marker='o', linestyle='-', color='blue')

# Set x-axis labels to the forecasted month-year labels
#plt.xticks(forecast_months_range, future_months, rotation=45)

plt.xlabel('Month-Year')
plt.ylabel('Sick Absence Count')
plt.title('Sick Absence Count Forecast for the Next 6 Months')
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()

model.save("Sick_Absence_Model")

pip install flask

pip install flask_cors jsonify
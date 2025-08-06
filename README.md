# Weather Forecast App (Flask)

A simple Flask web app to retrieve and display a 5-day weather forecast using a US ZIP code and the OpenWeatherMap API.

## Features

- Form-based ZIP code input
- 5-day forecast with high/low temperatures and precipitation totals

## Versioning

Created in Python 3.13

## Setup

cd weather-forecast-app

pip install -r requirements.txt

## Setting the OpenWeatherMap API Key

The app needs an API key from [OpenWeatherMap](https://openweathermap.org/api).

You can pass this key via an environment variable.

###  On Linux/macOS (bash/zsh)

export OPENWEATHER_API_KEY=your_api_key_here

###  On Windows cmd

set OPENWEATHER_API_KEY=your_api_key_here

## Run the app

On Windows:

python run.py

MacOs:

python3 run.py

Open in the browser and navigate to:

http://localhost:5000

## Attribution(s)

Weather data provided by https://openweathermap.org/

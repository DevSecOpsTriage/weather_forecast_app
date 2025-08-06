import requests
from flask import current_app
from requests.exceptions import RequestException
from datetime import datetime
import pandas as pd


def process_weather_data(weather_data):
    """Process raw weather data into daily summaries."""
    
    # Extract forecast list
    forecast_list = weather_data.get('list', [])
    
    if not forecast_list:
        return []
    
    # Convert to DataFrame for processing
    df_data = []
    
    for item in forecast_list:
        # Parse datetime
        dt_str = item.get('dt_txt', '')
        try:
            dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            date_key = dt_obj.strftime('%m/%d/%Y')  # M format
        except:
            continue
            
        # Extract data
        main_data = item.get('main', {})
        weather_data_item = item.get('weather', [{}])[0]
        rain_data = item.get('rain', {})
        snow_data = item.get('snow', {})
        clouds_data = item.get('clouds', {})
        
        df_data.append({
            'date': date_key,
            'datetime': dt_obj,
            'temp': main_data.get('temp'),
            'temp_min': main_data.get('temp_min'),
            'temp_max': main_data.get('temp_max'),
            'description': weather_data_item.get('description', ''),
            'rain_3h': rain_data.get('3h', 0),
            'snow_3h': snow_data.get('3h', 0),
            'clouds': clouds_data.get('all', 0)
        })
    
    if not df_data:
        return []
    
    df = pd.DataFrame(df_data)
    
    # Group by date and aggregate
    daily_summaries = []
    
    for date, group in df.groupby('date'):
        # Temperature processing
        temp_values = group['temp'].dropna()
        temp_min_values = group['temp_min'].dropna()
        temp_max_values = group['temp_max'].dropna()
        
        if len(temp_values) > 0:
            daily_high = round(temp_values.max())
            daily_low = round(temp_values.min())
        elif len(temp_max_values) > 0 and len(temp_min_values) > 0:
            daily_high = round(temp_max_values.max())
            daily_low = round(temp_min_values.min())
        else:
            daily_high = daily_low = None
        
        # Precipitation processing
        total_rain = group['rain_3h'].sum()
        total_snow = group['snow_3h'].sum()
        total_precipitation = total_rain + total_snow
        
        # Weather descriptions (get unique ones)
        descriptions = group['description'].dropna().unique()
        weather_description = ', '.join(descriptions) if len(descriptions) > 0 else 'No data'
        
        # Cloud coverage for sunshine calculation
        cloud_values = group['clouds'].dropna()
        avg_clouds = cloud_values.mean() if len(cloud_values) > 0 else None
        
        # Calculate sunshine hours (approximate)
        sunshine_hours = None
        sunshine_note = ""
        
        if avg_clouds is not None:
            # Rough calculation: 12 hours daylight * (1 - cloud_percentage/100)
            sunshine_hours = round(12 * (1 - avg_clouds/100), 1)
        else:
            sunshine_note = "Missing cloud data"
        
        # Notes for missing data
        notes = []
        expected_readings = 8  # Approximately 8 readings per day (24h / 3h)
        actual_readings = len(group)
        
        if actual_readings < expected_readings:
            notes.append(f"Missing {expected_readings - actual_readings} readings")
        
        temp_missing = len(group) - len(temp_values)
        if temp_missing > 0:
            notes.append(f"Missing {temp_missing} temperature readings")
            
        precip_missing = len(group) - len(group[group['rain_3h'].notna() | group['snow_3h'].notna()])
        if precip_missing > 0:
            notes.append(f"Missing {precip_missing} precipitation readings")
        
        if sunshine_note:
            notes.append(sunshine_note)
        
        notes_text = '; '.join(notes) if notes else 'Complete data'
        
        daily_summaries.append({
            'date': date,
            'temperature': f"{daily_high}/{daily_low}" if daily_high is not None and daily_low is not None else "No data",
            'precipitation': f"{total_precipitation:.1f}",
            'description': weather_description,
            'sunshine_hours': f"{sunshine_hours:.1f}" if sunshine_hours is not None else "No data",
            'notes': notes_text
        })
    
    # Sort by date
    daily_summaries.sort(key=lambda x: datetime.strptime(x['date'], '%m/%d/%Y'))
    
    return daily_summaries


def get_weather_by_zip(zip_code: str) -> tuple:
    """Fetch weather data for the given ZIP code from OpenWeather API and return processed data."""

    api_key = current_app.config.get("OPENWEATHER_API_KEY", "your_dev_key_here")
    #print(f"[DEBUG] Using API Key: {api_key}")

    if not api_key or api_key == "your_dev_key_here":
        raise EnvironmentError("OPENWEATHER_API_KEY is not set properly in your environment or config.")

    url = (
        f"http://api.openweathermap.org/data/2.5/forecast"
        f"?zip={zip_code}&appid={api_key}&units=metric"
    )

    try:
        # Add timeout to prevent hanging requests and DoS attacks
        response = requests.get(url, timeout=10)
        
        # Handle specific API error responses
        if response.status_code == 404:
            raise ValueError(f"ZIP code '{zip_code}' not found. Please check the ZIP code and try again.")
        elif response.status_code == 401:
            raise RuntimeError("API key is invalid or expired.")
        elif response.status_code == 429:
            raise RuntimeError("API rate limit exceeded. Please try again later.")
        
        response.raise_for_status()
        
        # Check response size to prevent memory exhaustion attacks
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 1024 * 1024:  # 1MB limit
            raise RuntimeError("Response too large from weather service.")
        
    except requests.exceptions.ConnectTimeout:
        raise RuntimeError("Connection to weather service timed out. Please try again.")
    except requests.exceptions.ReadTimeout:
        raise RuntimeError("Weather service took too long to respond. Please try again.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Weather service request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Unable to connect to weather service. Please check your internet connection.")
    except RequestException as e:
        if "404" in str(e):
            raise ValueError(f"ZIP code '{zip_code}' not found. Please check the ZIP code and try again.")
        raise RuntimeError(f"Error fetching weather data: {e}")

    #print(f"[DEBUG] Weather data fetched for ZIP {zip_code}")
    
    try:
        # Get raw weather data
        weather_data = response.json()
        
        # Validate that we got expected data structure
        if 'list' not in weather_data or not weather_data['list']:
            raise ValueError("No forecast data available for this location.")
        
        # Process into daily summaries
        daily_forecasts = process_weather_data(weather_data)
        
        if not daily_forecasts:
            raise ValueError("Unable to process forecast data for this location.")
        
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Unexpected response format from weather service: {e}")
    
    print(f"[DEBUG] Returning weather_data type: {type(weather_data)}")
    print(f"[DEBUG] Returning daily_forecasts type: {type(daily_forecasts)}")
    
    # Return both raw data and processed summaries
    return weather_data, daily_forecasts
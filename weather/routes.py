import re
from flask import render_template, request, abort, flash, redirect, url_for
from weather.weather_client import get_weather_by_zip


def validate_zip_code(zip_code):
    """Validate ZIP code format."""
    if not zip_code:
        return False, "ZIP code is required."
    
    # Remove any whitespace
    zip_code = zip_code.strip()
    
    # Check for basic US ZIP code format (5 digits or 5+4)
    if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
        return False, "Please enter a valid US ZIP code (5 digits, e.g., 10001)."
    
    return True, zip_code


def zip_form():
    return render_template("zip_form.html")


def forecast():
    zip_code = request.form.get("zip_code")
    
    # Validate ZIP code format
    is_valid, result = validate_zip_code(zip_code)
    if not is_valid:
        return render_template("zip_form.html", error=result)
    
    zip_code = result  # Use the cleaned ZIP code

    try:
        weather_data, daily_forecasts = get_weather_by_zip(zip_code)
    except ValueError as e:
        # Handle validation errors from weather_client
        return render_template("zip_form.html", error=str(e))
    except RuntimeError as e:
        # Handle API errors from weather_client
        return render_template("zip_form.html", error=f"Weather service error: {str(e)}")
    except Exception as e:
        # Handle any other unexpected errors
        return render_template("zip_form.html", error="An unexpected error occurred. Please try again.")
    
    return render_template("zip_forecast.html", 
                         weather=weather_data, 
                         daily_forecasts=daily_forecasts)


# Function to register routes
def register_routes(app):
    app.add_url_rule("/", "zip_form", zip_form, methods=["GET"])
    app.add_url_rule("/forecast", "forecast", forecast, methods=["POST"])
from flask import Flask

def create_app():
    app = Flask(__name__)

    from weather.config import Config
    app.config.from_object(Config)

    # Import and register routes explicitly here
    from weather import routes
    routes.register_routes(app)

    return app

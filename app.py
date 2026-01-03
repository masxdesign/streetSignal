"""
Flask application for Street Signal - London Retail & Property Street Intelligence Tool.
"""

import os
from flask import Flask
from routes.jobs import jobs_bp
from routes.geocode import geocode_bp


app = Flask(__name__)

# Register blueprints
app.register_blueprint(jobs_bp)
app.register_blueprint(geocode_bp)


if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    app.run(debug=True, host=host, port=port)

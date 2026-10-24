import os
from pathlib import Path


def create_app(config=None):
    from flask import Flask, send_from_directory
    from backend.controllers.api import api
    app = Flask(__name__, static_folder=None)
    app.config.update(DATA_DIR=os.environ.get('DATA_DIR', str(Path(__file__).resolve().parent.parent / 'data')))
    if config:
        app.config.update(config)
    app.register_blueprint(api, url_prefix='/api')
    dist = Path(__file__).resolve().parent.parent / 'dist'

    @app.get('/')
    def index():
        return send_from_directory(dist, 'index.html')

    @app.get('/assets/<path:name>')
    def assets(name):
        return send_from_directory(dist / 'assets', name)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response
    return app

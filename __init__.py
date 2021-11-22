from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap

db = PyMongo()
bs = Bootstrap()


def create_app():
    app = Flask(__name__)

    app.config['MONGO_URI'] = "mongodb://mongo:27017/go"
    app.config['SECRET_KEY'] = '1234'

    db.init_app(app)
    bs.init_app(app)

    with app.app_context():
        from . import routes

        return app

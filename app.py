from flask import Flask, Blueprint
from flask_restful import Api
from resources.irq_api import *

app = Flask(__name__)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

InterruptAPIV1(api)

if __name__ == '__main__':
	app.register_blueprint(api_bp)
	app.run(host="0.0.0.0",port=8080,debug=True)
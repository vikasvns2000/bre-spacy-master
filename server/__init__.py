# project/server/__init__.py

import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS



# for cors...
def after_request(response):
    header = response.headers
    #header['Access-Control-Allow-Origin'] = 'http://localhost:4200'
    header['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

app = Flask(__name__)
CORS(app, resources=["/auth/*","/bre/*"], origins=['http://angular-auth-hilife-chatbot.apps.rhocp.com','http://localhost:4200'])
#CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app_settings = os.getenv(
    'APP_SETTINGS',
    'server.config.DevelopmentConfig'
)
app.config.from_object(app_settings)

bcrypt = Bcrypt(app)


from server.api.bre_apis import bre_blueprint

#add what to do after every request - before sending the response
bre_blueprint.after_app_request(after_request)

app.register_blueprint(bre_blueprint)

# project/server/config.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))
POSTGRES_DB_NAME = os.getenv('POSTGRES_DB_NAME', 'postgresql.hilife-chatbot.svc')
MONGO_SERVER_NAME = os.getenv('MONGO_SERVER_NAME', 'mongodb.hilife-chatbot.svc')
postgres_local_base = 'postgresql://openhack:openhack@localhost/'
mongo_db_uri = 'mongodb://localhost:27017/test'
database_name = 'auth_db'


class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret_openhack')
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_DBNAME = 'test'


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_base + database_name


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_base + database_name + '_test'
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    SECRET_KEY = 'secret_openhack'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://openhack:openhack@' + POSTGRES_DB_NAME + '/' + database_name
    CORS_HEADERS = 'Content-Type'
    #MONGO_URI = 'mongodb://' + MONGO_SERVER_NAME + '/test'
    MONGO_HOST = MONGO_SERVER_NAME
    MONGO_USERNAME = 'openhack'
    MONGO_PASSWORD = 'openhack'
    MONGO_AUTH_SOURCE = 'test'
    MONGO_DBNAME = 'test'
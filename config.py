import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://acs_user:Nick_ACS_DB_Password@localhost:5432/acs_db')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
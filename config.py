import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    """Config settings for the app"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = os.environ.get('GOOGLE_DISCOVERY_URL')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@arhat.uk']
    POSTS_PER_PAGE = 5
    DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH = os.path.join(
        os.getcwd(),"private_key.txt"
        )
    DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH = os.path.join(
        os.getcwd(),"public_key.txt"
        )
    VAPID_PRIVATE_KEY = open(
        DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH, 
        "r+").readline().strip("\n")
    VAPID_PUBLIC_KEY = open(
        DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH, 
        "r+").read().strip("\n")
    VAPID_CLAIMS = {
    "sub": "mailto:admin@arhat.uk"
    }
    SUB_KEY ={
        'endpoint': """https://fcm.googleapis.com/fcm/send/fP-WhA51C
        _k:APA91bEqgqiKx4XSvsSLuSzauq350SmRXfL_5vY4UK3ykIxW6pU_
        S4HGktJrhG2abgWttO4EMV553OURRgCzFcv76SiAtwy1AOeXxE3LYRr94N0R
        P0tUZ1c0jpDwVwwngZ36NLdDWOpA""", 
        'expirationTime': None, 
        'keys': {'p256dh': """BHtLgF4m5_KSJKvlURF76D1oqKCeBFbbpleQNO
        Oq6LN65NZV1PtHpIHvZKlqCrrZxJaNGWOBWdcFX49YWO2dY3Y""", 
        'auth': 'gEJu6Peu5tvGhSuhaWb3tQ'}
        }
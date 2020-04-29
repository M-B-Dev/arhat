from flask import Blueprint

bp = Blueprint('sn', __name__)

from app.sn import routes
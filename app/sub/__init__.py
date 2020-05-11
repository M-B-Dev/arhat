from flask import Blueprint

bp = Blueprint('sub', __name__)

from app.sub import routes
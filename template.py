from app.models import User, Post

from app import create_app, db

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Returns a shell context."""
    return {'db': db, 'User': User, 'Post': Post}
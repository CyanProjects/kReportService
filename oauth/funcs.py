from functools import wraps
from quart import g, request, url_for, redirect
from .oauth import oauth


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if getattr(g, 'user', None) is None:
            return redirect(url_for('http:auth.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function

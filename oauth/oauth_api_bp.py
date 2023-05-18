from quart import Blueprint, request, render_template
from .structures import *
from .funcs import login_required
from .oauth import oauth

Bp = Blueprint('http:oauth', __name__, url_prefix='/api/oauth')

@Bp.route('/login', methods=["POST"])
async def login():
    pass
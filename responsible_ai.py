from flask import Blueprint, render_template

responsible_ai_bp = Blueprint('responsible_ai', __name__, url_prefix='/responsible-ai')

@responsible_ai_bp.route('/')
def index():
    return render_template('responsible_ai.html')

from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, CartItem, WishlistItem

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to continue.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.wishlist import wishlist_bp
from routes.orders import orders_bp
from routes.reviews import reviews_bp
from routes.admin import admin_bp
from routes.ai import ai_bp

app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(wishlist_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(ai_bp)

# Context processors
@app.context_processor
def inject_globals():
    cart_count = 0
    wishlist_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
        wishlist_count = WishlistItem.query.filter_by(user_id=current_user.id).count()
    from models import Category
    categories = Category.query.filter(Category.parent_id == None).all()
    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'nav_categories': categories,
    }

@app.template_filter('inr')
def inr_format(value):
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

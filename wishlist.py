from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, WishlistItem, Product, CartItem

wishlist_bp = Blueprint('wishlist', __name__)

@wishlist_bp.route('/wishlist')
@login_required
def view_wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', items=items)

@wishlist_bp.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    product_id = request.form.get('product_id', type=int)
    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        added = False
        message = 'Removed from wishlist'
    else:
        item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        added = True
        message = 'Added to wishlist!'
    count = WishlistItem.query.filter_by(user_id=current_user.id).count()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'added': added, 'message': message, 'count': count})
    flash(message, 'success' if added else 'info')
    return redirect(request.referrer or url_for('wishlist.view_wishlist'))

@wishlist_bp.route('/wishlist/move-to-cart/<int:item_id>', methods=['POST'])
@login_required
def move_to_cart(item_id):
    wish_item = WishlistItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    existing_cart = CartItem.query.filter_by(user_id=current_user.id, product_id=wish_item.product_id).first()
    if not existing_cart:
        cart_item = CartItem(user_id=current_user.id, product_id=wish_item.product_id, quantity=1)
        db.session.add(cart_item)
    db.session.delete(wish_item)
    db.session.commit()
    flash('Moved to cart!', 'success')
    return redirect(url_for('wishlist.view_wishlist'))

@wishlist_bp.route('/wishlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    item = WishlistItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Removed from wishlist.', 'info')
    return redirect(url_for('wishlist.view_wishlist'))

from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Review, Product

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews/add', methods=['POST'])
@login_required
def add_review():
    product_id = request.form.get('product_id', type=int)
    rating = request.form.get('rating', type=int)
    title = request.form.get('title', '').strip()
    comment = request.form.get('comment', '').strip()
    product = Product.query.get_or_404(product_id)

    if not (1 <= rating <= 5):
        flash('Please select a valid rating.', 'danger')
        return redirect(url_for('products.product_detail', slug=product.slug))

    existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.rating = rating
        existing.title = title
        existing.comment = comment
    else:
        review = Review(user_id=current_user.id, product_id=product_id,
                        rating=rating, title=title, comment=comment)
        db.session.add(review)

    # Recalculate product rating
    from sqlalchemy import func
    avg = db.session.query(func.avg(Review.rating)).filter_by(product_id=product_id).scalar()
    count = Review.query.filter_by(product_id=product_id).count()
    product.rating = round(float(avg or 0), 1)
    product.rating_count = count
    db.session.commit()
    flash('Review submitted! Thank you.', 'success')
    return redirect(url_for('products.product_detail', slug=product.slug))

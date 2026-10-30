from flask import Blueprint, render_template, request, jsonify, abort
from models import db, Product, Category
from sqlalchemy import or_, func
from config import Config

products_bp = Blueprint('products', __name__)

PER_PAGE = Config.PRODUCTS_PER_PAGE

@products_bp.route('/')
def home():
    featured = Product.query.filter_by(is_featured=True, is_active=True).limit(12).all()
    top_deals = Product.query.filter(Product.discount_percent >= 40, Product.is_active == True).order_by(
        Product.discount_percent.desc()).limit(20).all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(16).all()
    top_categories = Category.query.filter(Category.parent_id == None).all()
    flash_deals = Product.query.filter(Product.discount_percent >= 50, Product.is_active == True).order_by(
        func.random()).limit(8).all()
    return render_template('index.html',
                           featured=featured,
                           top_deals=top_deals,
                           new_arrivals=new_arrivals,
                           categories=top_categories,
                           flash_deals=flash_deals)


@products_bp.route('/products')
def product_list():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', '')
    search_q = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'popular')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 999999, type=float)
    min_rating = request.args.get('rating', 0, type=float)
    brand_filter = request.args.get('brand', '')

    query = Product.query.filter_by(is_active=True)

    category = None
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        child_ids = [c.id for c in category.children]
        if child_ids:
            query = query.filter(or_(Product.category_id == category.id,
                                     Product.category_id.in_(child_ids)))
        else:
            query = query.filter_by(category_id=category.id)

    if search_q:
        query = query.filter(or_(
            Product.name.ilike(f'%{search_q}%'),
            Product.description.ilike(f'%{search_q}%'),
            Product.brand.ilike(f'%{search_q}%'),
            Product.tags.ilike(f'%{search_q}%'),
        ))

    if brand_filter:
        query = query.filter(Product.brand.ilike(f'%{brand_filter}%'))

    if min_rating > 0:
        query = query.filter(Product.rating >= min_rating)

    query = query.filter(Product.original_price >= min_price)
    if max_price < 999999:
        query = query.filter(Product.original_price <= max_price)

    sort_map = {
        'popular': Product.rating_count.desc(),
        'price_low': Product.original_price.asc(),
        'price_high': Product.original_price.desc(),
        'rating': Product.rating.desc(),
        'newest': Product.created_at.desc(),
        'discount': Product.discount_percent.desc(),
    }
    query = query.order_by(sort_map.get(sort_by, Product.rating_count.desc()))

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    all_categories = Category.query.filter(Category.parent_id == None).all()

    return render_template('products/list.html',
                           products=pagination.items,
                           pagination=pagination,
                           category=category,
                           categories=all_categories,
                           search_q=search_q,
                           sort_by=sort_by,
                           min_price=min_price,
                           max_price=max_price,
                           min_rating=min_rating)


@products_bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).order_by(func.random()).limit(8).all()

    from flask_login import current_user
    from models import WishlistItem, CartItem
    in_wishlist = False
    in_cart = False
    if current_user.is_authenticated:
        in_wishlist = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
        in_cart = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None

    return render_template('products/detail.html',
                           product=product,
                           related=related,
                           in_wishlist=in_wishlist,
                           in_cart=in_cart)


@products_bp.route('/api/search-suggestions')
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    results = Product.query.filter(
        Product.name.ilike(f'%{q}%'),
        Product.is_active == True
    ).limit(8).all()
    return jsonify([{'name': p.name, 'slug': p.slug, 'price': p.discounted_price,
                     'image': p.image_url} for p in results])

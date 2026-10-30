from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products.home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}! 🎉', 'success')
            return redirect(next_page or url_for('products.home'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('products.home'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')
        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash(f'Welcome to ShopKart, {name}! 🛒', 'success')
        return redirect(url_for('products.home'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('products.home'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import Address
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            current_user.name = request.form.get('name', current_user.name).strip()
            current_user.phone = request.form.get('phone', current_user.phone).strip()
            db.session.commit()
            flash('Profile updated!', 'success')
        elif action == 'add_address':
            addr = Address(
                user_id=current_user.id,
                name=request.form.get('addr_name'),
                phone=request.form.get('addr_phone'),
                street=request.form.get('addr_street'),
                city=request.form.get('addr_city'),
                state=request.form.get('addr_state'),
                pincode=request.form.get('addr_pincode'),
                address_type=request.form.get('addr_type', 'Home'),
            )
            db.session.add(addr)
            db.session.commit()
            flash('Address added!', 'success')
        elif action == 'delete_address':
            addr_id = request.form.get('addr_id')
            addr = Address.query.filter_by(id=addr_id, user_id=current_user.id).first()
            if addr:
                db.session.delete(addr)
                db.session.commit()
                flash('Address deleted.', 'info')
        return redirect(url_for('auth.profile'))
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('auth/profile.html', addresses=addresses)

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Order, OrderItem, CartItem, Address, Coupon, Product
from datetime import datetime, timedelta

orders_bp = Blueprint('orders', __name__)

def apply_coupon(code, subtotal):
    """Returns (discount_amount, error_message)"""
    coupon = Coupon.query.filter_by(code=code.upper(), is_active=True).first()
    if not coupon:
        return 0, "Invalid coupon code."
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        return 0, "Coupon has expired."
    if coupon.uses_left <= 0:
        return 0, "Coupon usage limit reached."
    if subtotal < coupon.min_order:
        return 0, f"Minimum order ₹{coupon.min_order:.0f} required."

    if coupon.discount_percent > 0:
        discount = min(subtotal * coupon.discount_percent / 100, coupon.max_discount)
    else:
        discount = min(coupon.discount_flat, subtotal)
    return round(discount, 2), None


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    addresses = Address.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.subtotal() for item in cart_items)
    shipping = 0 if subtotal >= 499 else 49

    coupon_code = request.form.get('coupon_code', '').strip()
    discount = 0
    coupon_error = None
    if coupon_code:
        discount, coupon_error = apply_coupon(coupon_code, subtotal)

    if request.method == 'POST':
        action = request.form.get('action', 'place_order')
        if action == 'place_order':
            address_id = request.form.get('address_id')
            if address_id and address_id != 'new' and str(address_id).isdigit():
                address_id = int(address_id)
                # Verify address belongs to current user
                existing_addr = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
                if not existing_addr:
                    address_id = None
            else:
                address_id = None

            payment_method = request.form.get('payment_method', 'COD')
            coupon_code = request.form.get('coupon_code', '').strip()
            discount, coupon_error = apply_coupon(coupon_code, subtotal) if coupon_code else (0, None)

            if not address_id:
                # Create new address if submitted
                addr_name = (request.form.get('addr_name') or request.form.get('full_name') or '').strip()
                addr_phone = (request.form.get('addr_phone') or request.form.get('phone') or '').strip()
                addr_street = (request.form.get('addr_street') or request.form.get('street') or '').strip()
                addr_city = (request.form.get('addr_city') or request.form.get('city') or '').strip()
                addr_state = (request.form.get('addr_state') or request.form.get('state') or '').strip()
                addr_pincode = (request.form.get('addr_pincode') or request.form.get('pincode') or '').strip()
                if not all([addr_name, addr_phone, addr_street, addr_city, addr_state, addr_pincode]):
                    flash('Please fill in a complete delivery address.', 'danger')
                    return redirect(url_for('orders.checkout'))
                addr = Address(
                    user_id=current_user.id,
                    name=addr_name,
                    phone=addr_phone,
                    street=addr_street,
                    city=addr_city,
                    state=addr_state,
                    pincode=addr_pincode,
                )
                db.session.add(addr)
                db.session.flush()
                address_id = addr.id

        total = subtotal + shipping - discount
        delivery_date = (datetime.utcnow() + timedelta(days=5)).strftime('%d %b %Y')

        order = Order(
            user_id=current_user.id,
            address_id=address_id,
            subtotal=subtotal,
            discount_amount=discount,
            shipping_fee=shipping,
            total=total,
            coupon_code=coupon_code if discount > 0 else None,
            payment_method=payment_method,
            payment_status='Pending' if payment_method == 'COD' else 'Paid',
            status='Placed',
            estimated_delivery=delivery_date,
        )
        db.session.add(order)
        db.session.flush()

        for ci in cart_items:
            oi = OrderItem(
                order_id=order.id,
                product_id=ci.product_id,
                quantity=ci.quantity,
                price=ci.product.discounted_price,
                product_name=ci.product.name,
                product_image=ci.product.image_url,
            )
            db.session.add(oi)
            # Reduce stock
            ci.product.stock = max(0, ci.product.stock - ci.quantity)

        # Reduce coupon uses
        if coupon_code and discount > 0:
            coupon = Coupon.query.filter_by(code=coupon_code.upper()).first()
            if coupon:
                coupon.uses_left -= 1

        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash(f'🎉 Order placed successfully! Order #{order.id}', 'success')
        return redirect(url_for('orders.order_detail', order_id=order.id))

    total = subtotal + shipping - discount
    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           discount=discount,
                           total=total,
                           addresses=addresses,
                           coupon_code=coupon_code,
                           coupon_error=coupon_error)


@orders_bp.route('/orders')
@login_required
def order_list():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/list.html', orders=orders)


@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('orders/detail.html', order=order)


@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    if order.status in ['Placed', 'Confirmed']:
        order.status = 'Cancelled'
        # Restore stock
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
        db.session.commit()
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Order cannot be cancelled at this stage.', 'warning')
    return redirect(url_for('orders.order_detail', order_id=order_id))


@orders_bp.route('/api/apply-coupon', methods=['POST'])
@login_required
def api_apply_coupon():
    code = request.json.get('code', '').strip()
    subtotal = request.json.get('subtotal', 0)
    discount, error = apply_coupon(code, subtotal)
    if error:
        return jsonify({'success': False, 'message': error})
    return jsonify({'success': True, 'discount': discount,
                    'message': f'Coupon applied! You save ₹{discount:.0f}'})

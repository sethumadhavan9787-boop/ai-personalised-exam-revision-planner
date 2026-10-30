from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import Product, Category
from config import Config
import os

ai_bp = Blueprint('ai', __name__)

def get_groq_client():
    try:
        from groq import Groq
        api_key = Config.GROQ_API_KEY
        if not api_key or api_key == 'your_groq_api_key_here':
            return None
        return Groq(api_key=api_key)
    except Exception:
        return None

@ai_bp.route('/api/chat', methods=['POST'])
def ai_chat():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    # Try to find relevant products from DB
    words = user_message.lower().split()
    search_query = ' '.join([w for w in words if len(w) > 3])
    from sqlalchemy import or_
    suggested_products = []
    if search_query:
        prods = Product.query.filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.tags.ilike(f'%{search_query}%'),
                Product.brand.ilike(f'%{search_query}%'),
            ),
            Product.is_active == True
        ).limit(4).all()
        suggested_products = [
            {'name': p.name, 'price': p.discounted_price, 'slug': p.slug,
             'image': p.image_url, 'discount': p.discount_percent, 'rating': p.rating}
            for p in prods
        ]

    client = get_groq_client()
    if client:
        try:
            product_context = ""
            if suggested_products:
                product_context = "\n\nAvailable products:\n" + "\n".join(
                    [f"- {p['name']} at ₹{p['price']:.0f} ({p['discount']:.0f}% off)" for p in suggested_products]
                )
            system_prompt = f"""You are ShopBot, a friendly AI shopping assistant for ShopKart — an Indian e-commerce store.
Help users find products, compare items, and make purchase decisions.
Be concise, friendly, and helpful. Use Indian Rupees (₹).
If users ask about specific products, mention what's available from the store.
Keep responses short (2-3 sentences max).{product_context}"""

            response = client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            ai_reply = get_fallback_response(user_message, suggested_products)
    else:
        ai_reply = get_fallback_response(user_message, suggested_products)

    return jsonify({
        'reply': ai_reply,
        'products': suggested_products[:3]
    })

def get_fallback_response(message, products):
    msg_lower = message.lower()
    if any(w in msg_lower for w in ['hello', 'hi', 'hey']):
        return "Hi there! 👋 I'm ShopBot, your shopping assistant. What are you looking for today?"
    elif any(w in msg_lower for w in ['deal', 'offer', 'discount', 'sale']):
        return "We have amazing deals! Check out our Flash Deals section for up to 70% off. 🔥"
    elif any(w in msg_lower for w in ['return', 'refund', 'exchange']):
        return "We offer a 10-day easy return policy on all products. Just go to My Orders to initiate a return. 📦"
    elif any(w in msg_lower for w in ['delivery', 'shipping', 'ship']):
        return "Free delivery on orders above ₹499! Standard delivery takes 5-7 business days. 🚚"
    elif products:
        names = ", ".join([p['name'][:30] for p in products[:2]])
        return f"I found some great options for you: {names}. Check them out! 🛒"
    else:
        return "I can help you find products, check deals, or answer questions about your orders. What do you need? 😊"


@ai_bp.route('/api/smart-search', methods=['POST'])
def smart_search():
    """AI-powered natural language search"""
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({'products': []})

    client = get_groq_client()
    search_term = query

    if client:
        try:
            response = client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "Extract the main product/item keywords from the user's shopping query. Return only 3-5 keywords separated by spaces. No explanations."},
                    {"role": "user", "content": query}
                ],
                max_tokens=30,
            )
            search_term = response.choices[0].message.content.strip()
        except Exception:
            pass

    from sqlalchemy import or_
    keywords = search_term.split()
    conditions = []
    for kw in keywords:
        conditions.append(Product.name.ilike(f'%{kw}%'))
        conditions.append(Product.brand.ilike(f'%{kw}%'))
        conditions.append(Product.tags.ilike(f'%{kw}%'))

    products = Product.query.filter(or_(*conditions), Product.is_active == True).limit(12).all()
    return jsonify({
        'products': [
            {'name': p.name, 'price': p.discounted_price, 'original_price': p.original_price,
             'slug': p.slug, 'image': p.image_url, 'discount': p.discount_percent, 'rating': p.rating}
            for p in products
        ]
    })

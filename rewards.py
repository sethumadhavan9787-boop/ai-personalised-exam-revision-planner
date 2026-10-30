from flask import Blueprint, render_template, request, jsonify
from database import get_db, get_current_user, purchase_reward, equip_reward

rewards_bp = Blueprint('rewards', __name__)

@rewards_bp.route('/rewards')
def rewards_catalog():
    user = get_current_user()
    category = request.args.get('category', 'all')
    conn = get_db()
    cursor = conn.cursor()

    # Fetch user's inventory
    cursor.execute("""
        SELECT reward_id, is_equipped 
        FROM user_inventory 
        WHERE user_id = ?
    """, (user['id'],))
    inventory_map = {row['reward_id']: bool(row['is_equipped']) for row in cursor.fetchall()}

    # Fetch rewards
    if category != 'all':
        cursor.execute("SELECT * FROM rewards WHERE type = ? ORDER BY cost ASC", (category,))
    else:
        cursor.execute("SELECT * FROM rewards ORDER BY cost ASC")
    
    reward_rows = cursor.fetchall()
    rewards = []
    for r in reward_rows:
        item = dict(r)
        item['is_owned'] = item['id'] in inventory_map
        item['is_equipped'] = inventory_map.get(item['id'], False)
        rewards.append(item)

    conn.close()

    return render_template('rewards.html',
                           user=user,
                           rewards=rewards,
                           active_category=category)

@rewards_bp.route('/api/purchase-reward', methods=['POST'])
def api_purchase():
    data = request.get_json() or {}
    reward_id = data.get('reward_id')
    if not reward_id:
        return jsonify({'success': False, 'message': 'Missing reward_id'}), 400

    user = get_current_user()
    result = purchase_reward(user['id'], int(reward_id))
    result['user'] = get_current_user(user['id'])
    return jsonify(result)

@rewards_bp.route('/api/equip-reward', methods=['POST'])
def api_equip():
    data = request.get_json() or {}
    reward_id = data.get('reward_id')
    if not reward_id:
        return jsonify({'success': False, 'message': 'Missing reward_id'}), 400

    user = get_current_user()
    result = equip_reward(user['id'], int(reward_id))
    result['user'] = get_current_user(user['id'])
    return jsonify(result)

from flask import Blueprint, render_template, request, jsonify
from database import get_db, get_current_user, reset_user_progress

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings_page():
    user = get_current_user()
    return render_template('settings.html', user=user)

@settings_bp.route('/api/update-settings', methods=['POST'])
def api_update_settings():
    data = request.get_json() or {}
    user = get_current_user()
    
    username = data.get('username', '').strip()
    avatar = data.get('avatar', '').strip()
    sound_enabled = 1 if data.get('sound_enabled', True) else 0
    music_enabled = 1 if data.get('music_enabled', True) else 0
    theme = data.get('theme', 'dark').strip()

    if not username:
        return jsonify({'success': False, 'message': 'Username cannot be empty'}), 400
    if len(username) > 20:
        return jsonify({'success': False, 'message': 'Username cannot exceed 20 characters'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users 
            SET username = ?, avatar = ?, sound_enabled = ?, music_enabled = ?, theme = ?
            WHERE id = ?
        """, (username, avatar or user['avatar'], sound_enabled, music_enabled, theme, user['id']))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Username is already taken or invalid'}), 400

    conn.close()
    return jsonify({'success': True, 'message': 'Settings saved successfully!'})

@settings_bp.route('/api/reset-progress', methods=['POST'])
def api_reset_progress():
    data = request.get_json() or {}
    confirm_text = data.get('confirm_text', '').strip()

    if confirm_text != 'RESET':
        return jsonify({'success': False, 'message': 'Type RESET in all caps to confirm progress reset.'}), 400

    user = get_current_user()
    reset_user_progress(user['id'])
    return jsonify({'success': True, 'message': 'All progress has been reset to default initial state.'})

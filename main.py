from flask import Blueprint, render_template, jsonify, request
from database import get_db, get_current_user, get_streak_info, claim_daily_reward

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    user = get_current_user()
    streak = get_streak_info()
    conn = get_db()
    cursor = conn.cursor()

    # Quick statistics
    cursor.execute("""
        SELECT COUNT(*) as total_played, COALESCE(MAX(score), 0) as best_score 
        FROM game_history 
        WHERE user_id = ?
    """, (user['id'],))
    stats = dict(cursor.fetchone())

    # Get games list with high scores for this user
    cursor.execute("""
        SELECT g.*, COALESCE(gs.high_score, 0) as user_high_score, COALESCE(gs.times_played, 0) as times_played
        FROM games g
        LEFT JOIN game_scores gs ON g.id = gs.game_id AND gs.user_id = ?
        ORDER BY g.id ASC
    """, (user['id'],))
    games = [dict(row) for row in cursor.fetchall()]

    # Recent activity
    cursor.execute("""
        SELECT gh.*, g.title, g.icon
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ?
        ORDER BY gh.played_at DESC
        LIMIT 5
    """, (user['id'],))
    recent_games = [dict(row) for row in cursor.fetchall()]

    # Unlocked achievements count
    cursor.execute("""
        SELECT COUNT(*) as unlocked_count 
        FROM user_achievements 
        WHERE user_id = ? AND is_unlocked = 1
    """, (user['id'],))
    ach_unlocked = cursor.fetchone()['unlocked_count']

    cursor.execute("SELECT COUNT(*) as total_count FROM achievements")
    ach_total = cursor.fetchone()['total_count']

    conn.close()

    return render_template('index.html',
                           user=user,
                           streak=streak,
                           stats=stats,
                           games=games,
                           recent_games=recent_games,
                           ach_unlocked=ach_unlocked,
                           ach_total=ach_total)

@main_bp.route('/api/claim-daily', methods=['POST'])
def api_claim_daily():
    user = get_current_user()
    result = claim_daily_reward(user['id'])
    user_updated = get_current_user(user['id'])
    streak_updated = get_streak_info(user['id'])
    result['user'] = user_updated
    result['streak'] = streak_updated
    return jsonify(result)

@main_bp.route('/api/user-stats', methods=['GET'])
def api_user_stats():
    user = get_current_user()
    streak = get_streak_info()
    return jsonify({'user': user, 'streak': streak})

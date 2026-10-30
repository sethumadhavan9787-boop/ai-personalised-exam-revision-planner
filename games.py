from flask import Blueprint, render_template, jsonify, request, abort
from database import (
    get_db, get_current_user, submit_game_score,
    toggle_favorite, get_user_favorite_ids,
    get_user_daily_challenges, claim_daily_challenge,
    get_daily_reward_calendar
)

games_bp = Blueprint('games', __name__)

@games_bp.route('/games')
def games_list():
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.*, 
               COALESCE(gs.high_score, 0) as user_high_score, 
               COALESCE(gs.times_played, 0) as times_played
        FROM games g
        LEFT JOIN game_scores gs ON g.id = gs.game_id AND gs.user_id = ?
        ORDER BY g.category ASC, g.id ASC
    """, (user['id'],))
    games_rows = [dict(row) for row in cursor.fetchall()]

    # Fetch user favorites
    fav_ids = get_user_favorite_ids(user['id'])
    for g in games_rows:
        g['is_favorite'] = (g['id'] in fav_ids)

    # Fetch recently played games (most recent unique games)
    cursor.execute("""
        SELECT DISTINCT g.slug, g.title, g.icon, g.category, g.color, gh.played_at
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ?
        ORDER BY gh.played_at DESC
        LIMIT 6
    """, (user['id'],))
    recently_played = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Get daily challenges
    daily_challenges = get_user_daily_challenges(user['id'])

    return render_template('games.html', 
                           user=user, 
                           games=games_rows, 
                           recently_played=recently_played,
                           daily_challenges=daily_challenges)

@games_bp.route('/games/<slug>')
def play_game(slug):
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM games WHERE slug = ?", (slug,))
    game_row = cursor.fetchone()
    if not game_row:
        conn.close()
        abort(404)

    game = dict(game_row)

    # Get user's high score for this game
    cursor.execute("SELECT * FROM game_scores WHERE user_id = ? AND game_id = ?", (user['id'], game['id']))
    score_row = cursor.fetchone()
    user_high_score = score_row['high_score'] if score_row else 0
    times_played = score_row['times_played'] if score_row else 0

    # Get equipped skins/effects for this game or user
    cursor.execute("""
        SELECT r.* FROM user_inventory ui
        JOIN rewards r ON ui.reward_id = r.id
        WHERE ui.user_id = ? AND ui.is_equipped = 1 AND (r.game_slug = ? OR r.type = 'effect')
    """, (user['id'], slug))
    equipped_items = [dict(row) for row in cursor.fetchall()]

    # Check favorite status
    cursor.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND game_id = ?", (user['id'], game['id']))
    is_favorite = bool(cursor.fetchone())

    # Other games for "More Games" recommendation bar
    cursor.execute("SELECT * FROM games WHERE slug != ? ORDER BY RANDOM() LIMIT 4", (slug,))
    other_games = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template('game_play.html',
                           user=user,
                           game=game,
                           is_favorite=is_favorite,
                           user_high_score=user_high_score,
                           times_played=times_played,
                           equipped_items=equipped_items,
                           other_games=other_games)

@games_bp.route('/api/submit-score', methods=['POST'])
def api_submit_score():
    data = request.get_json() or {}
    game_slug = data.get('game_slug')
    score = data.get('score')
    metadata = data.get('metadata', {})

    if not game_slug or score is None:
        return jsonify({'success': False, 'message': 'Missing game_slug or score'}), 400

    try:
        score = int(score)
        if score < 0 or score > 10000000:
            return jsonify({'success': False, 'message': 'Score out of valid bounds'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid score format'}), 400

    user = get_current_user()
    result = submit_game_score(user['id'], game_slug, score, metadata)
    result['user'] = get_current_user(user['id'])
    return jsonify(result)

@games_bp.route('/api/toggle-favorite', methods=['POST'])
def api_toggle_favorite():
    data = request.get_json() or {}
    game_id = data.get('game_id')
    game_slug = data.get('game_slug')

    conn = get_db()
    cursor = conn.cursor()
    if not game_id and game_slug:
        cursor.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        row = cursor.fetchone()
        if row:
            game_id = row['id']
    conn.close()

    if not game_id:
        return jsonify({'success': False, 'message': 'Missing game identifier'}), 400

    user = get_current_user()
    is_fav = toggle_favorite(user['id'], game_id)
    return jsonify({'success': True, 'game_id': game_id, 'is_favorite': is_fav})

@games_bp.route('/api/daily-challenges', methods=['GET'])
def api_daily_challenges():
    user = get_current_user()
    challenges = get_user_daily_challenges(user['id'])
    return jsonify({'success': True, 'challenges': challenges})

@games_bp.route('/api/claim-daily-challenge', methods=['POST'])
def api_claim_daily_challenge():
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    if not challenge_id:
        return jsonify({'success': False, 'message': 'Missing challenge_id'}), 400

    user = get_current_user()
    result = claim_daily_challenge(user['id'], challenge_id)
    if result.get('success'):
        result['user'] = get_current_user(user['id'])
    return jsonify(result)

@games_bp.route('/api/daily-reward-calendar', methods=['GET'])
def api_daily_reward_calendar():
    user = get_current_user()
    cal_data = get_daily_reward_calendar(user['id'])
    return jsonify({'success': True, 'data': cal_data})

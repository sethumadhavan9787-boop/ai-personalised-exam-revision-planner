from flask import Blueprint, render_template, request, jsonify
from database import get_db, get_current_user

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard')
def leaderboard_view():
    user = get_current_user()
    timeframe = request.args.get('timeframe', 'global')
    game_filter = request.args.get('game', 'all')

    if timeframe not in ['daily', 'weekly', 'global']:
        timeframe = 'global'

    conn = get_db()
    cursor = conn.cursor()

    # Get games for dropdown filter
    cursor.execute("SELECT slug, title, icon FROM games ORDER BY id ASC")
    all_games = [dict(row) for row in cursor.fetchall()]

    # Fetch leaderboard entries
    # If specific game selected, look up game_scores or leaderboard_players
    entries = []

    # Get current user's score and level
    if game_filter == 'all':
        cursor.execute("SELECT COALESCE(MAX(score), 0) as user_best FROM game_history WHERE user_id = ?", (user['id'],))
        user_best = cursor.fetchone()['user_best']
    else:
        cursor.execute("""
            SELECT COALESCE(gs.high_score, 0) as user_best 
            FROM games g
            LEFT JOIN game_scores gs ON g.id = gs.game_id AND gs.user_id = ?
            WHERE g.slug = ?
        """, (user['id'], game_filter))
        row = cursor.fetchone()
        user_best = row['user_best'] if row else 0

    # Fetch demo competitors for this timeframe
    cursor.execute("""
        SELECT username, avatar, score, level 
        FROM leaderboard_players 
        WHERE timeframe = ?
        ORDER BY score DESC
    """, (timeframe,))
    demo_players = [dict(row) for row in cursor.fetchall()]

    # Insert current user into the list dynamically to position them accurately
    user_entry = {
        'username': user['username'],
        'avatar': user['avatar'],
        'score': user_best,
        'level': user['level'],
        'is_current_user': True
    }
    
    all_entries = []
    for dp in demo_players:
        dp['is_current_user'] = False
        all_entries.append(dp)
    all_entries.append(user_entry)

    # Sort descending by score
    all_entries.sort(key=lambda x: x['score'], reverse=True)

    # Assign ranks
    ranked_entries = []
    user_rank = 0
    for idx, entry in enumerate(all_entries, 1):
        entry['rank'] = idx
        if entry['is_current_user']:
            user_rank = idx
        ranked_entries.append(entry)

    podium = ranked_entries[:3]
    top_entries = ranked_entries[:50]

    conn.close()

    return render_template('leaderboard.html',
                           user=user,
                           timeframe=timeframe,
                           game_filter=game_filter,
                           all_games=all_games,
                           podium=podium,
                           entries=top_entries,
                           user_rank=user_rank,
                           user_best=user_best)

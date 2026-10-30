from flask import Blueprint, render_template, request
from database import get_db, get_current_user

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
def game_history_view():
    user = get_current_user()
    game_filter = request.args.get('game', 'all')
    tab = request.args.get('tab', 'games') # 'games' or 'coins'
    
    conn = get_db()
    cursor = conn.cursor()

    # Get games list for filter
    cursor.execute("SELECT slug, title, icon FROM games ORDER BY id ASC")
    games = [dict(row) for row in cursor.fetchall()]

    # Fetch game history
    if game_filter == 'all':
        cursor.execute("""
            SELECT gh.*, g.title as game_title, g.icon as game_icon, g.slug as game_slug
            FROM game_history gh
            JOIN games g ON gh.game_id = g.id
            WHERE gh.user_id = ?
            ORDER BY gh.played_at DESC
            LIMIT 100
        """, (user['id'],))
    else:
        cursor.execute("""
            SELECT gh.*, g.title as game_title, g.icon as game_icon, g.slug as game_slug
            FROM game_history gh
            JOIN games g ON gh.game_id = g.id
            WHERE gh.user_id = ? AND g.slug = ?
            ORDER BY gh.played_at DESC
            LIMIT 100
        """, (user['id'], game_filter))
    
    history_records = [dict(row) for row in cursor.fetchall()]

    # Fetch coin transactions
    cursor.execute("""
        SELECT * FROM coin_transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 100
    """, (user['id'],))
    transactions = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template('history.html',
                           user=user,
                           games=games,
                           active_filter=game_filter,
                           active_tab=tab,
                           history_records=history_records,
                           transactions=transactions)

from flask import Blueprint, render_template
from database import get_db, get_current_user, get_detailed_game_stats

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def user_profile():
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()

    # Total score and games count
    cursor.execute("""
        SELECT COUNT(*) as total_games, 
               COALESCE(SUM(score), 0) as cumulative_score,
               COALESCE(MAX(score), 0) as max_score,
               COALESCE(SUM(coins_earned), 0) as lifetime_coins,
               COALESCE(SUM(xp_earned), 0) as lifetime_xp
        FROM game_history
        WHERE user_id = ?
    """, (user['id'],))
    aggregate = dict(cursor.fetchone())

    # Streak info
    cursor.execute("SELECT current_streak, longest_streak FROM daily_streaks WHERE user_id = ?", (user['id'],))
    streak_row = cursor.fetchone()
    streak = dict(streak_row) if streak_row else {'current_streak': 0, 'longest_streak': 0}

    # Detailed statistics for each game
    game_stats = get_detailed_game_stats(user['id'])

    # Unlocked achievements
    cursor.execute("""
        SELECT a.*, ua.unlocked_at
        FROM user_achievements ua
        JOIN achievements a ON ua.achievement_id = a.id
        WHERE ua.user_id = ? AND ua.is_unlocked = 1
        ORDER BY ua.unlocked_at DESC
    """, (user['id'],))
    unlocked_achievements = [dict(row) for row in cursor.fetchall()]

    # Inventory
    cursor.execute("""
        SELECT r.*, ui.is_equipped, ui.acquired_at
        FROM user_inventory ui
        JOIN rewards r ON ui.reward_id = r.id
        WHERE ui.user_id = ?
        ORDER BY ui.acquired_at DESC
    """, (user['id'],))
    inventory = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template('profile.html',
                           user=user,
                           aggregate=aggregate,
                           streak=streak,
                           game_stats=game_stats,
                           unlocked_achievements=unlocked_achievements,
                           inventory=inventory)

from flask import Blueprint, render_template
from database import get_db, get_current_user, check_achievements

achievements_bp = Blueprint('achievements', __name__)

@achievements_bp.route('/achievements')
def achievements_list():
    user = get_current_user()
    check_achievements(user['id']) # Sync status

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, 
               COALESCE(ua.progress, 0) as user_progress,
               COALESCE(ua.is_unlocked, 0) as is_unlocked,
               ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
        ORDER BY a.id ASC
    """, (user['id'],))

    achievements = []
    unlocked_count = 0
    total_reward_claimed = 0

    for row in cursor.fetchall():
        ach = dict(row)
        pct = min(100, round((ach['user_progress'] / ach['target_value']) * 100, 1)) if ach['target_value'] > 0 else 0
        ach['percent'] = pct
        if ach['is_unlocked']:
            unlocked_count += 1
            total_reward_claimed += ach['reward_coins']
        achievements.append(ach)

    total_count = len(achievements)
    completion_pct = round((unlocked_count / total_count) * 100, 1) if total_count > 0 else 0

    conn.close()

    return render_template('achievements.html',
                           user=user,
                           achievements=achievements,
                           unlocked_count=unlocked_count,
                           total_count=total_count,
                           completion_pct=completion_pct,
                           total_reward_claimed=total_reward_claimed)

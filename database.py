import sqlite3
import os
import json
import random
from datetime import datetime, date, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DB_PATH = os.path.join(DB_DIR, 'gamezone.db')

# 7-Day Daily Reward Schedule
DAILY_REWARD_CALENDAR = {
    1: 20,
    2: 30,
    3: 50,
    4: 75,
    5: 100,
    6: 150,
    7: 300
}

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        avatar TEXT DEFAULT '🎮',
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 100,
        theme TEXT DEFAULT 'dark',
        sound_enabled INTEGER DEFAULT 1,
        music_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        category TEXT NOT NULL,
        instructions TEXT NOT NULL,
        color TEXT DEFAULT '#6366f1'
    );

    CREATE TABLE IF NOT EXISTS game_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        high_score INTEGER DEFAULT 0,
        times_played INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, game_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS game_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        coins_earned INTEGER DEFAULT 0,
        xp_earned INTEGER DEFAULT 0,
        metadata TEXT DEFAULT '{}',
        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        category TEXT NOT NULL,
        target_value INTEGER NOT NULL,
        reward_coins INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id INTEGER NOT NULL,
        progress INTEGER DEFAULT 0,
        is_unlocked INTEGER DEFAULT 0,
        unlocked_at TIMESTAMP,
        UNIQUE(user_id, achievement_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (achievement_id) REFERENCES achievements (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        cost INTEGER NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        preview_color TEXT DEFAULT '#6366f1',
        game_slug TEXT DEFAULT NULL
    );

    CREATE TABLE IF NOT EXISTS user_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reward_id INTEGER NOT NULL,
        is_equipped INTEGER DEFAULT 0,
        acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, reward_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (reward_id) REFERENCES rewards (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS coin_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS daily_streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        current_streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        last_login_date TEXT,
        last_claimed_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS leaderboard_players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        avatar TEXT NOT NULL,
        game_slug TEXT NOT NULL,
        score INTEGER NOT NULL,
        level INTEGER NOT NULL,
        timeframe TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_favorites (
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, game_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_date TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        game_slug TEXT NOT NULL,
        target_metric TEXT NOT NULL,
        target_value INTEGER NOT NULL,
        reward_xp INTEGER DEFAULT 100,
        reward_coins INTEGER DEFAULT 50
    );

    CREATE TABLE IF NOT EXISTS user_daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        progress INTEGER DEFAULT 0,
        is_completed INTEGER DEFAULT 0,
        is_claimed INTEGER DEFAULT 0,
        claimed_at TIMESTAMP,
        UNIQUE(user_id, challenge_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (challenge_id) REFERENCES daily_challenges (id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_game_scores_user ON game_scores(user_id);
    CREATE INDEX IF NOT EXISTS idx_game_scores_game ON game_scores(game_id);
    CREATE INDEX IF NOT EXISTS idx_history_user ON game_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_history_game ON game_history(game_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_user ON coin_transactions(user_id);
    CREATE INDEX IF NOT EXISTS idx_favorites_user ON user_favorites(user_id);
    CREATE INDEX IF NOT EXISTS idx_challenges_date ON daily_challenges(challenge_date);
    ''')
    conn.commit()
    conn.close()

def xp_for_level(level):
    """XP threshold required to complete a given level: 100 * level^1.5"""
    return int(100 * (level ** 1.5))

def total_xp_for_level(target_level):
    """Total cumulative XP required to reach target_level from Level 1"""
    total = 0
    for lvl in range(1, target_level):
        total += xp_for_level(lvl)
    return total

def calculate_level_from_xp(total_xp):
    """Returns (current_level, current_level_xp, xp_needed_for_next_level, progress_percent)"""
    level = 1
    remaining_xp = total_xp
    while True:
        req = xp_for_level(level)
        if remaining_xp >= req:
            remaining_xp -= req
            level += 1
        else:
            break
    needed = xp_for_level(level)
    pct = round((remaining_xp / needed) * 100, 1) if needed > 0 else 100
    return level, remaining_xp, needed, pct

def get_current_user(user_id=1):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
    user = dict(user)
    level, cur_xp, next_xp, pct = calculate_level_from_xp(user['xp'])
    user['level'] = level
    user['cur_level_xp'] = cur_xp
    user['next_level_xp'] = next_xp
    user['xp_percent'] = pct
    conn.close()
    return user

def add_coin_transaction(conn, user_id, amount, reason):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                   (user_id, amount, reason))

def add_xp_and_coins(user_id, xp_gained, coins_gained, reason):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    old_xp = row['xp']
    new_xp = old_xp + xp_gained
    old_level, _, _, _ = calculate_level_from_xp(old_xp)
    new_level, cur_xp, needed_xp, pct = calculate_level_from_xp(new_xp)
    
    leveled_up = new_level > old_level
    bonus_coins = 0
    if leveled_up:
        for lvl in range(old_level + 1, new_level + 1):
            bonus_coins += lvl * 50

    total_coins_to_add = coins_gained + bonus_coins
    cursor.execute("UPDATE users SET xp = ?, level = ? WHERE id = ?", (new_xp, new_level, user_id))
    if total_coins_to_add > 0:
        cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (total_coins_to_add, user_id))
        cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                       (user_id, coins_gained, reason))
        if bonus_coins > 0:
            cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                           (user_id, bonus_coins, f"🎉 Level Up Bonus! Reached Level {new_level}"))

    conn.commit()
    conn.close()

    return {
        'old_level': old_level,
        'new_level': new_level,
        'leveled_up': leveled_up,
        'bonus_coins': bonus_coins,
        'total_coins_gained': total_coins_to_add,
        'current_xp': cur_xp,
        'needed_xp': needed_xp,
        'xp_percent': pct
    }

def get_streak_info(user_id=1):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    today_str = date.today().isoformat()

    if not streak_row:
        cursor.execute("INSERT INTO daily_streaks (user_id, current_streak, longest_streak, last_login_date, last_claimed_date) VALUES (?, 0, 0, ?, NULL)",
                       (user_id, today_str))
        conn.commit()
        cursor.execute("SELECT * FROM daily_streaks WHERE user_id = ?", (user_id,))
        streak_row = cursor.fetchone()

    streak = dict(streak_row)
    can_claim = (streak['last_claimed_date'] != today_str)

    current = streak['current_streak']
    milestones = [3, 7, 14, 30]
    next_milestone = 3
    for m in milestones:
        if current < m:
            next_milestone = m
            break
        elif m == 30:
            next_milestone = 30 + (current // 30) * 30

    streak['can_claim'] = can_claim
    streak['next_milestone'] = next_milestone
    conn.close()
    return streak

def get_daily_reward_calendar(user_id=1):
    """
    Returns 7-day reward calendar with status for each day:
    Day 1 -> 20, Day 2 -> 30, Day 3 -> 50, Day 4 -> 75,
    Day 5 -> 100, Day 6 -> 150, Day 7 -> 300
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    current_streak = streak_row['current_streak'] if streak_row else 0
    last_claimed = streak_row['last_claimed_date'] if streak_row else None
    already_claimed_today = (last_claimed == today_str)

    # Calculate active cycle day (1 to 7)
    if already_claimed_today:
        day_in_cycle = ((current_streak - 1) % 7) + 1
        claimable_day = None
    else:
        if last_claimed == yesterday_str:
            day_in_cycle = (current_streak % 7) + 1
        else:
            # Streak resets
            day_in_cycle = 1
        claimable_day = day_in_cycle

    calendar = []
    for day_num in range(1, 8):
        coins = DAILY_REWARD_CALENDAR[day_num]
        if already_claimed_today:
            if day_num <= day_in_cycle:
                status = 'claimed'
            elif day_num == day_in_cycle + 1:
                status = 'next'
            else:
                status = 'locked'
        else:
            if day_num < day_in_cycle:
                status = 'claimed'
            elif day_num == day_in_cycle:
                status = 'ready'
            else:
                status = 'locked'

        calendar.append({
            'day': day_num,
            'coins': coins,
            'status': status
        })

    conn.close()
    return {
        'current_streak': current_streak,
        'already_claimed_today': already_claimed_today,
        'current_day_in_cycle': day_in_cycle,
        'claimable_day': claimable_day,
        'next_reward_coins': DAILY_REWARD_CALENDAR.get(claimable_day or (((day_in_cycle) % 7) + 1)),
        'calendar': calendar
    }

def claim_daily_reward(user_id=1):
    """
    Claims the daily streak reward according to the 7-day calendar.
    Day 1: 20, Day 2: 30, Day 3: 50, Day 4: 75, Day 5: 100, Day 6: 150, Day 7: 300 coins.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    today = date.today()
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    if not streak_row:
        conn.close()
        return {'success': False, 'message': 'Streak record not found'}

    streak = dict(streak_row)
    if streak['last_claimed_date'] == today_str:
        conn.close()
        return {'success': False, 'message': 'Already claimed today! Return tomorrow.'}

    # Determine streak continuation
    if streak['last_claimed_date'] == yesterday_str:
        new_streak = streak['current_streak'] + 1
    elif streak['last_claimed_date'] is None:
        new_streak = 1
    else:
        new_streak = 1

    longest = max(streak['longest_streak'], new_streak)
    
    # 7-day cyclic reward calculation
    day_in_cycle = ((new_streak - 1) % 7) + 1
    total_coins = DAILY_REWARD_CALENDAR.get(day_in_cycle, 20)
    milestone_text = f"Day {day_in_cycle} of 7 Calendar Reward! (+{total_coins} 🪙)"

    cursor.execute("""
        UPDATE daily_streaks 
        SET current_streak = ?, longest_streak = ?, last_login_date = ?, last_claimed_date = ? 
        WHERE user_id = ?
    """, (new_streak, longest, today_str, today_str, user_id))

    cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (total_coins, user_id))
    cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                   (user_id, total_coins, f"Daily Reward - Day {day_in_cycle} ({new_streak}-day streak)"))

    conn.commit()
    conn.close()

    # Check streak achievements
    new_unlocked = check_achievements(user_id)

    return {
        'success': True,
        'new_streak': new_streak,
        'day_in_cycle': day_in_cycle,
        'coins_awarded': total_coins,
        'milestone_text': milestone_text,
        'unlocked_achievements': new_unlocked
    }

# =========================================================================
# DAILY CHALLENGES
# =========================================================================

CHALLENGE_POOL = [
    {
        'title': '🏃 Marathon Kickoff',
        'description': 'Run 1,000 meters in Endless Runner',
        'icon': '🏃',
        'game_slug': 'endless_runner',
        'target_metric': 'distance',
        'target_value': 1000,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🎯 Precision Deadeye',
        'description': 'Hit 30 targets in Target Shooter',
        'icon': '🎯',
        'game_slug': 'target_shooter',
        'target_metric': 'hits',
        'target_value': 30,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🐍 Serpent Master',
        'description': 'Score 500+ points in Snake',
        'icon': '🐍',
        'game_slug': 'snake',
        'target_metric': 'score',
        'target_value': 500,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🧱 Demolition Expert',
        'description': 'Score 400+ points in Brick Breaker',
        'icon': '🧱',
        'game_slug': 'brick_breaker',
        'target_metric': 'score',
        'target_value': 400,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🚀 Armada Buster',
        'description': 'Score 800+ in Space Shooter',
        'icon': '🚀',
        'game_slug': 'space_shooter',
        'target_metric': 'score',
        'target_value': 800,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🎈 Balloon Fiesta',
        'description': 'Pop 35 balloons in Balloon Pop',
        'icon': '🎈',
        'game_slug': 'balloon_pop',
        'target_metric': 'score',
        'target_value': 35,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🏎️ Highway Speeder',
        'description': 'Drive 1,200 meters in Traffic Racer',
        'icon': '🏎️',
        'game_slug': 'traffic_racer',
        'target_metric': 'distance',
        'target_value': 1200,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🧟 Zombie Slayer',
        'description': 'Survive 3 waves in Zombie Survival',
        'icon': '🧟',
        'game_slug': 'zombie_survival',
        'target_metric': 'wave',
        'target_value': 3,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🪙 Coin Vault Raider',
        'description': 'Collect 50 coins in Coin Collector',
        'icon': '🪙',
        'game_slug': 'coin_collector',
        'target_metric': 'coins_collected',
        'target_value': 50,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🧱 Quantum Combiner',
        'description': 'Reach 512 score or tile in 2048',
        'icon': '🧱',
        'game_slug': 'game_2048',
        'target_metric': 'score',
        'target_value': 512,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '🔤 Word Anagram Champion',
        'description': 'Unscramble 4 words in Word Scramble',
        'icon': '🔤',
        'game_slug': 'word_scramble',
        'target_metric': 'solved',
        'target_value': 4,
        'reward_xp': 100,
        'reward_coins': 50
    },
    {
        'title': '⚡ Lightning Reflexes',
        'description': 'Score in Reaction Test under 350ms',
        'icon': '⚡',
        'game_slug': 'reaction_test',
        'target_metric': 'reaction_score',
        'target_value': 300,
        'reward_xp': 100,
        'reward_coins': 50
    }
]

def ensure_daily_challenges(today_str=None):
    """Ensures 3 daily challenges are seeded for today."""
    if today_str is None:
        today_str = date.today().isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM daily_challenges WHERE challenge_date = ?", (today_str,))
    if cursor.fetchone()['cnt'] == 0:
        # Deterministically select 3 challenges based on the day string
        seed_val = sum(ord(c) for c in today_str)
        rng = random.Random(seed_val)
        selected = rng.sample(CHALLENGE_POOL, 3)

        for ch in selected:
            cursor.execute("""
                INSERT INTO daily_challenges (challenge_date, title, description, icon, game_slug, target_metric, target_value, reward_xp, reward_coins)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (today_str, ch['title'], ch['description'], ch['icon'], ch['game_slug'], ch['target_metric'], ch['target_value'], ch['reward_xp'], ch['reward_coins']))
        conn.commit()
    conn.close()

def get_user_daily_challenges(user_id=1):
    """Returns today's 3 daily challenges with user progress and claim status."""
    today_str = date.today().isoformat()
    ensure_daily_challenges(today_str)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dc.*, 
               COALESCE(udc.progress, 0) as user_progress,
               COALESCE(udc.is_completed, 0) as is_completed,
               COALESCE(udc.is_claimed, 0) as is_claimed
        FROM daily_challenges dc
        LEFT JOIN user_daily_challenges udc ON dc.id = udc.challenge_id AND udc.user_id = ?
        WHERE dc.challenge_date = ?
        ORDER BY dc.id ASC
    """, (user_id, today_str))

    challenges = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for ch in challenges:
        ch['progress_percent'] = min(100, int((ch['user_progress'] / max(1, ch['target_value'])) * 100))
    return challenges

def claim_daily_challenge(user_id, challenge_id):
    """Claims rewards for a completed daily challenge (+100 XP, +50 Coins)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dc.*, udc.is_completed, udc.is_claimed
        FROM daily_challenges dc
        JOIN user_daily_challenges udc ON dc.id = udc.challenge_id
        WHERE udc.user_id = ? AND dc.id = ?
    """, (user_id, challenge_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {'success': False, 'message': 'Challenge not found or progress not started'}

    ch = dict(row)
    if not ch['is_completed']:
        conn.close()
        return {'success': False, 'message': 'Challenge is not yet completed!'}

    if ch['is_claimed']:
        conn.close()
        return {'success': False, 'message': 'Challenge reward already claimed!'}

    # Mark claimed
    cursor.execute("""
        UPDATE user_daily_challenges 
        SET is_claimed = 1, claimed_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND challenge_id = ?
    """, (user_id, challenge_id))

    reward_xp = ch['reward_xp'] or 100
    reward_coins = ch['reward_coins'] or 50

    conn.commit()
    conn.close()

    progression = add_xp_and_coins(user_id, reward_xp, reward_coins, f"Daily Challenge Reward: {ch['title']}")

    return {
        'success': True,
        'message': f"Claimed +{reward_xp} XP & +{reward_coins} GameCoins!",
        'reward_xp': reward_xp,
        'reward_coins': reward_coins,
        'progression': progression
    }

# =========================================================================
# FAVORITES SYSTEM
# =========================================================================

def toggle_favorite(user_id, game_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_favorites WHERE user_id = ? AND game_id = ?", (user_id, game_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM user_favorites WHERE user_id = ? AND game_id = ?", (user_id, game_id))
        is_fav = False
    else:
        cursor.execute("INSERT INTO user_favorites (user_id, game_id) VALUES (?, ?)", (user_id, game_id))
        is_fav = True

    conn.commit()
    conn.close()
    return is_fav

def get_user_favorite_ids(user_id=1):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT game_id FROM user_favorites WHERE user_id = ?", (user_id,))
    fav_ids = set(row['game_id'] for row in cursor.fetchall())
    conn.close()
    return fav_ids

# =========================================================================
# SUBMIT GAME SCORE & UNIFIED REWARD MECHANISM
# =========================================================================

def submit_game_score(user_id, game_slug, raw_score, metadata=None):
    """
    Validates score, awards XP and coins, logs history, updates high score,
    progresses daily challenges, and checks achievements.
    """
    if metadata is None:
        metadata = {}

    score = int(max(0, raw_score))
    conn = get_db()
    cursor = conn.cursor()

    # Fetch game
    cursor.execute("SELECT * FROM games WHERE slug = ?", (game_slug,))
    game = cursor.fetchone()
    if not game:
        conn.close()
        return {'success': False, 'message': 'Invalid game'}

    game_id = game['id']

    # Server-side calculation of XP and Coins based on game and score
    # Every completed game gets base 20 XP + 10 Coins, plus scaling based on performance
    base_xp = 20
    base_coins = 10
    
    score_factor = 0
    if game_slug == 'snake':
        score_factor = min(score // 20, 100)
    elif game_slug in ('quiz', 'number_challenge'):
        score_factor = min(score // 10, 120)
    elif game_slug == 'memory':
        score_factor = min(score // 10, 80)
    elif game_slug == 'brick_breaker':
        score_factor = min(score // 50, 150)
    elif game_slug in ('space_shooter', 'space_invaders', 'zombie_survival'):
        score_factor = min(score // 40, 200)
    elif game_slug in ('racing', 'traffic_racer', 'f1_sprint', 'bike_racer'):
        score_factor = min(score // 30, 150)
    elif game_slug in ('aim_trainer', 'target_shooter', 'balloon_pop'):
        score_factor = min(score // 20, 120)
    elif game_slug == 'endless_runner':
        score_factor = min(score // 25, 160)
    elif game_slug == 'game_2048':
        score_factor = min(score // 30, 150)
    elif game_slug in ('sudoku', 'word_scramble'):
        score_factor = min(score // 15, 100)
    elif game_slug in ('tic_tac_toe', 'reaction_test', 'coin_collector'):
        score_factor = min(score // 15, 100)
    else:
        score_factor = min(score // 30, 100)

    xp_earned = base_xp + int(score_factor * 1.2)
    coins_earned = base_coins + int(score_factor * 0.8)

    # Insert game history
    cursor.execute("""
        INSERT INTO game_history (user_id, game_id, score, coins_earned, xp_earned, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, game_id, score, coins_earned, xp_earned, json.dumps(metadata)))

    # Fetch or insert game score
    cursor.execute("SELECT * FROM game_scores WHERE user_id = ? AND game_id = ?", (user_id, game_id))
    score_row = cursor.fetchone()
    is_new_high_score = False
    prev_high_score = 0

    if not score_row:
        cursor.execute("""
            INSERT INTO game_scores (user_id, game_id, high_score, times_played)
            VALUES (?, ?, ?, 1)
        """, (user_id, game_id, score))
        is_new_high_score = (score > 0)
    else:
        prev_high_score = score_row['high_score']
        times_played = score_row['times_played'] + 1
        if score > prev_high_score:
            is_new_high_score = True
            cursor.execute("""
                UPDATE game_scores 
                SET high_score = ?, times_played = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (score, times_played, score_row['id']))
        else:
            cursor.execute("""
                UPDATE game_scores 
                SET times_played = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (times_played, score_row['id']))

    conn.commit()

    # Progress Daily Challenges for this game
    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT * FROM daily_challenges WHERE challenge_date = ? AND game_slug = ?
    """, (today_str, game_slug))
    active_challenges = cursor.fetchall()

    for ch in active_challenges:
        ch_id = ch['id']
        metric = ch['target_metric']
        target = ch['target_value']
        
        val = score
        if metric in metadata:
            try:
                val = int(metadata[metric])
            except Exception:
                val = score

        # Check existing user progress
        cursor.execute("SELECT * FROM user_daily_challenges WHERE user_id = ? AND challenge_id = ?", (user_id, ch_id))
        user_ch = cursor.fetchone()

        if not user_ch:
            new_prog = val
            completed = 1 if new_prog >= target else 0
            cursor.execute("""
                INSERT INTO user_daily_challenges (user_id, challenge_id, progress, is_completed, is_claimed)
                VALUES (?, ?, ?, ?, 0)
            """, (user_id, ch_id, new_prog, completed))
        else:
            old_prog = user_ch['progress']
            # If target metric is score/distance, take maximum or accumulate
            if metric in ('score', 'distance', 'reaction_score'):
                new_prog = max(old_prog, val)
            else:
                new_prog = old_prog + val

            completed = 1 if new_prog >= target else user_ch['is_completed']
            cursor.execute("""
                UPDATE user_daily_challenges 
                SET progress = ?, is_completed = ?
                WHERE user_id = ? AND challenge_id = ?
            """, (new_prog, completed, user_id, ch_id))

    conn.commit()
    conn.close()

    # Award XP and coins through the centralized method
    progression = add_xp_and_coins(user_id, xp_earned, coins_earned, f"Played {game['title']} (Score: {score})")

    # Check achievements
    unlocked_achievements = check_achievements(user_id)

    return {
        'success': True,
        'game_title': game['title'],
        'score': score,
        'is_new_high_score': is_new_high_score,
        'prev_high_score': prev_high_score,
        'coins_earned': coins_earned,
        'xp_earned': xp_earned,
        'progression': progression,
        'unlocked_achievements': unlocked_achievements
    }

# =========================================================================
# DETAILED GAME STATISTICS FOR PROFILE
# =========================================================================

def get_detailed_game_stats(user_id=1):
    """
    Returns per-game statistics tracking:
    - Games played
    - Best score
    - Total score
    - Highest level
    - Total coins earned
    - Last played
    - Average score
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.*, 
               COALESCE(gs.high_score, 0) as high_score,
               COALESCE(gs.times_played, 0) as times_played,
               gs.updated_at as last_played,
               COALESCE(stat.total_score, 0) as total_score,
               COALESCE(stat.avg_score, 0) as avg_score,
               COALESCE(stat.total_coins, 0) as total_coins_earned,
               COALESCE(stat.max_level, 1) as highest_level
        FROM games g
        LEFT JOIN game_scores gs ON g.id = gs.game_id AND gs.user_id = ?
        LEFT JOIN (
            SELECT game_id, 
                   SUM(score) as total_score,
                   ROUND(AVG(score)) as avg_score,
                   SUM(coins_earned) as total_coins,
                   MAX(COALESCE(json_extract(metadata, '$.level'), 1)) as max_level
            FROM game_history
            WHERE user_id = ?
            GROUP BY game_id
        ) stat ON g.id = stat.game_id
        ORDER BY g.category ASC, g.id ASC
    """, (user_id, user_id))

    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stats

# =========================================================================
# ACHIEVEMENTS SYSTEM
# =========================================================================

def check_achievements(user_id=1):
    """Evaluates all achievement criteria and unlocks those met, giving coin rewards."""
    conn = get_db()
    cursor = conn.cursor()

    # Get user statistics
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())

    cursor.execute("SELECT COUNT(*) as games_count, MAX(score) as max_score FROM game_history WHERE user_id = ?", (user_id,))
    history_stat = dict(cursor.fetchone())
    total_games = history_stat['games_count'] or 0

    cursor.execute("SELECT current_streak, longest_streak FROM daily_streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    streak = streak_row['current_streak'] if streak_row else 0

    # Get game-specific stats
    cursor.execute("""
        SELECT g.slug, g.category, gs.high_score, gs.times_played 
        FROM game_scores gs
        JOIN games g ON gs.game_id = g.id
        WHERE gs.user_id = ?
    """, (user_id,))
    game_scores = {row['slug']: dict(row) for row in cursor.fetchall()}

    # Count distinct games played
    cursor.execute("SELECT COUNT(DISTINCT game_id) as distinct_games FROM game_scores WHERE user_id = ? AND times_played > 0", (user_id,))
    distinct_games = cursor.fetchone()['distinct_games'] or 0

    # Total distance run in endless runner
    cursor.execute("""
        SELECT COALESCE(SUM(score), 0) as total_distance
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ? AND g.slug = 'endless_runner'
    """, (user_id,))
    runner_meters = cursor.fetchone()['total_distance'] or 0

    # Total targets hit across target shooter & aim trainer
    cursor.execute("""
        SELECT COALESCE(SUM(score), 0) as total_targets
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ? AND g.slug IN ('target_shooter', 'aim_trainer')
    """, (user_id,))
    targets_hit = cursor.fetchone()['total_targets'] or 0

    # Total space enemies destroyed
    cursor.execute("""
        SELECT COALESCE(SUM(score), 0) as space_kills
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ? AND g.slug IN ('space_shooter', 'space_invaders')
    """, (user_id,))
    space_kills = cursor.fetchone()['space_kills'] or 0

    # Completed puzzle games
    cursor.execute("""
        SELECT COUNT(*) as puzzle_matches
        FROM game_history gh
        JOIN games g ON gh.game_id = g.id
        WHERE gh.user_id = ? AND g.category = 'Brain & Puzzle'
    """, (user_id,))
    puzzle_count = cursor.fetchone()['puzzle_matches'] or 0

    # Fetch all achievements
    cursor.execute("""
        SELECT a.*, ua.is_unlocked, ua.progress 
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
    """, (user_id,))
    achievements = cursor.fetchall()

    newly_unlocked = []

    for ach in achievements:
        ach_id = ach['id']
        slug = ach['slug']
        target = ach['target_value']
        already_unlocked = bool(ach['is_unlocked'])
        current_progress = 0

        if slug == 'first_game':
            current_progress = total_games
        elif slug in ('on_fire', 'gaming_streak_7'):
            current_progress = streak
        elif slug == 'marathon_runner':
            current_progress = runner_meters
        elif slug in ('sharpshooter', 'sharpshooter_pro'):
            current_progress = targets_hit
        elif slug == 'space_commander':
            current_progress = space_kills
        elif slug in ('speed_demon', 'speed_demon_pro'):
            current_progress = max(
                game_scores.get('racing', {}).get('high_score', 0),
                game_scores.get('traffic_racer', {}).get('high_score', 0),
                game_scores.get('f1_sprint', {}).get('high_score', 0),
                game_scores.get('bike_racer', {}).get('high_score', 0)
            )
        elif slug == 'all_rounder':
            current_progress = distinct_games
        elif slug == 'game_collector':
            current_progress = distinct_games
        elif slug == 'puzzle_master':
            current_progress = puzzle_count
        elif slug in ('coin_hoarder', 'coin_hunter_10k'):
            current_progress = user['coins']
        elif slug == 'snake_master':
            current_progress = game_scores.get('snake', {}).get('high_score', 0)
        elif slug == 'genius':
            current_progress = game_scores.get('quiz', {}).get('high_score', 0)
        elif slug == 'space_pilot':
            current_progress = game_scores.get('space_shooter', {}).get('high_score', 0)
        elif slug == 'brick_destroyer':
            current_progress = game_scores.get('brick_breaker', {}).get('high_score', 0)
        elif slug == 'math_wizard':
            current_progress = game_scores.get('number_challenge', {}).get('high_score', 0)
        elif slug == 'champion':
            current_progress = user['level']
        elif slug == 'collector':
            cursor.execute("SELECT COUNT(*) as cnt FROM user_inventory WHERE user_id = ?", (user_id,))
            current_progress = cursor.fetchone()['cnt']

        is_now_unlocked = (current_progress >= target)

        if not already_unlocked and is_now_unlocked:
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, progress, is_unlocked, unlocked_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, achievement_id) DO UPDATE SET 
                    progress = excluded.progress,
                    is_unlocked = 1,
                    unlocked_at = CURRENT_TIMESTAMP
            """, (user_id, ach_id, current_progress))

            reward = ach['reward_coins']
            cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (reward, user_id))
            cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                           (user_id, reward, f"🏆 Achievement Unlocked: {ach['title']}"))

            newly_unlocked.append({
                'id': ach_id,
                'title': ach['title'],
                'description': ach['description'],
                'icon': ach['icon'],
                'reward_coins': reward
            })
        else:
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, progress, is_unlocked)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(user_id, achievement_id) DO UPDATE SET 
                    progress = excluded.progress
            """, (user_id, ach_id, current_progress))

    conn.commit()
    conn.close()
    return newly_unlocked

def purchase_reward(user_id, reward_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return {'success': False, 'message': 'User not found'}

    cursor.execute("SELECT * FROM rewards WHERE id = ?", (reward_id,))
    reward = cursor.fetchone()
    if not reward:
        conn.close()
        return {'success': False, 'message': 'Reward item not found'}

    cursor.execute("SELECT * FROM user_inventory WHERE user_id = ? AND reward_id = ?", (user_id, reward_id))
    if cursor.fetchone():
        conn.close()
        return {'success': False, 'message': 'You already own this item!'}

    cost = reward['cost']
    if user['coins'] < cost:
        conn.close()
        return {'success': False, 'message': f'Not enough GameCoins! (Need {cost} 🪙, you have {user["coins"]} 🪙)'}

    cursor.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, ?, ?)",
                   (user_id, -cost, f"Purchased {reward['name']}"))
    cursor.execute("INSERT INTO user_inventory (user_id, reward_id, is_equipped) VALUES (?, ?, 0)",
                   (user_id, reward_id))

    conn.commit()
    conn.close()

    check_achievements(user_id)

    return {'success': True, 'message': f'Successfully acquired {reward["name"]}!'}

def equip_reward(user_id, reward_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ui.*, r.type, r.slug, r.name, r.icon
        FROM user_inventory ui
        JOIN rewards r ON ui.reward_id = r.id
        WHERE ui.user_id = ? AND ui.reward_id = ?
    """, (user_id, reward_id))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return {'success': False, 'message': 'You do not own this item'}

    item_type = item['type']

    cursor.execute("""
        UPDATE user_inventory 
        SET is_equipped = 0 
        WHERE user_id = ? AND reward_id IN (SELECT id FROM rewards WHERE type = ?)
    """, (user_id, item_type))

    cursor.execute("UPDATE user_inventory SET is_equipped = 1 WHERE user_id = ? AND reward_id = ?",
                   (user_id, reward_id))

    if item_type == 'avatar':
        cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (item['icon'], user_id))
    elif item_type == 'theme':
        cursor.execute("UPDATE users SET theme = ? WHERE id = ?", (item['slug'], user_id))

    conn.commit()
    conn.close()

    return {'success': True, 'message': f'Equipped {item["name"]}!'}

def reset_user_progress(user_id=1):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users 
        SET level = 1, xp = 0, coins = 100, theme = 'dark', avatar = '🎮' 
        WHERE id = ?
    """, (user_id,))

    cursor.execute("DELETE FROM game_history WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM game_scores WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_achievements WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_inventory WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM coin_transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_favorites WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_daily_challenges WHERE user_id = ?", (user_id,))
    cursor.execute("""
        UPDATE daily_streaks 
        SET current_streak = 0, longest_streak = 0, last_claimed_date = NULL 
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("INSERT INTO coin_transactions (user_id, amount, reason) VALUES (?, 100, 'GameZone Welcome Bonus (Progress Reset)')", (user_id,))

    conn.commit()
    conn.close()
    return True

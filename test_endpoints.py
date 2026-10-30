import requests
import json
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:5000'

def test_all():
    session = requests.Session()

    print("[1] Testing Page Routes...")
    pages = [
        '/',
        '/games',
        '/leaderboard',
        '/rewards',
        '/achievements',
        '/profile',
        '/history',
        '/settings',
        '/games/snake',
        '/games/quiz',
        '/games/memory',
        '/games/brick_breaker',
        '/games/space_shooter',
        '/games/racing',
        '/games/aim_trainer',
        '/games/number_challenge'
    ]

    for p in pages:
        r = session.get(f"{BASE_URL}{p}")
        assert r.status_code == 200, f"Failed GET {p}: status {r.status_code}"
        print(f"  OK: {p}")

    print("\n[2] Testing API Claim Daily...")
    r = session.post(f"{BASE_URL}/api/claim-daily")
    assert r.status_code == 200
    data = r.json()
    print(f"  Daily claim response: success={data.get('success')}, coins={data.get('coins_awarded')}, streak={data.get('new_streak')}")

    print("\n[3] Testing API Submit Score for All 8 Games...")
    scores = [
        ('snake', 250, {'reason': 'wall'}),
        ('quiz', 900, {'accuracy': 90}),
        ('memory', 450, {'moves': 12}),
        ('brick_breaker', 520, {'level': 2}),
        ('space_shooter', 1100, {'wave': 4}),
        ('racing', 750, {'distance_km': 7.5}),
        ('aim_trainer', 420, {'accuracy': 95}),
        ('number_challenge', 550, {'streak': 8})
    ]

    for slug, sc, meta in scores:
        r = session.post(f"{BASE_URL}/api/submit-score", json={'game_slug': slug, 'score': sc, 'metadata': meta})
        assert r.status_code == 200, f"Submit score failed for {slug}"
        resp = r.json()
        assert resp.get('success') == True
        coins = resp.get('coins_earned')
        xp = resp.get('xp_earned')
        new_high = resp.get('is_new_high_score')
        achs = [a['title'] for a in resp.get('unlocked_achievements', [])]
        print(f"  OK {slug}: Score={sc}, +{coins} Coins, +{xp} XP, NewHigh={new_high}, AchievementsUnlocked={achs}")

    print("\n[4] Testing User Stats...")
    r = session.get(f"{BASE_URL}/api/user-stats")
    assert r.status_code == 200
    user = r.json().get('user')
    print(f"  User Level: {user['level']}, XP: {user['xp']}, Coins: {user['coins']}")

    print("\n[5] Testing Rewards Purchase & Equip...")
    # Find a reward item
    r = session.get(f"{BASE_URL}/rewards")
    # Purchase item with id 5 (avatar-ninja, cost 100) or theme
    r = session.post(f"{BASE_URL}/api/purchase-reward", json={'reward_id': 5})
    p_data = r.json()
    print(f"  Purchase result: {p_data}")

    r = session.post(f"{BASE_URL}/api/equip-reward", json={'reward_id': 5})
    e_data = r.json()
    print(f"  Equip result: {e_data}")

    print("\n[6] Testing Settings Update...")
    r = session.post(f"{BASE_URL}/api/update-settings", json={
        'username': 'NeonPlayer007',
        'avatar': '⚡',
        'theme': 'cyberpunk',
        'sound_enabled': True
    })
    assert r.status_code == 200
    print(f"  Settings update: {r.json()}")

    print("\n[7] Testing User Profile & History reflect changes...")
    r = session.get(f"{BASE_URL}/profile")
    assert r.status_code == 200
    assert 'NeonPlayer007' in r.text

    r = session.get(f"{BASE_URL}/history")
    assert r.status_code == 200
    assert 'Snake' in r.text

    print("\nALL BACKEND AND API TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_all()

# 🎮 GameZone — Play • Earn • Compete

> A modern, responsive, cyber-arcade Mini Game Hub built with **Flask**, **SQLite**, **HTML5 Canvas**, and **Vanilla JavaScript**. Play games, earn virtual GameCoins, level up, unlock achievements, maintain daily login streaks, and compete on leaderboards!

---

## 🚀 Key Highlights
- **100% Free & Local**: Zero paid APIs, no OpenAI/AI keys, no external database servers required.
- **8 Fully Playable Games**:
  1. 🐍 **Snake**: Classic grid arcade with speed ramp, particle trails, and skin customization.
  2. 🧠 **Quiz Master**: Multi-category trivia (Science, Tech, GK, History, Sports, Math) with a 15-second countdown timer.
  3. 🧩 **Memory Match**: Card matching with 3D flip animation across Easy, Medium, and Hard tiers.
  4. 🧱 **Brick Breaker**: Neon breakout with angled ball physics, brick HP, lives, and levels.
  5. 🚀 **Space Shooter**: 2D arcade shooter with enemy swarms, plasma lasers, starfield parallax, and waves.
  6. 🏎️ **Mini Racing**: 3-lane top-down highway arcade racer with traffic dodging, speed ramp, and coin pickups.
  7. 🎯 **Aim Trainer**: 30-second reflex challenge tracking target hits, misses, accuracy %, and reaction time (ms).
  8. 🔢 **Number Challenge**: Mental math speed challenge covering arithmetic, percentages, and algebra with combo multipliers.
- **Progression & Economy**:
  - **GameCoins 🪙**: Earned by playing games and maintaining streaks; trackable in a complete ledger.
  - **Level & XP System ⭐**: Every match awards XP; level-ups award coin bonuses and trigger animated modals.
  - **Daily Streaks 🔥**: Claim daily rewards with milestone bonuses at 3, 7, 14, and 30 days.
  - **Achievements Engine 🏅**: Milestone badges and coin bonuses for high scores, shop purchases, and streaks.
  - **Rewards Shop 🎁**: Spend GameCoins to acquire and equip custom Themes, Avatars, Game Skins, and Effects.
  - **Competitive Leaderboard 🏆**: Global, Weekly, and Daily rankings with top-3 podium and user highlighting.
  - **Web Audio Synthesizer 🔊**: Pure JavaScript audio synthesizer using the Web Audio API for arcade sound FX without external MP3 files.
  - **Mobile Touch Controls 📱**: Virtual on-screen D-Pad and action buttons for touchscreens.

---

## 📋 1. Requirements
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Any modern web browser (Google Chrome, Microsoft Edge, Firefox, Safari, Brave)
- Windows / macOS / Linux

---

## 🐍 2. Python Installation
If you do not have Python installed:
1. Download Python from [python.org](https://www.python.org/downloads/).
2. On Windows, make sure to check **"Add Python to PATH"** during installation.

---

## 📦 3. Installing Dependencies
Open PowerShell or your command prompt in the project root directory and run:

```bash
pip install -r requirements.txt
```

*(Note: The only backend dependency is Flask)*

---

## ▶️ 4. Running the Application
Launch GameZone with a single command:

```bash
python app.py
```

The database (`database/gamezone.db`) will auto-initialize, apply schema migrations, and generate seed data on the first run.

---

## 🌐 5. Opening in the Browser
Once running, open your web browser and navigate to:

```
http://127.0.0.1:5000
```

---

## 📁 6. Project Structure
```
GameZone/
│
├── app.py                     # Flask application entry point & blueprint registration
├── database.py                # SQLite connection, schema, progression, validation, queries
├── seed_data.py               # Pre-seeds default player, 8 games, achievements, shop items
├── requirements.txt           # Minimal dependencies
├── README.md                  # Detailed documentation
│
├── database/
│   └── gamezone.db            # Auto-generated SQLite database file
│
├── routes/
│   ├── __init__.py
│   ├── main.py                # Dashboard (/), daily check-in API, quick stats API
│   ├── games.py               # Games catalogue (/games), game player (/games/<id>), score API
│   ├── leaderboard.py         # Leaderboards (/leaderboard) - Global, Weekly, Daily
│   ├── rewards.py             # Rewards shop (/rewards), purchase API, equip API
│   ├── achievements.py        # Achievements list & status (/achievements)
│   ├── profile.py             # Player profile (/profile), game breakdown stats
│   ├── history.py             # Game history (/history) & coin ledger with filters
│   └── settings.py            # Preferences (/settings), avatar/theme update, progress reset
│
├── templates/
│   ├── base.html              # Modern dark layout, navbar, mobile drawer, modals, toasts
│   ├── index.html             # Dashboard with hero, XP progress, streak card, stats
│   ├── games.html             # Full 8-game catalogue with category filters and search
│   ├── game_play.html         # Universal game arena (canvas/touch controls, HUD, pause)
│   ├── leaderboard.html       # Top 3 podium display + ranked table with current user
│   ├── rewards.html           # Virtual shop with themes, skins, avatars, effects
│   ├── achievements.html      # Achievements grid with progress bars and claimable rewards
│   ├── profile.html           # Detailed player dossier, statistics, unlocked inventory
│   ├── history.html           # Filterable game sessions and coin transaction logs
│   └── settings.html          # Profile settings, audio toggles, theme switcher, reset dialog
│
└── static/
    ├── css/
    │   └── style.css          # Cyberpunk dark gaming design system, animations, responsive grid
    └── js/
        ├── sound.js           # Web Audio API sound effect synthesizer
        ├── common.js          # Level-up modal, achievement toast, navbar dynamic stats
        └── games/
            ├── snake.js           # Snake 🐍
            ├── quiz.js            # Quiz Master 🧠
            ├── memory.js          # Memory Match 🧩
            ├── brick_breaker.js   # Brick Breaker 🧱
            ├── space_shooter.js   # Space Shooter 🚀
            ├── racing.js          # Mini Racing 🏎️
            ├── aim_trainer.js     # Aim Trainer 🎯
            └── number_challenge.js# Number Challenge 🔢
```

---

## 🗄️ 7. Database
GameZone uses SQLite. Tables created:
- `users`: Stores username, avatar, level, xp, coins, theme, sound settings.
- `games`: Details for all 8 games (title, description, icon, instructions, theme colors).
- `game_scores`: Personal high scores and times played for each user and game.
- `game_history`: Full audit trail of every played match with score, coins, and XP earned.
- `achievements`: List of all badge goals and coin rewards.
- `user_achievements`: Player progress tracking and unlocked dates.
- `rewards`: Shop catalog items (skins, themes, avatars, effects).
- `user_inventory`: Items owned and equipped by the player.
- `coin_transactions`: Financial ledger tracking every coin credit and debit.
- `daily_streaks`: Tracks consecutive logins, milestones, and last claim dates.
- `leaderboard_players`: Pre-seeded realistic competitors across all timeframes.

---

## 🕹️ 8. How Each Game Works

### 1. Snake 🐍
- **Controls**: Arrow Keys or `W`/`A`/`S`/`D` (or touch D-pad).
- **Rules**: Consume energy orbs to grow longer and score points. Speed increases every 50 points. Avoid hitting the wall or your own body.
- **Reward**: 10 points per food orb.

### 2. Quiz Master 🧠
- **Controls**: Mouse click or touch tap on option buttons `A`, `B`, `C`, or `D`.
- **Rules**: 10 randomized trivia questions per round across Science, Tech, History, GK, Math, and Sports. 15-second countdown per question. Fast answers award speed combo points.
- **Reward**: Base 100 points + speed bonus per correct answer.

### 3. Memory Match 🧩
- **Controls**: Click or tap cards to flip.
- **Rules**: Match all hidden cyber glyph pairs in minimal moves and time. Choose between Easy (6 pairs), Medium (8 pairs), or Hard (12 pairs).
- **Reward**: Points calculated based on pairs matched, remaining time, and move efficiency.

### 4. Brick Breaker 🧱
- **Controls**: Arrow keys `Left`/`Right`, `A`/`D`, mouse drag, or touch buttons.
- **Rules**: Deflect the bouncing kinetic energy ball with your paddle to shatter neon bricks. Upper bricks take 2 hits. Ball reflects with realistic angled physics based on where it strikes the paddle. You have 3 lives.
- **Reward**: 20 points per brick hit + 200 point wave clear bonus.

### 5. Space Shooter 🚀
- **Controls**: Arrow keys / `W`/`A`/`S`/`D` to maneuver ship; `Spacebar` or `K` (or touch button) to fire plasma lasers.
- **Rules**: Shoot down incoming alien fighters and dodge enemy ships. Survive waves as density and speed increase.
- **Reward**: 30 points per destroyed enemy fighter.

### 6. Mini Racing 🏎️
- **Controls**: `Left`/`Right` or `A`/`D` to change lanes; `Up`/`Down` or `W`/`S` to adjust cruise velocity.
- **Rules**: Cruise down the 3-lane neon highway. Dodge enemy cars and pick up yellow GameCoins along the road. Speed increases over distance.
- **Reward**: Points equal distance covered in meters + 50 points per coin pickup.

### 7. Aim Trainer 🎯
- **Controls**: Mouse click or touch tap directly on targets.
- **Rules**: 30-second reflex trial. Bullseye targets spawn and shrink across the canvas. Click them quickly before they vanish.
- **Reward**: Points rewarded for every hit scaled by reaction speed (ms). Final accuracy % and reaction time are recorded.

### 8. Number Challenge 🔢
- **Controls**: Click or tap the correct answer from 4 choices.
- **Rules**: 45-second rapid mental math drill. Generates equations on the fly (addition, subtraction, multiplication, division, percentages, and basic algebra). Correct answers build combo multipliers up to 4x.
- **Reward**: 15 points × multiplier for each correct solution.

---

## 🔄 9. How to Reset the Database
You can reset your player progress at any time:
1. **Via UI**: Navigate to **⚙️ Settings**, locate the **Danger Zone**, click **Reset All Game Progress**, and type `RESET` to confirm.
2. **Via File System**:
   - Stop the Flask server (`Ctrl + C`).
   - Delete the file `database/gamezone.db`.
   - Run `python app.py` — it will automatically re-create and re-seed a brand new database.

---

## 🛠️ 10. Troubleshooting
- **Port 5000 Already in Use**: If another app is using port 5000, change the port in `app.py` (e.g. `app.run(port=5050)`).
- **Sound Not Playing**: Web browsers require a user interaction (such as clicking anywhere on the screen) before audio can play. Ensure sound is not muted in the top navigation bar (🔊 icon).
- **Touch Controls Not Appearing**: Virtual touch controls display automatically on touchscreen devices. You can also resize your browser to mobile width (<768px).

---

## 📜 License
GameZone is open-source and free to play locally. Have fun and enjoy the games!

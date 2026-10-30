/**
 * GameZone Common Application Logic
 * Level-up modal, achievement toast dispatcher, coin animations, touch controls.
 */

window.GameZone = {
    // Current user state cached locally
    user: null,

    // Initialize UI, audio toggles, streak claims, and theme
    init() {
        this.initTheme();
        this.initAudioToggle();
        this.initDailyStreakButton();
    },

    initTheme() {
        const savedTheme = localStorage.getItem('gamezone_theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
    },

    setTheme(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('gamezone_theme', themeName);
    },

    initAudioToggle() {
        const soundBtn = document.getElementById('soundToggleBtn');
        if (!soundBtn) return;

        const updateBtn = (enabled) => {
            soundBtn.innerHTML = enabled ? '🔊' : '🔇';
            soundBtn.title = enabled ? 'Mute Sound' : 'Unmute Sound';
            soundBtn.classList.toggle('muted', !enabled);
        };

        updateBtn(window.soundMgr.enabled);

        soundBtn.addEventListener('click', () => {
            const enabled = window.soundMgr.toggleSound();
            updateBtn(enabled);
            this.showToast('Audio Settings', enabled ? 'Sound effects enabled 🔊' : 'Sound effects muted 🔇', 'info');
        });
    },

    initDailyStreakButton() {
        const claimBtn = document.getElementById('claimStreakBtn');
        if (!claimBtn) return;

        claimBtn.addEventListener('click', async () => {
            claimBtn.disabled = true;
            claimBtn.innerHTML = '<span class="spinner"></span> Claiming...';

            try {
                const res = await fetch('/api/claim-daily', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();

                if (data.success) {
                    window.soundMgr.playCoin();
                    this.showToast('Streak Claimed! 🔥', `+${data.coins_awarded} GameCoins added! Current streak: ${data.new_streak} days!`, 'success');
                    
                    if (data.milestone_text) {
                        setTimeout(() => {
                            window.soundMgr.playAchievement();
                            this.showToast('Milestone Bonus! 🏆', data.milestone_text, 'warning');
                        }, 600);
                    }

                    if (data.unlocked_achievements && data.unlocked_achievements.length > 0) {
                        data.unlocked_achievements.forEach((ach, i) => {
                            setTimeout(() => this.triggerAchievementModal(ach), 1000 + i * 800);
                        });
                    }

                    // Update UI elements
                    this.updateNavStats(data.user);
                    const streakCount = document.getElementById('streakCountDisplay');
                    if (streakCount) streakCount.textContent = data.new_streak;

                    claimBtn.innerHTML = '✅ Claimed Today';
                    claimBtn.classList.remove('btn-primary', 'pulse-glow');
                    claimBtn.classList.add('btn-disabled');
                } else {
                    this.showToast('Streak Check-in', data.message, 'info');
                    claimBtn.innerHTML = 'Claim Daily Bonus';
                    claimBtn.disabled = false;
                }
            } catch (err) {
                console.error('Error claiming streak:', err);
                this.showToast('Error', 'Failed to connect to server.', 'error');
                claimBtn.disabled = false;
                claimBtn.innerHTML = 'Claim Daily Bonus';
            }
        });
    },

    // Submit Game Score API
    async submitScore(gameSlug, score, metadata = {}) {
        try {
            const res = await fetch('/api/submit-score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    game_slug: gameSlug,
                    score: Math.floor(score),
                    metadata: metadata
                })
            });

            const data = await res.json();
            if (!data.success) {
                console.error('Score submission error:', data.message);
                return null;
            }

            // Play coin and award sound
            window.soundMgr.playCoin();

            // Update topbar stats dynamically
            if (data.user) {
                this.updateNavStats(data.user);
            }

            // Check level-up
            if (data.progression && data.progression.leveled_up) {
                setTimeout(() => {
                    this.triggerLevelUpModal(data.progression.new_level, data.progression.bonus_coins);
                }, 700);
            }

            // Check unlocked achievements
            if (data.unlocked_achievements && data.unlocked_achievements.length > 0) {
                data.unlocked_achievements.forEach((ach, index) => {
                    setTimeout(() => {
                        this.triggerAchievementModal(ach);
                    }, 1200 + index * 1000);
                });
            }

            return data;
        } catch (err) {
            console.error('Failed to submit score:', err);
            return null;
        }
    },

    // Update coins, XP, and level displayed in navbar
    updateNavStats(user) {
        if (!user) return;
        const coinsEl = document.getElementById('navCoins');
        const levelEl = document.getElementById('navLevel');
        const xpBarEl = document.getElementById('navXpBar');
        const avatarEl = document.getElementById('navAvatar');

        if (coinsEl) {
            coinsEl.textContent = user.coins;
            coinsEl.classList.add('coin-bump');
            setTimeout(() => coinsEl.classList.remove('coin-bump'), 400);
        }
        if (levelEl) levelEl.textContent = user.level;
        if (xpBarEl && user.xp_percent !== undefined) {
            xpBarEl.style.width = `${user.xp_percent}%`;
        }
        if (avatarEl && user.avatar) {
            avatarEl.textContent = user.avatar;
        }
    },

    // Level-Up Modal
    triggerLevelUpModal(newLevel, bonusCoins) {
        window.soundMgr.playLevelUp();
        
        let modal = document.getElementById('levelUpModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'levelUpModal';
            modal.className = 'gz-modal-overlay';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="gz-modal-content level-up-card animate-pop">
                <div class="level-up-crown">👑</div>
                <h2 class="neon-title">LEVEL UP!</h2>
                <div class="level-badge-large">LEVEL ${newLevel}</div>
                <p class="level-up-subtitle">Incredible performance, Cyber Champion!</p>
                <div class="level-reward-box">
                    <span class="coin-icon">🪙</span>
                    <span class="reward-amount">+${bonusCoins} GameCoins</span>
                </div>
                <button class="btn btn-primary btn-glow" id="closeLevelUpBtn">CONTINUE PLAYING</button>
            </div>
        `;

        modal.classList.add('active');

        document.getElementById('closeLevelUpBtn').addEventListener('click', () => {
            modal.classList.remove('active');
        });
    },

    // Achievement Notification Toast & Modal
    triggerAchievementModal(ach) {
        window.soundMgr.playAchievement();

        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = 'achievement-toast animate-slide-in';
        toast.innerHTML = `
            <div class="ach-icon">${ach.icon || '🏆'}</div>
            <div class="ach-info">
                <div class="ach-badge">ACHIEVEMENT UNLOCKED!</div>
                <div class="ach-title">${ach.title}</div>
                <div class="ach-reward">+${ach.reward_coins} 🪙 GameCoins</div>
            </div>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('animate-slide-out');
            setTimeout(() => toast.remove(), 400);
        }, 4500);
    },

    // Generic Toast Notification
    showToast(title, message, type = 'info') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `gz-toast toast-${type} animate-slide-in`;
        
        const icons = {
            success: '✅',
            warning: '⚠️',
            error: '❌',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || '✨'}</div>
            <div class="toast-body">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('animate-slide-out');
            setTimeout(() => toast.remove(), 400);
        }, 3500);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.GameZone.init();
});

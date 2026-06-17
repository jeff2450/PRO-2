/**
 * Secure Server-Controlled Exam Countdown Timer
 * Simplified version - focuses on visible countdown updates
 */

class ExamCountdownTimer {
    constructor(options = {}) {
        this.attemptId = options.attemptId;
        this.testId = options.testId;
        this.timerDisplay = document.querySelector('[data-timer-display]');
        this.form = document.querySelector('[data-test-form]');
        this.warningThreshold = 300; // 5 minutes
        
        this.remainingSeconds = 0;
        this.endTime = null;
        this.isExpired = false;
        this.isSyncing = false;
        this.localTimerInterval = null;
        this.syncTimer = null;
        
        console.log('[TIMER] Init:', { 
            attemptId: this.attemptId, 
            testId: this.testId,
            display: !!this.timerDisplay,
            form: !!this.form
        });
        
        this.init();
    }

    async init() {
        try {
            if (!this.attemptId) {
                console.log('[TIMER] Starting exam');
                await this.startExam();
            }
            
            console.log('[TIMER] Getting status');
            await this.syncWithServer();
            
            console.log('[TIMER] Remaining:', this.remainingSeconds + 's');
            
            // IMMEDIATELY show the time
            this.updateDisplay();
            
            // Start countdown
            this.startLocalTimer();
            
            // Sync periodically
            this.startServerSync();
            
            this.setupVisibilityHandler();
            this.setupUnloadHandler();
        } catch (error) {
            console.error('[TIMER] Init error:', error);
        }
    }

    async startExam() {
        const response = await fetch('/api/exam-attempt/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test_id: this.testId }),
        });
        if (!response.ok) throw new Error('Failed to start exam');
        const data = await response.json();
        this.attemptId = data.attempt_id;
        this.remainingSeconds = data.remaining_seconds;
        if (this.form) {
            const input = this.form.querySelector('input[name="attempt_id"]');
            if (input) input.value = this.attemptId;
        }
        sessionStorage.setItem(`exam_attempt_${this.testId}`, this.attemptId);
        console.log('[TIMER] Exam started:', this.attemptId);
    }

    async syncWithServer() {
        if (this.isSyncing) return;
        this.isSyncing = true;
        try {
            const response = await fetch(`/api/exam-attempt/${this.attemptId}/status`);
            if (!response.ok) throw new Error('Sync failed');
            const data = await response.json();
            this.remainingSeconds = data.remaining_seconds;
            console.log('[TIMER] Synced:', this.remainingSeconds + 's');
            if (data.status === 'EXPIRED' || this.remainingSeconds <= 0) {
                this.handleTimeExpired();
            }
        } catch (error) {
            console.error('[TIMER] Sync error:', error);
        } finally {
            this.isSyncing = false;
        }
    }

    startLocalTimer() {
        console.log('[TIMER] Local timer starting');
        this.localTimerInterval = setInterval(() => {
            this.remainingSeconds--;
            this.updateDisplay();
            
            if (this.remainingSeconds <= 0) {
                clearInterval(this.localTimerInterval);
                this.handleTimeExpired();
            }
        }, 1000);
    }

    startServerSync() {
        this.syncTimer = setInterval(() => this.syncWithServer(), 30000);
    }

    updateDisplay() {
        if (!this.timerDisplay) return;
        
        const h = Math.floor(this.remainingSeconds / 3600);
        const m = Math.floor((this.remainingSeconds % 3600) / 60);
        const s = this.remainingSeconds % 60;
        
        let display = '';
        if (h > 0) display = `${h}h `;
        display += `${String(m).padStart(2, '0')}m ${String(s).padStart(2, '0')}s`;
        
        this.timerDisplay.textContent = display;
        console.log('[TIMER] Display updated:', display);
        
        // Update styling
        const container = this.timerDisplay.closest('[data-test-timer]');
        if (container) {
            container.classList.remove('timer-warning', 'timer-critical');
            if (this.remainingSeconds <= 60) {
                container.classList.add('timer-critical');
            } else if (this.remainingSeconds <= 300) {
                container.classList.add('timer-warning');
            }
        }
    }

    handleTimeExpired() {
        console.log('[TIMER] Time expired');
        clearInterval(this.localTimerInterval);
        clearInterval(this.syncTimer);
        this.isExpired = true;
        this.remainingSeconds = 0;
        this.updateDisplay();
        
        if (this.form) {
            this.form.querySelectorAll('input, button, textarea, select').forEach(el => {
                if (el.type !== 'hidden') el.disabled = true;
            });
        }
        
        const alert = document.createElement('div');
        alert.className = 'exam-alert exam-alert-critical';
        alert.textContent = '⏰ Time expired! Submitting...';
        document.body.appendChild(alert);
        
        setTimeout(() => {
            if (this.form) this.form.submit();
        }, 2000);
    }

    setupVisibilityHandler() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('[TIMER] Tab visible - syncing');
                this.syncWithServer();
            }
        });
    }

    setupUnloadHandler() {
        window.addEventListener('beforeunload', (e) => {
            if (!this.isExpired && this.form) {
                e.preventDefault();
                e.returnValue = 'Exam in progress';
            }
        });
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'exam-alert exam-alert-error';
        alert.textContent = message;
        document.body.appendChild(alert);
    }

    static async initialize(options) {
        const timerEl = document.querySelector('[data-test-timer]');
        if (!timerEl) {
            console.log('[TIMER] No timer element');
            return null;
        }
        
        // Extract test ID from multiple sources
        const fromArticle = timerEl.closest('[data-test-id]')?.dataset.testId;
        const fromPath = window.location.pathname.match(/\/mock-tests\/(\d+)/)?.[1];
        const fromURL = new URLSearchParams(window.location.search).get('test_id');
        
        const testId = parseInt(fromArticle || fromPath || fromURL || '0');
        let attemptId = parseInt(sessionStorage.getItem(`exam_attempt_${testId}`)) || null;
        
        console.log('[TIMER] Init params:', { testId, attemptId });
        
        const timer = new ExamCountdownTimer({ ...options, testId, attemptId });
        window.timerInstance = timer;
        return timer;
    }
}

// Auto-initialize
console.log('[TIMER] Script loaded');
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ExamCountdownTimer.initialize());
} else {
    ExamCountdownTimer.initialize();
}

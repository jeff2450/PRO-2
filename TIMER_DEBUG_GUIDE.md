# Timer Debugging Guide

## The Issue: Timer Not Counting Down

I've added comprehensive logging to help diagnose why the timer isn't decreasing. Follow these steps:

### Step 1: Open Developer Console
1. Go to the mock test page
2. Press **F12** (or right-click → Inspect)
3. Click the **Console** tab
4. You should see several logs starting with:
   ```
   "Exam timer script loaded, document ready state: complete"
   ```

### Step 2: Check the Console Logs

Look for these key messages:

**✅ GOOD SIGNS:**
```
Exam timer script loaded
DOMContentLoaded fired, initializing timer
Timer element found
Test ID detection: {fromArticle: "1", fromBody: undefined, fromURL: undefined, final: 1}
ExamCountdownTimer initialized with: {attemptId: null, testId: 1, timerDisplayElement: "Found", formElement: "Found"}
No attempt ID, starting new exam
Exam started successfully: {attempt_id: 42, status: "ACTIVE", remaining_seconds: 7200, ...}
Initial sync complete. Remaining seconds: 7200
Starting local timer with update interval: 1000
Starting server sync with interval: 30000
```

**❌ BAD SIGNS (Errors to Fix):**
```
Timer element not found
timerDisplayElement: "NOT FOUND"
formElement: "NOT FOUND"
HTTP error!
Test ID not detected
```

### Step 3: Real-time Monitoring

Once the timer is running:

1. In the Console, type:
   ```javascript
   document.querySelector('[data-timer-display]').textContent
   ```
   Should show something like: `"2h 00m 00s"`

2. Wait 5 seconds, then type the same command again
   Should show: `"1h 59m 55s"` (5 seconds less)

3. If it shows the same time, the display is not updating

### Step 4: Check API Responses

In the **Network** tab:

1. Look for requests to `/api/exam-attempt/start`
2. Click on it, go to **Response**
3. Should show:
   ```json
   {
       "attempt_id": 42,
       "status": "ACTIVE",
       "remaining_seconds": 7200,
       "end_time": "2026-06-17T14:30:00",
       "start_time": "2026-06-17T12:30:00"
   }
   ```

4. If this doesn't exist or shows an error, the backend isn't responding

### Step 5: Manual Timer Test

In the Console, paste this to manually test:

```javascript
// Check if timer is working
const display = document.querySelector('[data-timer-display]');
console.log('Display element:', display);
console.log('Current text:', display.textContent);

// Manually update it
display.textContent = '1h 59m 59s';
```

If the text changes, the display element is working. If not, it's not found.

---

## Common Issues & Solutions

### Issue 1: Timer Not Starting
**Symptoms:**
- Console shows: `Timer element not found`
- Timer display shows: `--:--`

**Solution:**
- Check that `<div class="test-timer" data-test-timer>` exists in the HTML
- Verify the `<strong data-timer-display>` element exists inside it
- Run: `document.querySelector('[data-test-timer]')` in console
- Should NOT be `null`

### Issue 2: Test ID Not Detected
**Symptoms:**
- Console shows: `final: 0`
- API call never happens

**Solution:**
- Verify `<article class="panel test-panel" data-test-id="1">` in HTML
- Check URL contains test_id parameter
- Run in console: 
  ```javascript
  document.querySelector('[data-test-id]')?.dataset.testId
  ```
  Should show a number like `"1"` or `"6"`

### Issue 3: API Error
**Symptoms:**
- Console shows: `Failed to start exam: HTTP error!`
- Network tab shows 404 or 500

**Solution:**
- Verify `/api/exam-attempt/start` endpoint exists in `app.py`
- Check that you're logged in as a student
- Check that test with given ID exists
- Verify no database errors in Flask console

### Issue 4: Timer Shows But Doesn't Decrease
**Symptoms:**
- Display shows `2h 00m 00s` correctly
- But never changes to `1h 59m 59s`

**Solution:**
- Check Console for errors
- Verify `this.localTimerInterval` is set (check: `window.timerInstance?.localTimerInterval`)
- Test manually: In console, run:
  ```javascript
  setInterval(() => console.log('test'), 1000)
  ```
  Should log "test" every second
  
- If that works, issue is in our timer logic

---

## Quick Diagnostic Test

Paste this entire code into the Console:

```javascript
// Diagnostic Test
console.log('=== TIMER DIAGNOSTIC ===');

// Check 1: Elements exist
const timerEl = document.querySelector('[data-test-timer]');
const displayEl = document.querySelector('[data-timer-display]');
const formEl = document.querySelector('[data-test-form]');

console.log('1. Elements Found:');
console.log('   - Timer container:', !!timerEl);
console.log('   - Display element:', !!displayEl);
console.log('   - Form element:', !!formEl);

// Check 2: Test ID
const testId = timerEl?.closest('[data-test-id]')?.dataset.testId;
console.log('2. Test ID:', testId);

// Check 3: Current display
console.log('3. Current display:', displayEl?.textContent);

// Check 4: DOM tree
console.log('4. Timer HTML:', timerEl?.outerHTML?.substring(0, 100));

// Check 5: Intervals
console.log('5. Active intervals:', !!window.timerInstance?.localTimerInterval ? 'YES' : 'NO');
```

### Expected Output:
```
1. Elements Found:
   - Timer container: true
   - Display element: true
   - Form element: true
2. Test ID: 1
3. Current display: 2h 00m 00s
4. Timer HTML: <div class="test-timer" data-test-timer...
5. Active intervals: YES
```

---

## Network API Check

In **Network** tab, filter for `exam-attempt`:

1. **POST /api/exam-attempt/start** should show:
   - Status: 200
   - Response includes `remaining_seconds` and `end_time`

2. **GET /api/exam-attempt/{id}/status** should show:
   - Status: 200
   - Response includes updated `remaining_seconds`

If any show 404/500, the API endpoints have issues.

---

## Backend Verification

Run this in Python to test the backend:

```python
# In Flask shell or a test script
from app import EXAM_ATTEMPTS, app
with app.app_context():
    # Create an attempt
    attempt_id = EXAM_ATTEMPTS.start_exam(user_id=1, test_id=1, duration_minutes=120)
    print(f"Created attempt: {attempt_id}")
    
    # Get status
    status = EXAM_ATTEMPTS.get_attempt_status(attempt_id)
    print(f"Status: {status}")
    
    # Should show remaining_seconds > 0
```

---

## Final Debugging Steps

If none of the above work:

1. **Clear browser cache**: Ctrl+Shift+Delete, clear all
2. **Hard refresh**: Ctrl+Shift+R (not just F5)
3. **Try another browser**: Check if issue is browser-specific
4. **Check server time**: Ensure server's system clock is correct
5. **Verify Flask is running**: Check terminal shows no errors
6. **Check database**: Run SQL query to verify `exam_attempts` table exists

---

## Report These Findings

When contacting support, include:
1. **Browser**: Chrome, Firefox, Safari, Edge?
2. **Console errors**: Screenshot of console tab
3. **Network requests**: Screenshot of Network tab
4. **Initial display**: What does timer show on page load?
5. **Expected vs actual**: "Should show 2h 00m 00s but shows ___"

---

*Last Updated: June 17, 2026*

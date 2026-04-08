# 🚀 TheraGenome AI - Quick Start Testing Guide

## ✅ Current Status

### Backend ✅ RUNNING
- **Server**: http://localhost:8000
- **Health Check**: ✅ Responding (HTTP 200)
- **Chatbot Tests**: ✅ ALL PASSED (7/7 tests)

### Command to Run Demo Tests
```powershell
C:/Users/shiva/AppData/Local/Microsoft/WindowsApps/python3.11.exe test_chatbot_demo.py
```

---

## 🎯 Quick Test - 5 Minutes

### Step 1: Open Browser (Right Now!)
Open your web browser and go to:
```
http://localhost:8000
```

You should see the **TheraGenome AI Demo Control Panel** with:
- 🎯 Demo Scenarios section with 3 buttons
  - ✓ Safe Case
  - ⚠ High Risk Case  
  - ⚖ Compare Drugs
- Display Mode selector (Doctor/Patient)
- Results area

### Step 2: Click a Scenario Button
1. Click **\"✓ Safe Case\"** button
2. Wait 1-2 seconds for results
3. You should see:
   - Drug name (amoxicillin)
   - Risk assessment
   - Clinical analysis
   - Template type

### Step 3: Test Voice Output 🔊
1. After results appear, look for **\"🔊 Speak Result\"** button
2. Click it
3. Your computer will read the results aloud!
4. Use these controls:
   - ⏸ Pause - Pause speaking
   - ▶ Resume - Resume speaking
   - ⏹ Stop - Stop speaking

### Step 4: Test Voice Input 🎤
1. Look for **\"🎤 Start Listening\"** button in the control panel
2. Click it (you'll see a pulsing microphone icon)
3. Speak clearly: **\"Safe Case\"**
4. The system will recognize your voice and auto-select the scenario!
5. Click **\"⏹ Stop Listening\"** when done

---

## 📋 Test Checklist

### Voice Input (Microphone) 🎤
- [ ] Microphone is connected and working
- [ ] Browser asks for microphone permission (allow it)
- [ ] Clicked \"🎤 Start Listening\" successfully
- [ ] Spoke \"Safe Case\" clearly
- [ ] System recognized the command
- [ ] Scenario was auto-selected
- [ ] Clicked \"⏹ Stop Listening\"

### Voice Output (Speaker) 🔊
- [ ] Speaker/headphones are connected
- [ ] Volume is not muted
- [ ] Clicked \"🔊 Speak Result\" button
- [ ] Audio played and you could hear it
- [ ] Speech was clear and intelligible
- [ ] Pause button worked
- [ ] Resume button worked
- [ ] Stop button worked

### Full Workflow
- [ ] Started listening with voice input
- [ ] Said \"High Risk Case\"
- [ ] System recognized and selected the scenario
- [ ] Scenario ran and showed results
- [ ] Clicked speak result
- [ ] System read the analysis aloud

---

## 🎮 Try All 3 Scenarios

### 1️⃣ Safe Case (\"Safe Treatment Case\")
```
What it does: Shows a patient with no drug interactions
Voice Command: Say \"Safe Case\"
Expected: Amoxicillin analysis, low/medium risk
Speak Result: Reads the safe treatment details
```

### 2️⃣ High Risk Case (\"⚠ High-Risk Case\")  
```
What it does: Shows a patient with genetic contraindications
Voice Command: Say \"High Risk Case\" or \"Risk Case\"
Expected: Ciprofloxacin analysis, high risk warning
Speak Result: Reads the risk assessment and warnings
```

### 3️⃣ Comparison Case (\"Compare Drugs\")
```
What it does: Compares two antibiotics for MRSA
Voice Command: Say \"Compare\" or \"Compare Drugs\"
Expected: Multi-drug comparison with rankings
Speak Result: Reads which drug is recommended
```

---

## 🔄 Test Different Modes

### Doctor Mode 👨‍⚕️
1. Select \"Doctor Mode (Full Details)\" from dropdown
2. Run any scenario
3. See full medical details:
   - Raw model outputs
   - Detailed explanations
   - All technical information
   - Complete clinical rationale

### Patient Mode 👤
1. Select \"Patient Mode (Simplified)\" from dropdown
2. Run the SAME scenario
3. Notice different output:
   - Simplified explanations
   - No technical jargon
   - Easy-to-understand language
   - Patient-friendly presentation

---

## 🎧 Voice Features in Detail

### Speech-to-Text Features
- **Real-time Transcription**: You'll see what you're saying as you speak
- **Intent Recognition**: Sistema recognizes specific commands
- **Auto-Selection**: Automatically selects the scenario based on voice
- **Error Handling**: Clear error messages if not recognized

### Text-to-Speech Features
- **Complete Analysis Reading**: Reads the entire result
- **Natural Speech**: Uses system voice (female/male)
- **Customizable Settings** (in code):
  - Rate: Speed of speaking (0.9 = 90% speed)
  - Pitch: Voice pitch (1.0 = normal)
  - Volume: Audio volume (1.0 = normal)
  - Language: Currently English US

### Browser Compatibility
- ✅ Chrome 25+ (best support)
- ✅ Edge 79+ (excellent support)
- ✅ Firefox 25+ (good support)  
- ✅ Safari 14.1+ (standard API)

---

## 🛠️ Troubleshooting

### \"Browser shows blank page\"
1. Make sure http://localhost:8000 is in address bar
2. Press Ctrl+Shift+Delete to clear cache
3. Try opening in incognito/private window
4. Check that backend server is running (see Terminal)

### \"Microphone not working\"
1. Check system microphone is connected
2. Make sure volume is up
3. In browser, check permissions (should allow microphone)
4. Try different browser
5. Refresh page (Ctrl+F5)

### \"Can't hear voice output\"
1. Check speaker/headphone volume (not muted!)
2. Check system volume (not muted!)
3. Try different browser
4. Refresh page
5. Check browser console (F12 → Console) for errors

### \"Voice not recognized from speech input\"
1. Speak clearly and loudly
2. Make sure no background noise
3. Click \"🎤 Start Listening\" first
4. Wait for system to show \"listening\" indicator
5. Speak the exact command: \"Safe Case\", \"High Risk Case\", or \"Compare\"

### \"Backend server crashed/stopped\"
1. Check terminal where server is running
2. Look for error messages
3. Restart server:
   ```powershell
   cd c:\Users\shiva\Desktop\Integration-theragenome2
   C:/Users/shiva/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
4. Refresh browser (Ctrl+F5)

---

## 📊 Backend API Endpoints

If you want to test the API directly:

### Health Check
```
GET http://localhost:8000/health
Response: {\"status\": \"ok\", \"service\": \"theragenome-ai\"}
```

### Run Demo Scenario (Python)
```python
from backend.chatbot.demo import run_demo_case
result = run_demo_case(\"safe_case\", mode=\"doctor\")
```

### Get Available Scenarios
```python
from backend.chatbot.demo import get_demo_cases
cases = get_demo_cases()
# Returns: [{'id': 'safe_case', ...}, ...]
```

---

## 📝 Recording Your Test

### Test Log Template
Use this to document what you tested:

```
=== TheraGenome AI Test Log ===
Date: ________________
Time: ________________
Browser: ________________
OS: Windows

BACKEND TESTS:
[ ] Ran test_chatbot_demo.py - Result: ________
[ ] All 7 tests passed: YES / NO

FRONTEND LOADING:
[ ] Frontend loaded at http://localhost:8000: YES / NO
[ ] Saw demo buttons: YES / NO
[ ] Can switch modes: YES / NO

VOICE INPUT:
[ ] Microphone permission granted: YES / NO
[ ] Started listening: YES / NO
[ ] Said \"Safe Case\": YES / NO
[ ] System recognized: YES / NO
[ ] Scenario auto-selected: YES / NO

VOICE OUTPUT:
[ ] Results displayed: YES / NO
[ ] Speak button visible: YES / NO
[ ] Audio played: YES / NO
[ ] Could hear clearly: YES / NO
[ ] Pause worked: YES / NO
[ ] Resume worked: YES / NO
[ ] Stop worked: YES / NO

ALL SCENARIOS TESTED:
[ ] Safe Case: Completed / Skipped / Failed
[ ] High Risk Case: Completed / Skipped / Failed
[ ] Compare Drugs: Completed / Skipped / Failed

BOTH MODES TESTED:
[ ] Doctor Mode: Completed / Skipped / Failed
[ ] Patient Mode: Completed / Skipped / Failed

TOTAL SCORE: __/10 features working

Notes:
_______________________
_______________________
_______________________
```

---

## ✅ Success Criteria

Your testing is successful when you can:

1. ✅ Open http://localhost:8000 and see demo control panel
2. ✅ Click any scenario button and get results
3. ✅ Click \"🔊 Speak Result\" and hear it read aloud
4. ✅ Click \"🎤 Start Listening\" and say a voice command
5. ✅ System recognizes your voice and selects scenario
6. ✅ Switch between Doctor and Patient modes
7. ✅ Test all 3 scenarios (Safe, High-Risk, Comparison)
8. ✅ No errors in browser console (F12)
9. ✅ No errors in terminal where server is running
10. ✅ All voice features work as expected

---

## 🎓 Learning Resources

- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Full testing guide with troubleshooting
- [VOICE_FEATURES_GUIDE.md](./VOICE_FEATURES_GUIDE.md) - Voice API details
- [DEMO_USAGE.md](./DEMO_USAGE.md) - Python API examples
- [MULTILINGUAL_VOICE_GUIDE.md](./MULTILINGUAL_VOICE_GUIDE.md) - Voice customization

---

## 🎬 Next Steps

1. **Right Now**: Open http://localhost:8000 in your browser
2. **Click** on \"Safe Case\" button
3. **Wait** for results to load
4. **Click** \"🔊 Speak Result\" and listen
5. **Click** \"🎤 Start Listening\" and say \"Safe Case\"
6. **Try all** 3 scenarios and both modes

---

**Backend is running at http://localhost:8000 ✅**

**Ready to test? Open your browser now!** 🚀

---

For detailed troubleshooting and advanced testing, see [TESTING_GUIDE.md](./TESTING_GUIDE.md)

# 🧪 TheraGenome AI Chatbot - Sample Test Cases

## Test Environment Setup

**Backend**: http://localhost:8000 (running)  
**Frontend**: http://localhost:8001 (running)  
**Mode**: Can be Doctor or Patient

---

## Category 1: Drug Safety Questions

### Test Case 1.1: Single Safe Drug
```
Input: "Is amoxicillin safe?"

Expected in Doctor Mode:
- Template: DRUG_NOT_RECOMMENDED or SAFE_TO_USE (depends on patient data)
- Intent: drug_analysis
- Shows drug name: amoxicillin
- Shows risk level badge
- Shows confidence score
- Doctor mode: clinical reasoning

Expected in Patient Mode:
- Same response
- Simpler language
- No technical jargon
```

### Test Case 1.2: Drug with Allergy Context
```
Input: "Can I take penicillin if allergic to beta-lactams?"

Expected in Doctor Mode:
- Template: DRUG_NOT_RECOMMENDED
- Intent: drug_analysis
- Risk Level: high
- Reason codes: ALLERGY_CONTRAINDICATION
- Full medical explanation

Expected in Patient Mode:
- Simple: "No, you should not take this drug"
- Reason: "You are allergic to the drug class"
```

### Test Case 1.3: Drug with Caution
```
Input: "Is ciprofloxacin safe for my patient?"

Expected Output:
- Template: DRUG_USE_WITH_CAUTION
- Risk Level: medium or high
- Doctor mode: Lists specific concerns (QT prolongation, etc.)
- Patient mode: "Can be used but needs monitoring"
```

---

## Category 2: Comparison Questions

### Test Case 2.1: Simple Drug Comparison
```
Input: "Which is better - vancomycin or linezolid?"

Expected Output:
- Intent: compare_drugs
- Template: COMPARISON_RESULT
- Doctor mode: Detailed comparison with scores
- Patient mode: "Vancomycin is recommended" or similar

Visual: Comparison metrics/table
```

### Test Case 2.2: Multi-factor Comparison
```
Input: "Compare amoxicillin, cephalexin, and doxycycline"

Expected Output:
- Intent: compare_drugs
- Lists all three drugs
- Risk/benefit analysis for each
- Recommendation for best option

Doctor mode: Detailed clinical data
Patient mode: Simple recommendation
```

---

## Category 3: Insufficient Context

### Test Case 3.1: Vague Question
```
Input: "Is this drug safe?"

Expected Output:
- Template: REQUIRE_MORE_DATA or INSUFFICIENT_CONTEXT
- Intent: input_guidance
- Response: "Which drug are you asking about?"
- Guidance: "Please provide..."

Visual: Information box with help text
```

### Test Case 3.2: Missing Patient Data
```
Input: "Should I take antibiotics?"

Expected Output:
- Request for more information:
  - What infection?
  - What symptoms?
  - Known allergies?

Response: "I need more context to help you"
```

---

## Category 4: Mode Switching Tests

### Test Case 4.1: Same Question, Different Modes
```
Step 1: Set to Doctor Mode
Input: "Is warfarin safe?"

Step 2: Note the detailed response

Step 3: Change to Patient Mode
Input: "Is warfarin safe?"

Step 4: Compare responses
Doctor: "Warfarin (Coumarin) requires monitoring. INR levels must be maintained..."
Patient: "Warfarin needs regular blood tests. Discuss with your doctor."
```

### Test Case 4.2: Mode Persistence
```
Step 1: Switch to Patient Mode
Step 2: Ask a question
Step 3: Refresh page
Step 4: Mode should still be Patient Mode (localStorage)

Expected: Mode preference persists
```

---

## Category 5: Error Handling

### Test Case 5.1: Empty Message
```
Input: Click Send with empty field

Expected:
- Nothing happens
- No API call
- No error message
- Field remains focused
```

### Test Case 5.2: Backend Unavailable
```
Setup: Stop backend server
Input: Ask any question

Expected:
- Loading spinner appears
- After timeout: Error message
- Message: "Failed to process..." / "Connection error"
- User can retry
```

### Test Case 5.3: Invalid Response Format
```
Input: Question that gets unexpected response format

Expected:
- Graceful handling
- Error message shown
- No JavaScript errors in console
```

---

## Category 6: UI/UX Tests

### Test Case 6.1: Message Display
```
Expected:
- User message: Blue bubble, right side
- Bot message: Gray bubble, left side
- Messages have timestamps
- Auto-scroll to newest message
- Messages readable and well-formatted
```

### Test Case 6.2: Responsive Layout
```
Test on:
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

Expected:
- Chatbot container resizes
- Messages still readable
- Input field accessible
- Buttons clickable
- No horizontal scroll
```

### Test Case 6.3: Loading State
```
Input: Question that takes time

Expected:
- Loading spinner visible
- Message: "TheraGenome is analyzing..."
- Send button disabled
- Input field disabled
```

---

## Category 7: Chat History & Persistence

### Test Case 7.1: Chat History Displayed
```
Step 1: Ask 3 questions
Step 2: All messages visible in chat
Step 3: Scroll through history
Step 4: Timestamps correct
Step 5: Messages in correct order

Expected: Full conversation visible
```

### Test Case 7.2: Welcome Message Behavior
```
Step 1: First load - see welcome message
Step 2: Ask first question - welcome hides
Step 3: Continue conversation - no welcome

Expected: Welcome message appears once,
then starts showing chat messages
```

---

## Category 8: Template-Specific Tests

### Test Case 8.1: SAFE_TO_USE Template
```
Input: "Is acetaminophen safe?"

Visual Check:
- Green ✅ indicator
- "SAFE_TO_USE" badge
- Positive language
- Low risk level badge
```

### Test Case 8.2: DRUG_NOT_RECOMMENDED Template
```
Input: "Can I take aspirin if allergic to salicylates?"

Visual Check:
- Red ❌ indicator
- "DRUG_NOT_RECOMMENDED" badge
- Warning language
- High risk level badge
```

### Test Case 8.3: DRUG_USE_WITH_CAUTION Template
```
Input: Depending on backend, may get caution response

Visual Check:
- Yellow ⚠️ indicator
- "DRUG_USE_WITH_CAUTION" badge
- Moderate caution language
- Medium risk level badge
```

---

## Category 9: Doctor vs Patient Mode Details

### Test Case 9.1: Doctor Mode Features
```
Ask: "What are the contraindications for metoprolol?"

Doctor Mode Shows:
- Full drug name
- Detailed risk assessment
- Technical medical terms
- Specific contraindication codes
- Clinical rationale
- Model scores/confidence

Patient Mode Shows:
- Simple drug name
- Basic risk summary
- Plain language explanation
- Simple yes/no/caution answer
- What to do instead
```

---

## Category 10: Edge Cases

### Test Case 10.1: Very Long Input
```
Input: "I have been taking drug X for condition Y 
and also taking drug Z, and I'm worried about interactions 
because I also have condition W and I'm allergic to..."

Expected:
- Full message displayed
- Wraps correctly
- Readable
- API call succeeds
```

### Test Case 10.2: Special Characters
```
Input: "Is acetyl-CoA safe? What about @-compounds?"

Expected:
- Special chars displayed correctly
- No XSS or injection attacks
- Message sends successfully
```

### Test Case 10.3: Rapid Fire Questions
```
Step 1: Ask question A, don't wait for response
Step 2: Ask question B
Step 3: Ask question C
Step 4: Wait for all responses

Expected:
- All questions queued
- Responses come in order
- No messages lost
- No API errors
```

---

## Test Results Template

```
Date: __________
Tester: __________

Test Case: ________________
Input: ________________
Mode: Doctor / Patient
Status: PASS / FAIL
Notes: ________________

Visual Check:
[ ] Messages display correctly
[ ] Colors match expected
[ ] Layout is responsive
[ ] Timestamps visible
[ ] No console errors

API Check:
[ ] Request sent correctly
[ ] Response received
[ ] Response parsed
[ ] No 400/500 errors
[ ] Processing time reasonable

Functionality Check:
[ ] Mode switching works
[ ] Send button works
[ ] Input clears after send
[ ] Loading state works
[ ] Error handling works

Overall: PASS / FAIL
```

---

## Quick Test Checklist

**Before You Start:**
- [ ] Backend running on :8000
- [ ] Frontend running on :8001
- [ ] Browser console open (F12)
- [ ] Network tab open (F12 → Network)

**Basic Tests:**
- [ ] Page loads at http://localhost:8001
- [ ] Chatbot interface visible
- [ ] Welcome message shows
- [ ] Can type in input field
- [ ] Send button is clickable

**Functionality:**
- [ ] Send message successfully
- [ ] Response appears in chat
- [ ] Mode toggle works
- [ ] Timestamps show
- [ ] No JavaScript errors

**Integration:**
- [ ] API call visible in Network tab
- [ ] HTTP 200 response
- [ ] Response JSON correct format
- [ ] Frontend parses response
- [ ] No CORS errors

**Mode Testing:**
- [ ] Doctor mode shows full details
- [ ] Patient mode simplifies response
- [ ] Mode preference saved
- [ ] Same question shows differences

**Edge Cases:**
- [ ] Empty message blocking works
- [ ] Long messages handled
- [ ] Special characters safe
- [ ] Error messages display
- [ ] Rapid queries don't break

---

## Success Criteria

All tests pass when:

✅ Messages send and receive correctly  
✅ Both modes work as expected  
✅ No JavaScript errors in console  
✅ No network/CORS errors  
✅ Response formatting correct  
✅ UI is responsive and readable  
✅ Error handling graceful  
✅ Performance acceptable (<2 sec)  

---

## Notes

- Each test should be independent
- Run on multiple browsers
- Test on mobile if possible
- Document any failures
- Report bugs with screenshots
- Include console errors in bug reports
- Note response times
- Check performance in Network tab

---

## Sample Passing Test Output

```
TEST CASE 1.1: Single Safe Drug
Input: "Is amoxicillin safe?"
Mode: Doctor
Status: ✅ PASS

Visual: ✅ OK - Blue user bubble, gray bot bubble, readable
API: ✅ OK - HTTP 200, response JSON valid
Functionality: ✅ OK - Message sent, response received
Timing: 0.8s API call

All tests: PASSED ✅
```

---

**You're ready to test!** 🚀

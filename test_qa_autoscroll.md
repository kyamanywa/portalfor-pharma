# QA Auto-Scroll Feature - Capsule Filling

## What Was Added

Added automatic scrolling for QA users to pending sections in the capsule filling phase.

## How It Works

When a QA user opens the BMR document, the page will automatically scroll to:

### 1. **Line Clearance Priority**
   - Beginning LC (if status = `operator_filled`)
   - Ending LC (if status = `operator_filled`)

### 2. **IPQC Visual Inspection Priority** (NEW)
   - IPQC 1 (if status = `operator_filled`)
   - IPQC 2 (if status = `operator_filled`)
   - IPQC 3 (if status = `operator_filled`)
   - IPQC 4 (if status = `operator_filled`)
   - IPQC 5 (if status = `operator_filled`)
   - IPQC 6 (if status = `operator_filled`)

## Status Meanings

- **`not_started`** - Operator hasn't filled yet
- **`operator_filled`** - ✅ Operator completed, awaiting QA signature (TRIGGERS AUTO-SCROLL)
- **`qa_signed`** - QA has signed, section complete
- **`completed`** - Fully completed

## Example Scenarios

### Scenario 1: QA Login with Pending IPQC 3
- Operator completed IPQC 1, 2, and 3
- QA signed IPQC 1 and 2
- **Result**: Page auto-scrolls to IPQC 3 section

### Scenario 2: QA Login with Ending LC Pending
- All IPQCs completed and signed
- Ending LC filled by operator
- **Result**: Page auto-scrolls to Ending LC section

### Scenario 3: QA Login with Beginning LC Pending
- Beginning LC filled by operator
- **Result**: Page auto-scrolls to Beginning LC section (highest priority)

## Files Modified

- `templates/bmr/bmr_capsule.html` (lines ~5344-5370)
  - Added QA auto-scroll logic for IPQC sections with `operator_filled` status

## Testing

1. Log in as QA user
2. Navigate to BMR with capsule filling phase
3. Ensure at least one IPQC section has status `operator_filled`
4. Page should automatically scroll to that section on load

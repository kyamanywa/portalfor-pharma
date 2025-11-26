# Implementation Plan - Failure & Recovery Mechanisms

## What I Will FIX (3 Things Only):

---

### FIX #1: Automatic Rollback for Failed Phases
**Currently:** QA Final QA rejection uses MANUAL rollback code (lines 609-643 in dashboards/views.py)
**Problem:** Duplicates logic that already exists in `WorkflowService.handle_qc_failure_rollback()`
**Solution:** Replace manual code with service method call

**Changes:**
- Remove lines ~609-643 (manual rollback code in qa_dashboard)
- Replace with: `WorkflowService.handle_qc_failure_rollback(bmr, 'final_qa', rollback_phase)`
- Same result but cleaner, reusable, maintainable

**Impact:** Final QA rejections still work exactly the same way

---

### FIX #2: Recovery Mechanism for Failed Production Phases
**Currently:** When production phase fails → just marked 'failed' → no recovery
**Problem:** Batch stuck, cannot retry
**Solution:** Add service method to handle recovery

**What I'll Create:**
- New method: `WorkflowService.handle_production_phase_failure()`
- Marks phase as 'failed' with reason
- Resets the SAME phase back to 'pending' so operator can retry
- NOT rollback to previous phase - just retry current phase

**When Used:**
- Currently: NOWHERE (doesn't exist yet, will be there for future use)
- Operator workflow stays the same (start/complete only)
- No changes to operator dashboard

**Impact:** Future-proof code, ready when needed

---

### FIX #3: Rejected BMRs - Add to QA Dashboard
**Currently:** Regulatory rejects BMR → BMR.status='rejected' → disappears
**Problem:** QA can't see rejected BMRs, can't re-submit

**Solution:** Add rejected BMRs to QA Dashboard

**Changes in qa_dashboard() view:**
1. Query: `rejected_bmrs = BMR.objects.filter(status='rejected')`
2. Add to context: `'rejected_bmrs_for_review': rejected_bmrs`
3. Add re-submission endpoint handling:
   - QA clicks "Re-submit" on rejected BMR
   - Method: Resets `regulatory_approval` phase to 'pending'
   - Sets `bmr.status = 'submitted'`
   - BMR goes back to regulatory for review

**Changes in qa_dashboard.html template:**
1. Add new section: "Rejected BMRs Needing Review"
2. Show list of rejected BMRs with rejection reason
3. Add "Review & Re-submit" button for each

**Impact:** 
- Rejected BMRs are now visible to QA
- QA can review rejection reason and re-submit
- Batch recovery is automatic and traceable

---

## What I Will NOT Touch:

✅ **Operator dashboards** - Stay exactly as is (start/complete only)
✅ **Regulatory approval flow** - Only fix the rejection handling on QA side
✅ **QC rejection logic** - Already working correctly
✅ **Production phase logic** - No changes to how operators work

---

## Files That Will Be Modified:

1. **dashboards/views.py**
   - Line 568-723: qa_dashboard() - Add rejected BMR query and re-submission handler
   - New service method call for Final QA rollback (cleanup)
   - Add new WorkflowService.handle_production_phase_failure() method

2. **workflow/services.py**
   - Add: WorkflowService.handle_production_phase_failure() method
   - Refactor to use consistent rollback patterns

3. **templates/dashboards/qa_dashboard.html**
   - Add new section for "Rejected BMRs Needing Review"
   - Add re-submission form/modal

---

## Summary:

| Component | Current | After Fix | Impact |
|-----------|---------|-----------|--------|
| QA Rollback | Manual code | Service method | Cleaner, same result |
| Failed Phases | No recovery | Service method available | Ready for recovery |
| Rejected BMRs | Invisible | Visible in QA Dashboard | QA can re-submit |
| Operators | start/complete | No change | Unaffected |
| Regulatory | Rejects BMR | No change (handled on QA side) | Unaffected |

---

## Risk Assessment:

🟢 **LOW RISK** - All changes are additive or cleanup
- Not removing existing functionality
- Adding new visibility
- Using existing service patterns
- Operators workflow unchanged

---

**Ready for approval to proceed?**

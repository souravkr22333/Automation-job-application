# Queue Auto-Generate Fix Plan

## Bug 1: Frontend Doesn't Handle "done" Status
- **File**: `frontend/src/components/jobs/Addtoqueue.jsx`
- **Fix**: Add `'done'` to success status cases in `onAutoGenerate`

## Bug 2: Queue Polling Never Stops
- **File**: `frontend/src/contexts/QueueContext.jsx`
- **Fix**: Stop polling when all jobs reach final state (done/failed)

## Bug 3: Backend Error Isolation & Timeout
- **File**: `Backend/django_app/applications/views.py`
- **Fix**: Better error boundaries, isolate per-job failures, increase timeout

## Bug 4: Response Data Mapping Mismatch
- **File**: `frontend/src/components/jobs/Addtoqueue.jsx`
- **Fix**: Map backend response fields correctly (backend returns `job_id` in results)


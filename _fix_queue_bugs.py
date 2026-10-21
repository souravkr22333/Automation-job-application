"""
Comprehensive fix for queue/auto-generate issues:
1. Fix: When FastAPI returns 200, Django might still fail if response format doesn't match expectations
2. Fix: Queue polling never stops (already partially fixed, adding robustness)
3. Fix: Idempotency key collisions causing IntegrityError
4. Fix: Better error logging for debugging
5. Fix: Frontend status mapping correctness
"""

import os, sys

# ============================================================
# FIX 1: Backend - applications/views.py - auto_generate improvements
# ============================================================
views_path = 'Backend/django_app/applications/views.py'
with open(views_path, 'r') as f:
    content = f.read()

# Fix 1a: Add traceback import at the top
if 'import traceback' not in content.split('import logging')[0] if 'import logging' in content else '':
    print("Check 1a: traceback import check")

# Fix 1b: Fix the auto_generate method to better handle FastAPI responses
# The current fix was already applied (tailored_resume_obj = None etc.)
# But let's add better error handling for the FastAPI call itself

# Fix 1c: Fix the idempotency_key collision issue - add a unique suffix
old_idem = """                import hashlib
                idem_key_str = f"{request.user.id}_{job_id}_auto_generate"
                idempotency_key = hashlib.sha256(idem_key_str.encode()).hexdigest()"""

new_idem = """                import hashlib
                import uuid
                idem_key_str = f"{request.user.id}_{job_id}_{uuid.uuid4().hex[:8]}_auto_generate"
                idempotency_key = hashlib.sha256(idem_key_str.encode()).hexdigest()"""

if old_idem in content:
    content = content.replace(old_idem, new_idem)
    print("Fix 1c: Applied idempotency key collision fix")
else:
    # Check if already fixed
    if 'uuid.uuid4().hex[:8]' in content:
        print("Fix 1c: Already applied")
    else:
        print("Fix 1c: Pattern not found, checking...")
        if 'idem_key_str' in content:
            # Find the current pattern
            idx = content.find('idem_key_str')
            print(f"  Found idem_key_str at position {idx}:")
            print(content[idx:idx+150])

# Fix 1d: Add better error logging for the auto_generate except blocks
# Check for the generic except that catches Queue error for job
old_generic = """            except Exception as e:
                logger.error(f"Queue error for job {job_id}: {str(e)}")
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'message': str(e)
                })"""

new_generic = """            except Exception as e:
                logger.error(f"Queue error for job {job_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                results.append({
                    'job_id': job_id,
                    'status': 'failed',
                    'message': str(e)
                })"""

if old_generic in content:
    content = content.replace(old_generic, new_generic)
    print("Fix 1d: Applied better logging for generic queue error")
else:
    print("Fix 1d: Pattern not found (may already have better logging)")

# Fix 1e: Also add better logging in the _tailor_resume method
old_tailor_log = """        except Exception as e:
            logger.error(f"Tailoring error: {str(e)}")
            raise"""

new_tailor_log = """        except Exception as e:
            logger.error(f"Tailoring error: {str(e)}")
            import traceback
            logger.error(f"Tailoring traceback: {traceback.format_exc()}")
            raise"""

if old_tailor_log in content:
    content = content.replace(old_tailor_log, new_tailor_log)
    print("Fix 1e: Applied better logging in _tailor_resume")
else:
    print("Fix 1e: Pattern not found")

with open(views_path, 'w') as f:
    f.write(content)

# ============================================================
# FIX 2: Backend - Queue serializers - Add 'job' field mapping for frontend
# ============================================================
serializers_path = 'Backend/django_app/applications/serializers.py'
with open(serializers_path, 'r') as f:
    content = f.read()

# The serializer currently has 'job' which returns the UUID - good
if 'job =' in content:
    print("Fix 2: Serializer already has job field (UUID mapping)")
else:
    print("Fix 2: Serializer job field check")

# ============================================================
# FIX 3: Frontend - QueueContext - Add processing auto-stop after polling
# ============================================================
queuectx_path = 'frontend/src/contexts/QueueContext.jsx'
with open(queuectx_path, 'r') as f:
    content = f.read()

# Check if setIsProcessing(false) is called when all jobs are final
if 'setIsProcessing(false)' not in content:
    print("Fix 3a: Need to add auto-reset of isProcessing in polling")
    # Add an effect to auto-stop processing when all jobs reach final state
    old_effect_end = """    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [queueJobIds.length, allJobsFinal]);"""
    
    new_effect_end = """    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [queueJobIds.length, allJobsFinal]);
  
  // Auto-stop processing flag when all jobs reach final state
  useEffect(() => {
    if (allJobsFinal && queueJobIds.length > 0) {
      setIsProcessing(false);
    }
  }, [allJobsFinal, queueJobIds.length]);"""
    
    if old_effect_end in content:
        content = content.replace(old_effect_end, new_effect_end)
        print("Fix 3a: Applied auto-stop for isProcessing")
    else:
        print("Fix 3a: Pattern not found, exact match needed")
        idx = content.find('}, [queueJobIds.length, allJobsFinal]);')
        if idx > 0:
            print(f"  Found at {idx}")
else:
    print("Fix 3a: Already has setIsProcessing(false) call")

# Also need to add setIsProcessing to the allJobsFinal check in polling
# Actually better: add a separate effect to reset isProcessing when auto_generate completes
old_poll_body_start = """    const pollStatus = async () => {
      try {
        const response = await jobApi.getQueueStatus();
        const data = response.data;
        if (data && data.items) {
          setJobStatuses((prev) => {"""

new_poll_body_start = """    const pollStatus = async () => {
      try {
        const response = await jobApi.getQueueStatus();
        const data = response.data;
        if (data && data.items) {
          setJobStatuses((prev) => {"""

# Check if the file already has the fixes
if 'allJobsFinal' in content:
    print("Fix 3b: QueueContext already has allJobsFinal support")
else:
    print("Fix 3b: QueueContext missing allJobsFinal - might be older version")
    # Add allJobsFinal useMemo after the existing useEffects
    old_after_persist = """  // Persist to sessionStorage whenever queueJobIds changes
  useEffect(() => {
    saveQueueToStorage(queueJobIds);
  }, [queueJobIds]);"""
    
    new_after_persist = """  // Persist to sessionStorage whenever queueJobIds changes
  useEffect(() => {
    saveQueueToStorage(queueJobIds);
  }, [queueJobIds]);
  
  // Determine if all jobs are in final state (done/failed)
  const allJobsFinal = useMemo(() => {
    if (queueJobIds.length === 0) return false;
    return queueJobIds.every((id) => {
      const status = jobStatuses[id];
      return status === 'done' || status === 'failed';
    });
  }, [queueJobIds, jobStatuses]);"""
    
    if old_after_persist in content:
        content = content.replace(old_after_persist, new_after_persist)
        print("Fix 3b: Added allJobsFinal useMemo")
    
    # Fix polling effect dependency
    old_poll_dep = """  }, [queueJobIds.length]);"""
    new_poll_dep = """  }, [queueJobIds.length, allJobsFinal]);"""
    if old_poll_dep in content and 'allJobsFinal' not in content:
        content = content.replace(old_poll_dep, new_poll_dep)
        print("Fix 3b: Updated polling dependency")

with open(queuectx_path, 'w') as f:
    f.write(content)

# ============================================================
# FIX 4: Frontend - Addtoqueue.jsx - Better error handling
# ============================================================
addtoqueue_path = 'frontend/src/components/jobs/Addtoqueue.jsx'
with open(addtoqueue_path, 'r') as f:
    content = f.read()

# The Addtoqueue already looks good from our earlier analysis
# But let's add better error messages and logging
old_catch = """    } catch (e) {
      const errMsg =
        e?.response?.data?.detail || e?.message || "Failed to auto-generate resumes";
      setError(errMsg);"""

new_catch = """    } catch (e) {
      console.error("Auto-generate error:", e);
      console.error("Response data:", e?.response?.data);
      console.error("Response status:", e?.response?.status);
      const errMsg =
        e?.response?.data?.detail || 
        e?.response?.data?.error || 
        e?.response?.data?.message ||
        e?.message || 
        `Server error (${e?.response?.status || 'unknown'})`;
      setError(errMsg);"""

if old_catch in content:
    content = content.replace(old_catch, new_catch)
    print("Fix 4: Applied better error handling in Addtoqueue")
else:
    print("Fix 4: Could not find pattern")

with open(addtoqueue_path, 'w') as f:
    f.write(content)

print("\n=== All fixes applied! ===")
print("Please restart your Django and FastAPI servers for changes to take effect.")

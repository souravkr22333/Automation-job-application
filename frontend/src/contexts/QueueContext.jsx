import React, { createContext, useContext, useMemo, useState, useCallback, useEffect, useRef } from 'react';
import jobApi from '../services/jobApi';

const QUEUE_STORAGE_KEY = 'autoapply_queue_ids';

const QueueContext = createContext(null);

export const useQueue = () => {
  const ctx = useContext(QueueContext);
  if (!ctx) throw new Error('useQueue must be used within QueueProvider');
  return ctx;
};

const loadQueueFromStorage = () => {
  try {
    const stored = sessionStorage.getItem(QUEUE_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch (e) {
    console.warn('Failed to load queue from sessionStorage:', e);
  }
  return [];
};

const saveQueueToStorage = (ids) => {
  try {
    sessionStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(ids));
  } catch (e) {
    console.warn('Failed to save queue to sessionStorage:', e);
  }
};

// Status priority order: higher number = more "final"
const STATUS_ORDER = {
  queued: 0,
  processing: 1,
  generating_resume: 1,
  applying: 1,
  retrying: 1,
  done: 2,
  failed: 2,
  limit_reached: 2,
};

export const QueueProvider = ({ children }) => {
  const [queueJobIds, setQueueJobIds] = useState(loadQueueFromStorage);
  const [jobStatuses, setJobStatuses] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  const pollingRef = useRef(null);

  // Persist to sessionStorage whenever queueJobIds changes
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
  }, [queueJobIds, jobStatuses]);

  // Poll backend for status updates when there are active jobs
  useEffect(() => {
    // Stop polling if no jobs in queue OR all jobs reached final state
    if (queueJobIds.length === 0 || allJobsFinal) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }

    const pollStatus = async () => {
      try {
        const response = await jobApi.getQueueStatus();
        const data = response.data;
        if (data && data.items) {
          setJobStatuses((prev) => {
            const next = { ...prev };
            data.items.forEach((item) => {
              const jobId = item.job;
              // Map backend retrying -> frontend processing
              const backendStatus =
                item.status === 'retrying' ? 'processing' : item.status;
              const prevPriority = STATUS_ORDER[prev[jobId]] ?? -1;
              const newPriority = STATUS_ORDER[backendStatus] ?? -1;
              // Only upgrade: never overwrite 'processing'/'done'/'failed' with 'queued'
              if (newPriority >= prevPriority) {
                next[jobId] = backendStatus;
              } else {
                next[jobId] = prev[jobId];
              }
            });
            return next;
          });
        }
      } catch (e) {
        // Silently fail on polling errors
      }
    };

    // Initial poll
    pollStatus();

    // Poll every 3 seconds
    pollingRef.current = setInterval(pollStatus, 3000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [queueJobIds.length, allJobsFinal]);

  const toggleJob = useCallback((jobId) => {
    setQueueJobIds((prev) => {
      if (prev.includes(jobId)) {
        const filtered = prev.filter((id) => id !== jobId);
        return filtered;
      }
      return [...prev, jobId];
    });
  }, []);

  const clearQueue = useCallback(() => {
    setQueueJobIds([]);
    setJobStatuses({});
    setIsProcessing(false);
  }, []);

  const removeJobFromQueue = useCallback((jobId) => {
    setQueueJobIds((prev) => prev.filter((id) => id !== jobId));
    setJobStatuses((prev) => {
      const updated = { ...prev };
      delete updated[jobId];
      return updated;
    });
  }, []);

  const updateJobStatus = useCallback((jobId, status) => {
    setJobStatuses((prev) => ({ ...prev, [jobId]: status }));
  }, []);

  const setProcessing = useCallback((processing) => {
    setIsProcessing(processing);
  }, []);

  const value = useMemo(
    () => ({
      queueJobIds,
      jobStatuses,
      isProcessing,
 
 
      toggleJob,
      clearQueue,
      removeJobFromQueue,
      updateJobStatus,
      setProcessing,
    }),
    [queueJobIds, jobStatuses, isProcessing, toggleJob, clearQueue, removeJobFromQueue, updateJobStatus, setProcessing]
  );

  return <QueueContext.Provider value={value}>{children}</QueueContext.Provider>;
};

import React, { useMemo, useState } from "react";
import { ListChecks, Trash2, Zap, Loader2, CheckCircle, Clock, AlertCircle } from "lucide-react";
import jobApi from "../../services/jobApi";
import { useQueue } from "../../contexts/QueueContext";

const Addtoqueue = ({
  jobs = [],
  className = "",
  sidebarTitle = "Queue",
}) => {
  const {
    queueJobIds,
    jobStatuses,
    clearQueue,
    removeJobFromQueue,
    updateJobStatus,
    setProcessing,
  } = useQueue();

  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const queueJobs = useMemo(() => {
    const byId = new Map((jobs || []).map((j) => [j.id, j]));
    return queueJobIds.map((id) => byId.get(id)).filter(Boolean);
  }, [jobs, queueJobIds]);

  const onAutoGenerate = async () => {
    if (!queueJobIds.length) return;
    setError(null);
    setSuccessMessage(null);
    setProcessing(true);

    queueJobIds.forEach((id) => updateJobStatus(id, "processing"));

    try {
      const response = await jobApi.autoGenerateQueue(queueJobIds, null);
      const result = response.data;
      const processedIds = new Set();

      if (result.results) {
        result.results.forEach((res) => {
          processedIds.add(res.job_id);
          if (res.status === "done" || res.status === "pending" || res.status === "already_generated") {
            updateJobStatus(res.job_id, "done");
          } else if (res.status === "failed") {
            updateJobStatus(res.job_id, "failed");
          }
        });
        const successful = result.results.filter(
          (r) => r.status === "done" || r.status === "pending" || r.status === "already_generated"
        ).length;
        setSuccessMessage(successful + " resume(s) tailored successfully");
      }

      queueJobIds.forEach((id) => {
        if (!processedIds.has(id) && jobStatuses[id] === "processing") {
          updateJobStatus(id, "failed");
        }
      });
    } catch (e) {
      console.error("Auto-generate error:", e);
      const errMsg =
        e?.response?.data?.detail ||
        e?.response?.data?.error ||
        e?.response?.data?.message ||
        e?.message ||
        `Server error (${e?.response?.status || 'unknown'})`;
      setError(errMsg);
      queueJobIds.forEach((id) => {
        if (jobStatuses[id] === "processing") {
          updateJobStatus(id, "failed");
        }
      });
    } finally {
      setProcessing(false);
    }
  };

  const onAutoApply = async () => {
    if (!queueJobIds.length) return;
    setError(null);
    setSuccessMessage(null);
    setProcessing(true);

    queueJobIds.forEach((id) => updateJobStatus(id, "generating_resume"));

    try {
      const response = await jobApi.autoApplyQueue(queueJobIds, null);
      const result = response.data;
      const processedIds = new Set();

      if (result.results) {
        result.results.forEach((res) => {
          processedIds.add(res.job_id);
          if (res.status === "applied") {
            updateJobStatus(res.job_id, "done");
          } else if (res.status === "pending_confirmation") {
            updateJobStatus(res.job_id, "pending_confirmation");
          } else if (res.status === "already_applied") {
            updateJobStatus(res.job_id, "done");
          } else if (res.status === "processing") {
            updateJobStatus(res.job_id, "applying");
          } else if (res.status === "failed") {
            updateJobStatus(res.job_id, "failed");
          }
        });

        const successful = result.results.filter(
          (r) => r.status === "applied" || r.status === "already_applied"
        ).length;
        const pending = result.results.filter((r) => r.status === "pending_confirmation").length;
        const failed = result.results.filter((r) => r.status === "failed");
        setSuccessMessage(
          successful + " job(s) auto-applied successfully" +
            (pending ? "; " + pending + " submission(s) need confirmation" : "") +
            (failed.length ? "; " + failed.length + " failed" : "")
        );
        if (failed.length) {
          setError(failed[0].message || "One or more applications could not be submitted.");
        }
      }

      queueJobIds.forEach((id) => {
        if (!processedIds.has(id) && (jobStatuses[id] === "generating_resume" || jobStatuses[id] === "applying")) {
          updateJobStatus(id, "failed");
        }
      });
    } catch (e) {
      console.error("Auto-apply error:", e);
      const errMsg =
        e?.response?.data?.detail ||
        e?.response?.data?.error ||
        e?.response?.data?.message ||
        e?.message ||
        `Server error (${e?.response?.status || 'unknown'})`;
      setError(errMsg);
      queueJobIds.forEach((id) => {
        if (jobStatuses[id] === "generating_resume" || jobStatuses[id] === "applying") {
          updateJobStatus(
            id,
            e?.response?.status === 400 &&
              String(e?.response?.data?.detail || "").toLowerCase().includes("limit")
              ? "limit_reached"
              : "failed"
          );
        }
      });
    } finally {
      setProcessing(false);
    }
  };

  const getStatusIcon = (jobId) => {
    const status = jobStatuses[jobId];

    switch (status) {
      case "processing":
      case "generating_resume":
      case "applying":
        return <Loader2 className="w-3 h-3 text-yellow-400 animate-spin" />;
      case "done":
        return <CheckCircle className="w-3 h-3 text-green-400" />;
      case "failed":
      case "limit_reached":
        return <AlertCircle className="w-3 h-3 text-red-400" />;
      case "pending_confirmation":
        return <AlertCircle className="w-3 h-3 text-yellow-400" />;
      default:
        return <Clock className="w-3 h-3 text-gray-500" />;
    }
  };

  const getStatusColor = (jobId) => {
    const status = jobStatuses[jobId];
    switch (status) {
      case "processing":
      case "generating_resume":
      case "applying":
        return "border-yellow-500/50";
      case "done":
        return "border-green-500/50";
      case "failed":
      case "limit_reached":
        return "border-red-500/50";
      case "pending_confirmation":
        return "border-yellow-500/50";
      default:
        return "border-gray-800";
    }
  };

  const isAnyProcessing = Object.values(jobStatuses).some(
    (s) => ["processing", "generating_resume", "applying"].includes(s)
  );

  return (
    <div className={"w-full " + className}>
      <aside className="bg-black/60 dark:bg-gray-800/60 rounded-lg border border-gray-200/60 dark:border-gray-700 p-4 h-[calc(100vh-6rem)] flex flex-col">
        <div className="flex items-center justify-between gap-3 flex-none">
          <div className="flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-teal-400" />
            <h3 className="text-white font-semibold">{sidebarTitle}</h3>
          </div>
          {queueJobIds.length > 0 && (
            <button
              onClick={clearQueue}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-300 transition-colors"
              title="Clear queue"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-auto pr-1 min-h-0">
          {queueJobs.length === 0 ? (
            <p className="text-xs text-gray-400 mt-4">No jobs in queue. Use Add to queue.</p>
          ) : (
            <div className="flex flex-col gap-2 pt-4">
              {queueJobs.map((job) => (
                <div
                  key={job.id}
                  className={
                    "flex items-center gap-3 p-2 rounded-lg bg-black dark:bg-gray-900 border " +
                    getStatusColor(job.id)
                  }
                >
                  <div className="shrink-0 relative">
                    {job.company_logo ? (
                      <img
                        src={job.company_logo}
                        alt={job.company}
                        className="w-8 h-8 rounded-lg object-contain bg-blue-950 dark:bg-gray-700 p-1"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-lg bg-linear-to-br from-teal-100 to-blue-100 dark:from-teal-900/30 dark:to-blue-900/30 flex items-center justify-center text-lg font-bold text-teal-600 dark:text-teal-400">
                        {job.company?.charAt(0) || "?"}
                      </div>
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-[12px] font-medium text-white truncate max-w-35">
                      {job.title}
                    </p>
                    <p className="text-[10px] text-gray-400 truncate max-w-30">
                      {job.company}
                    </p>
                   
                  </div>

                  <button
                    onClick={() => removeJobFromQueue(job.id)}
                    className="p-1 rounded hover:bg-gray-800 text-gray-300 shrink-0"
                    title="Remove from queue"
                    disabled={isAnyProcessing}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <div title={jobStatuses[job.id] || "queued"}>{getStatusIcon(job.id)}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-auto pt-4">
          <div className="mt-3 flex items-center justify-between text-[11px] text-gray-400">
            <span>{queueJobIds.length || 0} selected</span>
            <span>Tailor and Queue</span>
          </div>

          <div className="space-y-2">
            <button
              onClick={onAutoGenerate}
              disabled={queueJobIds.length === 0 || isAnyProcessing}
              className={
                "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors " +
                (queueJobIds.length === 0
                  ? "bg-gray-700 text-gray-300 cursor-not-allowed"
                  : isAnyProcessing
                  ? "bg-teal-900/40 text-teal-200 cursor-not-allowed"
                  : "bg-teal-600 hover:bg-teal-700 text-white")
              }
              title="Auto-generate tailored resumes for all queued jobs"
            >
              {isAnyProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              {isAnyProcessing
                ? "Processing..."
                : "Auto Generate Resume" +
                  (queueJobIds.length ? " (" + queueJobIds.length + ")" : "")}
            </button>

            <button
              onClick={onAutoApply}
              disabled={queueJobIds.length === 0 || isAnyProcessing}
              className={
                "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors " +
                (queueJobIds.length === 0
                  ? "bg-orange-700 text-orange-200 cursor-not-allowed"
                  : isAnyProcessing
                  ? "bg-orange-900/40 text-orange-200 cursor-not-allowed"
                  : "bg-orange-600 hover:bg-orange-700 text-white")
              }
              title="Generate a tailored resume and auto-apply to all queued jobs"
            >
              {isAnyProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              {isAnyProcessing
                ? "Applying..."
                : "Auto Apply Jobs" +
                  (queueJobIds.length ? " (" + queueJobIds.length + ")" : "")}
            </button>
          </div>

          {successMessage && (
            <p className="mt-2 text-xs text-green-400 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {successMessage}
            </p>
          )}
          {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
        </div>
      </aside>
    </div>
  );
};

export default Addtoqueue;

// frontend/src/components/jobs/JobScout.jsx

import React, { useState, useEffect } from "react";
import {
  Search,
  MapPin,
  DollarSign,
  SlidersHorizontal,
  Briefcase,
  Clock,
  TrendingUp,
  CheckCircle,
  XCircle,
  Play,
  Pause,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Star,
  StarOff,
  ExternalLink,
  Filter,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useQueue } from "../../contexts/QueueContext";
import { jobApi } from "../../services/jobApi";
import { toast } from "react-hot-toast";

// Import sub-components
import JobFilters from "./JobFilters";
import DiscoverModal from "./DiscoverModal";
import JobStats from "./JobStats";
import JobCard from "./JobCard";
import JobList from "./JobList";
import AutoApplyControl from "./AutoApplyControl";
import QueueStatus from "./QueueStatus";
import Addtoqueue from "./Addtoqueue";

const JobScout = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    location: "All Locations",
    salary: "Any Salary",
    sort: "AI Matched",
    minScore: 0,
    source: "All Sources",
    remoteOnly: false,
    savedOnly: false,

    preferred_job_title: "",
    preferred_job_location: "",
  });
  const [stats, setStats] = useState({
    total: 0,
    saved: 0,
    applied: 0,
    matched: 0,
    queueProgress: 0,
  });
  const [selectedJob, setSelectedJob] = useState(null);
  const [viewMode, setViewMode] = useState("list"); // list | grid
  const [applying, setApplying] = useState({});
  const { queueJobIds, toggleJob: toggleQueueJob, clearQueue } = useQueue();

  // Load jobs on mount and filter change
  useEffect(() => {
    loadJobs(1, false);
    loadStats();
  }, [filters]);

  const loadJobs = async (pageNum = 1, append = false) => {
    if (!append) setLoading(true);
    else setLoadingMore(true);

    try {
      // Build params dynamically — only include filters that are actually active
      const params = {};

      if (filters.search) params.search = filters.search;
      if (filters.location !== "All Locations")
        params.location = filters.location;
      if (filters.minScore > 0) params.min_score = filters.minScore;
      if (filters.source !== "All Sources") params.source = filters.source;
      if (filters.remoteOnly) params.is_remote = "true";
      if (filters.savedOnly) params.is_saved = "true";

      params.ordering =
        filters.sort === "AI Matched" ? "-match_score" : "-created_at";
      params.page = pageNum;
      params.page_size = 12;

      const response = await jobApi.getAll(params);
      const nextJobs = response.data.results || [];
      const totalCount = Number(response.data.count || 0);
      const hasNextFromBackend = Boolean(response.data.next);
      const hasMoreByCount = totalCount > pageNum * params.page_size;

      setJobs((prevJobs) => (append ? [...prevJobs, ...nextJobs] : nextJobs));
      setHasMore(hasNextFromBackend || hasMoreByCount);
      setPage(pageNum);
    } catch (error) {
      console.error("Failed to load jobs:", error);
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleViewMore = () => {
    if (!hasMore || loadingMore) return;
    loadJobs(page + 1, true);
  };

  const loadStats = async () => {
    try {
      const response = await jobApi.getStats();
      setStats(response.data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const [discoverModalOpen, setDiscoverModalOpen] = useState(false);
  const [modalJobTitles, setModalJobTitles] = useState([]);
  const [modalJobLocations, setModalJobLocations] = useState([]);

  const handleOpenDiscoverModal = () => {
    const rawTitles = (filters.preferred_job_title || "").trim();
    const rawLocations = (filters.preferred_job_location || "").trim();

    const jobTitles = rawTitles
      ? rawTitles
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      : ["Software Engineer"];

    const jobLocations = rawLocations
      ? rawLocations
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      : ["Remote"];

    setModalJobTitles(jobTitles);
    setModalJobLocations(jobLocations);
    setDiscoverModalOpen(true);
  };

  const handleDiscover = async () => {
    setDiscoverModalOpen(false);
    setDiscovering(true);
    try {
      console.log(modalJobLocations, modalJobTitles);
      const response = await jobApi.discover({
        job_titles: modalJobTitles,
        location: modalJobLocations[0] || "Remote",
        max_jobs: 50,
        sources: ["apify_linkedin", "apify_indeed", "apify_naukri"],
      });
      toast.success(`Found ${response.data.jobs_found} new jobs!`);
      loadJobs();
      loadStats();
    } catch (error) {
      toast.error("Failed to discover jobs");
    } finally {
      setDiscovering(false);
    }
  };

  const handleApply = async (jobId) => {
    setApplying((prev) => ({ ...prev, [jobId]: true }));
    try {
      await jobApi.apply(jobId);
      toast.success("Application submitted successfully!");
      loadJobs();
      loadStats();
    } catch (error) {
      toast.error("Failed to apply");
    } finally {
      setApplying((prev) => ({ ...prev, [jobId]: false }));
    }
  };

  const handleSave = async (jobId, isSaved) => {
    try {
      if (isSaved) {
        await jobApi.unsave(jobId);
        toast.success("Job removed from saved list");
      } else {
        await jobApi.save(jobId);
        toast.success("Job saved!");
      }
      loadJobs();
      loadStats();
    } catch (error) {
      toast.error("Failed to save job");
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-black dark:bg-gray-900">
      {/* Header */}

      {/* Main two-column layout: left content + right queue sidebar */}
      <div className="max-w-auto mx-auto px-4 py-2 lg:py-3 pb-16 lg:pb-4 overflow-visible">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left column: filters + stats + job list */}
          <div className="lg:col-span-9 w-full">
            <div className="bg-black dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 lg:sticky lg:top-0 lg:z-5">
              <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-2 py-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <Briefcase className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                    <h1 className="text-2xl font-bold text-white dark:text-white">
                      Job Scout
                    </h1>
                    <span className="text-sm text-white dark:text-gray-400">
                      {stats.total.toLocaleString()} roles available
                    </span>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={handleOpenDiscoverModal}
                      disabled={discovering}
                      className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      {discovering ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Discovering...
                        </>
                      ) : (
                        <>
                          <Search className="w-4 h-4" />
                          Discover Jobs
                        </>
                      )}
                    </button>
                  </div>

                  <div className="py-5">
                    <JobFilters
                      filters={filters}
                      onFilterChange={handleFilterChange}
                      onViewModeChange={setViewMode}
                      viewMode={viewMode}
                    />
                  </div>

                  {/* Stats & Controls */}
                  <div className="py-2 w-full">
                    <div >
                      <JobStats stats={stats} />
                    </div>

                    {/* Queue Status */}
                    <div className="py-2">
                      <QueueStatus
                        progress={stats.queueProgress || 0}
                        queued={stats.pending || 0}
                        applied={stats.applied || 0}
                      />
                    </div>

                    {/* Job list */}
                    <div className="pt-2">
                      <JobList
                        jobs={jobs}
                        loading={loading}
                        viewMode={viewMode}
                        onApply={handleApply}
                        onSave={handleSave}
                        applying={applying}
                        selectedJob={selectedJob}
                        onSelectJob={setSelectedJob}
                        queueJobIds={queueJobIds}
                        onToggleQueueJob={toggleQueueJob}
                      />

                      {!loading && jobs.length > 0 && (
                        <div className="mt-4 flex justify-center">
                          {hasMore ? (
                            <button
                              onClick={handleViewMore}
                              disabled={loadingMore}
                              className="px-5 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-medium disabled:opacity-50"
                            >
                              {loadingMore ? "Loading..." : "View more"}
                            </button>
                          ) : (
                            <div className="px-4 py-2 text-sm text-gray-400 dark:text-gray-500">
                              No more jobs
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                   </div>
              </div>
            </div>
          </div>

{/* Right column: queue sidebar */}
                  <div className="lg:col-span-3">
                    <div className="lg:sticky lg:top-2">
                      <Addtoqueue
                        jobs={jobs}
                      />
                    </div>
                  </div>
               
        </div>
      </div>

      {/* Discover Modal */}
      <DiscoverModal
        open={discoverModalOpen}
        onClose={() => setDiscoverModalOpen(false)}
        preferredJobTitles={modalJobTitles}
        setPreferredJobTitles={setModalJobTitles}
        preferredJobLocations={modalJobLocations}
        setPreferredJobLocations={setModalJobLocations}
        onDiscover={handleDiscover}
        discovering={discovering}
      />
    </div>
  );
};

export default JobScout;

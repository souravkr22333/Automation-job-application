// frontend/src/components/jobs/JobCard.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 

  Building2, 
  MapPin, 
  DollarSign, 
  Clock, 
  ExternalLink,
  Star,
  StarOff,
  CheckCircle,
  Play,
  TrendingUp,
  Briefcase
} from 'lucide-react';

const JobCard = ({ 
  job, 
  onApply, 
  onSave, 
  applying, 
  selected,
  onSelect,
  viewMode,
  inQueue,
  onToggleQueue,
  queueIds = [],
  onToggleQueue: onToggleQueueProp,
}) => {
  const effectiveToggle = onToggleQueue ?? onToggleQueueProp;

  const _inQueue = (queueIds || []).includes(job.id);

  const [expanded, setExpanded] = useState(false);

  const getNumericMatchScore = (score) => {
    const parsed = Number(score);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const getMatchColor = (score) => {
    const numericScore = getNumericMatchScore(score);
    if (numericScore == null) return 'text-gray-600 dark:text-gray-400';
    if (numericScore >= 80) return 'text-green-600 dark:text-green-400';
    if (numericScore >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getMatchBg = (score) => {
    const numericScore = getNumericMatchScore(score);
    if (numericScore == null) return 'bg-gray-100 dark:bg-gray-800/60';
    if (numericScore >= 80) return 'bg-green-100 dark:bg-green-900/30';
    if (numericScore >= 60) return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-red-100 dark:bg-red-900/30';
  };

  const getSourceColor = (source) => {
    const colors = {
      linkedin: 'text-blue-600 dark:text-blue-400',
      indeed: 'text-purple-600 dark:text-purple-400',
      glassdoor: 'text-teal-600 dark:text-teal-400',
      google: 'text-red-600 dark:text-red-400'
    };
    return colors[source?.toLowerCase()] || 'text-gray-600 dark:text-gray-400';
  };

  const getSourceIcon = (source) => {
    const icons = {
      linkedin: 'in',
      indeed: 'id',
      glassdoor: 'gd',
      google: 'go'
    };
    return icons[source?.toLowerCase()] || '📌';
  };

  return (
    <div 
      className={`
        bg-black dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 
        hover:shadow-md transition-all duration-200 cursor-pointer
        ${selected ? 'ring-2 ring-teal-500' : ''}
        ${viewMode === 'grid' ? 'p-2' : 'p-2 hover:border-teal-300'}
      `}
      onClick={() => {
              // keep existing selection callback (used by JobScout state)
              onSelect && onSelect(job.id);
              // navigate to dedicated job detail page
              if (job?.id) window.location.href = `/jobs/${job.id}`;
            }}
    >
      <div className="flex flex-wrap items-start gap-3">
        {/* Company Logo */}
        <div className="`flex-shrink-0`">
          {job.company_logo ? (
            <img 
              src={job.company_logo} 
              alt={job.company}
              className="w-12 h-12 rounded-lg object-contain bg-blue-950 dark:bg-gray-700 p-1"
            />
          ) : (
            <div className="w-12 h-12 rounded-lg bg-blue-950 `bg-gradient-to-br` from-teal-100 to-blue-100 dark:from-teal-900/30 dark:to-blue-900/30 flex items-center justify-center text-lg font-bold text-teal-600 dark:text-teal-400">
              {job.company?.charAt(0) || '?'}
            </div>
          )}
        </div>

        {/* Job Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-white-500 text-[15px]  dark:text-white truncate max-w-100">
                {job.title}
              </h3>
              <p className="text-[11px] text-white dark:text-gray-400 flex items-center gap-1 ">
                <Building2 className="w-3.5 h-3.5" />
                <span className='truncate max-w-80'>{job.company}</span>
                {job.tailored_resume?.supabase_url && (
                  <span
                    className="inline-flex items-center gap-1 text-green-500 dark:text-green-400"
                    title="Tailored resume generated"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                  </span>
                )}
              </p>
              
            </div>

            {/* Match Score */}
            {(() => {
              const matchScore = getNumericMatchScore(job?.match_score);
              if (matchScore == null) return null;

              return (
                <div className={`shrink-0 px-3 py-1 rounded-full text-sm font-medium ${getMatchBg(matchScore)} ${getMatchColor(matchScore)}`}>
                  {Math.round(matchScore)}%
                </div>
              );
            })()}
          </div>

          {/* Location & Details */}
          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-white dark:text-gray-400">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {job.location || 'Remote'}
            </span>
            {job.salary && (
              <span className="flex items-center gap-1">
                <DollarSign className="w-3.5 h-3.5" />
                {job.salary}
              </span>
            )}
            {job.posted_date && (
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {job.posted_date}
              </span>
            )}
            <span className={`flex items-center gap-1 ${getSourceColor(job.source)}`}>
              {job.source_display || job.source || 'Unknown'}
            </span>
          </div>

        </div> 

        {/* Actions */}
        <div className="shrink-0 flex items-center gap-2">
          {/* Add to queue */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleQueue && onToggleQueue(job.id);
            }}
            className={`
              flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold transition-colors
              ${
                _inQueue
                  ? 'bg-yellow-100/20 hover:bg-yellow-100/30 text-yellow-200 border border-yellow-500/30'
                  : 'bg-black hover:bg-gray-900 text-gray-200 border border-gray-700'
              }
            `}
            title={_inQueue ? 'Remove from queue' : 'Add to queue'}
          >
            {_inQueue ? 'Queued' : 'Add to queue'}
          </button>
          {/* Save Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSave(job.id, job.is_saved);
            }}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={job.is_saved ? 'Unsave' : 'Save'}
          >
            {job.is_saved ? (
              <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
            ) : (
              <StarOff className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {/* Apply Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onApply(job.id);
            }}
            disabled={applying || job.is_applied}
            className={`
              flex items-center gap-1 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors
              ${job.is_applied 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 cursor-default'
                : 'bg-teal-600 hover:bg-teal-700 text-white'
              }
              ${applying ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            {job.is_applied ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Applied
              </>
            ) : applying ? (
              'Applying...'
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                Apply Now
              </>
            )}
          </button>

          {/* External Link */}
          {job.apply_url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="View on company site"
            >
              <ExternalLink className="w-4 h-4 text-gray-400" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobCard;


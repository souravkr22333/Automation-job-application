// frontend/src/components/jobs/JobFilters.jsx
import React from 'react';
import { Search, MapPin, DollarSign, SlidersHorizontal, LayoutGrid, List, Filter } from 'lucide-react';

const JobFilters = ({ filters, onFilterChange, onViewModeChange, viewMode }) => {
  const locations = ['All Locations', 'Remote', 'United States', 'New York', 'San Francisco', 'London', 'Berlin', 'Singapore'];
  const salaryRanges = ['Any Salary', '$50k-$80k', '$80k-$110k', '$110k-$150k', '$150k-$200k', '$200k+'];
  const sortOptions = ['AI Matched', 'Newest', 'Oldest', 'Salary: High to Low', 'Salary: Low to High'];
  const sources = ['All Sources', 'LinkedIn', 'Indeed', 'Glassdoor', 'Google Jobs'];

  return (
    <div className="bg-bl dark:bg-gray-800 rounded-xl p-2 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="flex-[1.6] min-w-50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs, companies, or keywords..."
              value={filters.search}
              onChange={(e) => onFilterChange('search', e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-black dark:bg-gray-700 text-white dark:text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Location Filter */}
        <div className="min-w-35">
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filters.location}
              onChange={(e) => onFilterChange('location', e.target.value)}
              className="w-full pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-black dark:bg-gray-700 text-white dark:text-white appearance-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            >
              {locations.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Salary Filter */}
        <div className="min-w-35">
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filters.salary}
              onChange={(e) => onFilterChange('salary', e.target.value)}
              className="w-full pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-black dark:bg-gray-700 text-white dark:text-white appearance-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            >
              {salaryRanges.map(range => (
                <option key={range} value={range}>{range}</option>
              ))}
            </select>
          </div>
        </div>



        {/* Source Filter */}
        <div className="min-w-35">
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filters.source}
              onChange={(e) => onFilterChange('source', e.target.value)}
              className="w-full pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-black dark:bg-gray-700 text-white dark:text-white appearance-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            >
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex gap-1 bg-black dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => onViewModeChange('list')}
            className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-blue-950 dark:bg-gray-600 shadow-sm' : 'hover:bg-gray-20 dark:hover:bg-gray-600'}`}
            title="List View"
          >
            <List className="w-4 h-4 text-white dark:text-gray-300" />
          </button>
          <button
            onClick={() => onViewModeChange('grid')}
            className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-blue-950 dark:bg-white-600 shadow-sm' : 'hover:bg-gray-20 dark:hover:bg-gray-600'}`}
            title="Grid View"
          >
            <LayoutGrid className="w-4 h-4 text-white dark:text-gray-300" />
          </button>
        </div>


       <div className="flex gap-4 items-center">
        {/* Remote Only Toggle */}
        <label className="flex items-center gap-2 text-sm text-white dark:text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.remoteOnly}
            onChange={(e) => onFilterChange('remoteOnly', e.target.checked)}
            className="w-4 h-4 text-teal-600 rounded border-gray-300 focus:ring-teal-500"
          />
          Remote Only
        </label>

        {/* Saved Only Toggle */}
        <label className="flex items-center gap-2 text-sm text-white dark:text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.savedOnly}
            onChange={(e) => onFilterChange('savedOnly', e.target.checked)}
            className="w-4 h-4 text-teal-600 rounded border-gray-300 focus:ring-teal-500"
          />
          Saved Only
        </label>
        </div>
      </div>
    </div>
  );
};

export default JobFilters;
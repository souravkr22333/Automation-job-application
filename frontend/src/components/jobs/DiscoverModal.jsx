import React from 'react';

const DiscoverModal = ({
  open,
  onClose,
  preferredJobTitles,
  preferredJobLocations,
  setPreferredJobTitles,
  setPreferredJobLocations,
  onDiscover,
  discovering,
  titleOptions = [],
  locationOptions = [],
}) => {
  if (!open) return null;

  const defaultTitleOptions = [
    'Software Engineer',
    'Frontend Engineer',
    'Full Stack Developer',
    'Backend Engineer',
    'React Developer',
    'Data Scientist',
    'DevOps Engineer',
  ];

  const defaultLocationOptions = [
    'Remote',
    'United States',
    'New York',
    'San Francisco',
    'London',
    'Berlin',
    'Singapore',
  ];

  const finalTitleOptions = titleOptions.length ? titleOptions : defaultTitleOptions;
  const finalLocationOptions = locationOptions.length ? locationOptions : defaultLocationOptions;

  const parseQuick = (value) =>
    String(value)
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-xl shadow-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white text-lg font-semibold">Discover Jobs</h2>
          <button
            className="px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 text-white border border-gray-700"
            onClick={onClose}
            type="button"
            disabled={discovering}
          >
            Close
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-gray-300">Job Titles (multi-select)</label>

            <input
              className="w-full px-3 py-2 bg-black/50 border border-gray-700 text-white rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Type titles separated by commas (e.g., React Developer, Full Stack)"
              value={preferredJobTitles.join(', ')}
              onChange={(e) => setPreferredJobTitles(parseQuick(e.target.value))}
            />

            <select
              multiple
              className="w-full `min-h-[140px]` px-3 py-2 bg-black/50 border border-gray-700 text-white rounded-lg text-sm focus:outline-none"
              value={preferredJobTitles}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions).map((o) => o.value);
                setPreferredJobTitles(values);
              }}
            >
              {finalTitleOptions.map((t) => (
                <option key={t} value={t} className="bg-gray-900">
                  {t}
                </option>
              ))}
            </select>

            <div className="text-xs text-gray-500">Tip: type custom titles in the input (comma-separated).</div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-gray-300">Job Locations (multi-select)</label>

            <input
              className="w-full px-3 py-2 bg-black/50 border border-gray-700 text-white rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Type locations separated by commas (e.g., Remote, London)"
              value={preferredJobLocations.join(', ')}
              onChange={(e) => setPreferredJobLocations(parseQuick(e.target.value))}
            />

            <select
              multiple
              className="w-full `min-h-[140px]` px-3 py-2 bg-black/50 border border-gray-700 text-white rounded-lg text-sm focus:outline-none"
              value={preferredJobLocations}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions).map((o) => o.value);
                setPreferredJobLocations(values);
              }}
            >
              {finalLocationOptions.map((l) => (
                <option key={l} value={l} className="bg-gray-900">
                  {l}
                </option>
              ))}
            </select>

            <div className="text-xs text-gray-500">Tip: type custom locations in the input (comma-separated).</div>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-5">
          <button
            className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white"
            onClick={onClose}
            type="button"
            disabled={discovering}
          >
            Cancel
          </button>

          <button
            className="px-4 py-2 rounded bg-teal-600 hover:bg-teal-700 text-white font-medium transition-colors disabled:opacity-50"
            onClick={onDiscover}
            type="button"
            disabled={
              discovering || preferredJobTitles.length === 0 || preferredJobLocations.length === 0
            }
          >
            {discovering ? 'Discovering...' : 'Discover'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DiscoverModal;


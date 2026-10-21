import React, { useState } from 'react';
import ApplicationKanban from './ApplicationKanban';
import ApplicationTable from './ApplicationTable';

const Applications = () => {
  const [view, setView] = useState('kanban');

  return (
    <div className="space-y-6 pt-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Applications</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView('kanban')}
            className={`px-4 py-2 rounded-lg transition ${
              view === 'kanban'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Kanban
          </button>
          <button
            onClick={() => setView('table')}
            className={`px-4 py-2 rounded-lg transition ${
              view === 'table'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Table
          </button>
        </div>
      </div>

      {view === 'kanban' ? <ApplicationKanban /> : <ApplicationTable />}
    </div>
  );
};

export default Applications;
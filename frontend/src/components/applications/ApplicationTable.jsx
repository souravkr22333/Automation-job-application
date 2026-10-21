import React, { useState } from 'react';
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

const ApplicationTable = () => {
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  
  const [applications] = useState([
    { id: 1, company: 'Stripe', position: 'Senior React Engineer', status: 'Applied', date: '2024-01-15', atsScore: 94 },
    { id: 2, company: 'Vercel', position: 'DX Engineer', status: 'Applied', date: '2024-01-14', atsScore: 87 },
    { id: 3, company: 'Google', position: 'Frontend Developer', status: 'Reviewing', date: '2024-01-13', atsScore: 76 },
    { id: 4, company: 'Meta', position: 'UI Engineer', status: 'Interviewing', date: '2024-01-12', atsScore: 82 },
    { id: 5, company: 'Amazon', position: 'Frontend Lead', status: 'Offered', date: '2024-01-10', atsScore: 91 },
  ]);

  const getStatusColor = (status) => {
    const colors = {
      'Applied': 'bg-blue-100 text-blue-700',
      'Reviewing': 'bg-yellow-100 text-yellow-700',
      'Interviewing': 'bg-purple-100 text-purple-700',
      'Offered': 'bg-green-100 text-green-700',
      'Rejected': 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const sortData = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedApplications = [...applications].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  return (
    <div className="bg-black-700 rounded-xl shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-black-800">
            <tr>
              {['Company', 'Position', 'Status', 'Date', 'ATS Score', 'Actions'].map((header) => (
                <th key={header} className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedApplications.map((app) => (
              <tr key={app.id} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium text-white">{app.company}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                  {app.position}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(app.status)}`}>
                    {app.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                  {app.date}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${app.atsScore}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-700">{app.atsScore}%</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ApplicationTable;
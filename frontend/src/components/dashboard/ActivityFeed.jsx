import React from 'react';

const ActivityFeed = ({ activities }) => {
  const getActivityIcon = (type) => {
    switch (type) {
      case 'search':
        return '🔍';
      case 'parse':
        return '📄';
      case 'tailor':
        return '✏️';
      case 'submit':
        return '✅';
      default:
        return '📌';
    }
  };

  return (
    <div className="space-y-3">
      {activities.map((activity) => (
        <div key={activity.id} className="flex items-start space-x-3 p-3 bg-black-600 border-gray-50 rounded-lg">
          <span className="text-xl">{getActivityIcon(activity.type)}</span>
          <div className="flex-1">
            <p className="text-sm text-white">{activity.message}</p>
            <p className="text-xs text-white mt-1">{activity.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ActivityFeed;
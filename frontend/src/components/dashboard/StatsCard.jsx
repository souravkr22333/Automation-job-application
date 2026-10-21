import React from 'react';

const StatsCard = ({  title, value, change , applications }) => {
  return (
    <div className={`bg-[#111111] border border-[#2A2A2A] rounded-xl p-6`}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-white">{title}</p>
        <span className={`text-sm font-semibold ${
          change.startsWith('+') ? 'text-green-600' : 'text-red-600'
        }`}>
          {change}
        </span>
      </div>
      <h3 className="text-2xl font-bold text-white mt-4">{value}</h3>
      <p>{applications}</p>
      
    </div>
  );
};

export default StatsCard;
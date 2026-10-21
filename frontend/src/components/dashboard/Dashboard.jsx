import React, { useState } from "react";
import StatsCard from "./StatsCard";
import ActivityFeed from "./ActivityFeed";
import {
  BriefcaseIcon,
  CalendarIcon,
  CheckBadgeIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

const Dashboard = () => {
  const [stats] = useState({
    applied: 142,
    interviewing: 8,
    offers: 2,
    atsScore: 84,
  });

  const [activities] = useState([
    {
      id: 1,
      message: 'Searching LinkedIn for "Senior React Engineer"...',
      time: "2 min ago",
      type: "search",
    },
    {
      id: 2,
      message: "Parsing job description for Stripe — Staff Engineer",
      time: "15 min ago",
      type: "parse",
    },
    {
      id: 3,
      message: "Tailoring resume for Vercel — DX Engineer",
      time: "1 hour ago",
      type: "tailor",
    },
    {
      id: 4,
      message: "Submitted application to Google — Frontend Developer",
      time: "3 hours ago",
      type: "submit",
    },
  ]);

  return (
    <div className="space-y-6 bg-black text-white p-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <div className="text-sm text-gray-600">
          <span className="font-semibold">281,204</span> applications processed
          this month
        </div>
      </div>

     <div className="grid grid-cols-2  gap-4">
           
        <StatsCard
          
          title="This Week"
          value={stats.applied}
          change="+12%"
          applications="applications"
          
        />
        <StatsCard
          
          title="This Month"
          value={stats.interviewing}
          change="+3"
          applications="applications"
          
        />


     </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
         
          title="Applied"
          value={stats.applied}
          change="+12%"
          
        />
        <StatsCard
           
          title="Interviewing"
          value={stats.interviewing}
          change="+3%"
          
        />
        <StatsCard

          title="Offers"
          value={stats.offers}
          change="+1%"
          
        />
        <StatsCard
          
          title="ATS Score"
          value={`${stats.atsScore}%`}
          change="+5%"
          
        />
      </div>

      {/* Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 bg-black ">
        <div className="lg:col-span-2">
          <div className="bg-black-600 rounded-xl shadow-md p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              AI Live Feed
            </h2>
            <ActivityFeed activities={activities} />
          </div>
        </div>
        <div className="lg:col-span-1">
          <div className="bg-black-600 rounded-xl shadow-md p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              Quick Actions
            </h2>
            <div className="space-y-3">
              <button className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition">
                Start Auto-Apply
              </button>
              <button className="w-full border border-gray-300 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-50 transition">
                View Applications
              </button>
              <button className="w-full border border-gray-300 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-50 transition">
                Upload Resume
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;



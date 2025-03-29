"use client";

import { useState } from "react";
import Link from "next/link";
import { BellIcon, GlobeAltIcon, RssIcon } from "@heroicons/react/24/outline";

// Mock data for demonstration
const alerts = [
  {
    id: 1,
    query: "Tell me when OpenAI updates their research page",
    target: "https://openai.com/research/",
    type: "website",
    lastChecked: "2024-03-29T10:00:00Z",
    status: "active",
  },
  {
    id: 2,
    query: "Notify me about new GPT-4 papers",
    target: "https://arxiv.org/list/cs.AI/recent",
    type: "rss",
    lastChecked: "2024-03-29T09:30:00Z",
    status: "active",
  },
];

export default function AlertsPage() {
  const [activeAlerts, setActiveAlerts] = useState(alerts);

  const handleDelete = (id: number) => {
    setActiveAlerts(activeAlerts.filter((alert) => alert.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Alerts</h1>
        <Link
          href="/alerts/new"
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
        >
          New Alert
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {activeAlerts.map((alert) => (
          <div
            key={alert.id}
            className="bg-white shadow rounded-lg p-6 space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {alert.type === "website" && (
                  <GlobeAltIcon className="h-5 w-5 text-gray-400" />
                )}
                {alert.type === "rss" && (
                  <RssIcon className="h-5 w-5 text-gray-400" />
                )}
                <h3 className="text-lg font-medium text-gray-900">
                  {alert.query}
                </h3>
              </div>
              <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                {alert.status}
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Monitoring:{" "}
              <a
                href={alert.target}
                className="text-indigo-600 hover:text-indigo-500"
              >
                {alert.target}
              </a>
            </p>
            <div className="flex items-center text-sm text-gray-500">
              <BellIcon className="h-4 w-4 mr-1" />
              Last checked: {new Date(alert.lastChecked).toLocaleString()}
            </div>
            <div className="flex justify-end space-x-2">
              <Link
                href={`/alerts/${alert.id}/edit`}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Edit
              </Link>
              <button
                onClick={() => handleDelete(alert.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {activeAlerts.length === 0 && (
        <div className="text-center py-12">
          <h3 className="mt-2 text-sm font-semibold text-gray-900">
            No alerts
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new alert.
          </p>
          <div className="mt-6">
            <Link
              href="/alerts/new"
              className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Create Alert
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useMemo } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const ExecutiveView: React.FC = () => {
  const [target, setTarget] = useState(48000000);

  const requiredInventory = useMemo(() => (target * 0.18) / 1000000, [target]);
  const holdingCostDelta = useMemo(() => {
    const delta = (target - 48000000) * 0.003;
    const sign = delta >= 0 ? '+' : '-';
    return sign + '$' + Math.abs(delta / 1000).toFixed(0) + 'K';
  }, [target]);
  const projServiceLevel = useMemo(() => {
    const level = 94 + (target - 30000000) / 5000000 * 0.3;
    return Math.min(99.5, level).toFixed(1) + '%';
  }, [target]);

  const chartData = useMemo(() => {
    const data = [];
    for (let t = 30000000; t <= 80000000; t += 5000000) {
      const serviceLevel = Math.min(99.5, 94 + (t - 30000000) / 5000000 * 0.3);
      data.push({ target: t, serviceLevel });
    }
    return data;
  }, []);

  const distributorData = useMemo(() => [
    { name: 'Sydney', all: 58, t1: 72 },
    { name: 'Melbourne', all: 45, t1: 61 },
    { name: 'Brisbane', all: 38, t1: 49 },
    { name: 'Perth', all: 51, t1: 65 },
    { name: 'Adelaide', all: 29, t1: 38 }
  ], []);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* KPI Row */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <p className="text-3xl font-bold text-gray-900">42</p>
            <p className="text-sm text-gray-500 mt-1">Network DOS</p>
            <p className="text-xs text-gray-400 mt-0.5">days</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-400">
            <p className="text-3xl font-bold text-gray-900">61%</p>
            <p className="text-sm text-gray-500 mt-1">Credit Utilization</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <p className="text-3xl font-bold text-gray-900">97.4%</p>
            <p className="text-sm text-gray-500 mt-1">Tier 1 Coverage</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
            <p className="text-3xl font-bold text-gray-900">3</p>
            <p className="text-sm text-gray-500 mt-1">On Credit Hold</p>
            <p className="text-xs text-gray-400 mt-0.5">accounts</p>
          </div>
        </div>

        {/* Revenue Target Simulator */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Revenue Target Simulator</h2>
          <div className="mb-4">
            <input
              type="range"
              min="30000000"
              max="80000000"
              step="500000"
              value={target}
              onChange={(e) => setTarget(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <p className="text-3xl font-bold text-center mb-6">${(target / 1000000).toFixed(1)}M</p>
          <div className="grid grid-cols-3 gap-4 mb-6 text-center">
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-lg font-semibold">${requiredInventory.toFixed(1)}M</p>
              <p className="text-sm text-gray-500">Required Inventory</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-lg font-semibold">{holdingCostDelta}</p>
              <p className="text-sm text-gray-500">Holding Cost Delta</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-lg font-semibold">{projServiceLevel}</p>
              <p className="text-sm text-gray-500">Proj. Service Level</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="target"
                tickFormatter={(t) => `$${(t / 1e6).toFixed(0)}M`}
              />
              <YAxis domain={[93, 100]} label={{ value: 'Service Level %', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Line type="monotone" dataKey="serviceLevel" stroke="#2563eb" strokeWidth={2} />
              <ReferenceLine
                x={target}
                stroke="#f59e0b"
                strokeDasharray="4 4"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Network DOS by Distributor */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Network Inventory Health — Days of Supply by Distributor</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={distributorData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Days of Supply', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend verticalAlign="bottom" height={36} />
              <ReferenceLine y={14} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Min 14d', position: 'right' }} />
              <ReferenceLine y={90} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Max 90d', position: 'right' }} />
              <Bar dataKey="all" label="All SKUs" fill="#3b82f6" />
              <Bar dataKey="t1" label="Tier 1" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveView;
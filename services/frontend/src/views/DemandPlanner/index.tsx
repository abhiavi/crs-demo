import React, { useState, useMemo } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const DemandPlannerView: React.FC = () => {
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const exceptions = [
    { sku: 'Solo Lemon 375mL Can 24pk', exType: 'P90 BREACH', model: 'TFT', p50: 452, fva: 1.8 },
    { sku: 'Powerade Mountain Blast 600mL', exType: 'NEGATIVE FVA', model: 'ETS', p50: 218, fva: -6.2 },
    { sku: 'Golden Circle OJ 2L 6pk', exType: 'MODEL RECLASSIFICATION', model: 'ETS->TFT', p50: 891, fva: null },
    { sku: 'V Energy 250mL 24pk', exType: 'P90 BREACH', model: 'SBA', p50: 134, fva: 2.1 },
    { sku: 'Bundaberg Ginger Beer 375mL', exType: 'NEGATIVE FVA', model: 'ARIMA', p50: 67, fva: -3.4 }
  ];

  const forecastData = useMemo(() => {
    const base = 450;
    const data = [];
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const p50 = base + (Math.random() - 0.5) * 20;
      const p10 = p50 * 0.75;
      const p90 = p50 * 1.30;
      const actual = i <= 20 ? p50 * (0.88 + Math.random() * 0.24) : null;
      data.push({
        date,
        p50,
        p10,
        p90,
        actual
      });
    }
    return data;
  }, []);

  const handleSubmitOverride = (sku: string, quantity: number, reason: string) => {
    alert(`Override submitted for ${sku}: ${quantity} units (${reason})`);
    // In real app: submit to API
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Demand Planner Dashboard</h1>

      {/* Exception Triage Grid */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Exception Triage</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Exception Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Model</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">P50 Forecast</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">FVA Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {exceptions.map((exc, index) => (
                <React.Fragment key={index}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{exc.sku}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${exc.exType === 'P90 BREACH' ? 'bg-red-100 text-red-800' : 
                          exc.exType === 'NEGATIVE FVA' ? 'bg-orange-100 text-orange-800' : 
                          'bg-blue-100 text-blue-800'}`}>
                        {exc.exType}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{exc.model}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{exc.p50}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {exc.fva === null ? (
                        <span className="text-gray-500">—</span>
                      ) : (
                        <span className={exc.fva > 0 ? 'text-green-600' : 'text-red-600'}>
                          {exc.fva.toFixed(1)}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setExpandedRow(expandedRow === index ? null : index)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Override
                      </button>
                    </td>
                  </tr>
                  {expandedRow === index && (
                    <tr>
                      <td colSpan="6" className="px-6 py-4">
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <form
                            onSubmit={(e) => {
                              e.preventDefault();
                              const formData = new FormData(e.target as HTMLFormElement);
                              const quantity = parseFloat(formData.get('quantity') as string);
                              const reason = formData.get('reason') as string;
                              handleSubmitOverride(exc.sku, quantity, reason);
                              setExpandedRow(null);
                            }}
                            className="space-y-3"
                          >
                            <div className="flex items-center gap-4">
                              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                Quantity:
                                <input
                                  type="number"
                                  name="quantity"
                                  min={Math.floor(exc.p50 * 0.85)}
                                  max={Math.ceil(exc.p50 * 1.15)}
                                  value={exc.p50}
                                  step="1"
                                  className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  required
                                />
                              </label>
                              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                                Reason:
                                <select
                                  name="reason"
                                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                  <option value="">Select reason</option>
                                  <option value="PROMOTIONAL_UPLIFT">PROMOTIONAL_UPLIFT</option>
                                  <option value="COMPETITOR_DISRUPTION">COMPETITOR_DISRUPTION</option>
                                  <option value="SEASONAL_PRE_BUILD">SEASONAL_PRE_BUILD</option>
                                  <option value="ERRONEOUS_FORECAST">ERRONEOUS_FORECAST</option>
                                </select>
                              </label>
                            </div>
                            <div className="flex justify-end space-x-3">
                              <button
                                type="button"
                                onClick={() => setExpandedRow(null)}
                                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                              >
                                Cancel
                              </button>
                              <button
                                type="submit"
                                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                              >
                                Submit
                              </button>
                            </div>
                          </form>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Forecast Band Chart and TFT Attention Weights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Forecast Band Chart */}
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Forecast Bands — Solo Lemon 375mL (Last 30 Days)</h2>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={4}
                tickFormatter={(date: string) => {
                  const d = new Date(date);
                  return d.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' });
                }}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(date: string) => new Date(date).toLocaleDateString('en-AU', { month: 'short', day: 'numeric' })}
                formatter={(value: number) => [Math.round(value), '']}
              />
              <Legend verticalAlign="top" height={36} />
              <Area type="monotone" dataKey="p90" stroke="#bfdbfe" fillOpacity={0.4} />
              <Area type="monotone" dataKey="p50" stroke="#2563eb" strokeWidth={2} fillOpacity={0} />
              <Area type="monotone" dataKey="p10" stroke="#bfdbfe" fillOpacity={0.4} />
              {forecastData.map((entry, index) => (
                index <= 20 && (
                  <Area
                    key={index}
                    type="monotone"
                    dataKey="actual"
                    stroke="#1e3a8a"
                    strokeWidth={2}
                    fillOpacity={0}
                    dot={{ r: 3, fill: '#1e3a8a' }}
                  />
                )
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* TFT Attention Weights */}
        <div>
          <h2 className="text-xl font-semibold mb-2">TFT Attention Weights — Why this forecast?</h2>
          <p className="text-sm text-gray-500 mb-4">Interpretable self-attention across 52-week history</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Lag Sales W-52', w: 0.31 },
              { name: 'Promo Depth', w: 0.24 },
              { name: 'Day of Week', w: 0.18 },
              { name: 'Weather Index', w: 0.12 },
              { name: 'Lag Sales W-4', w: 0.08 },
              { name: 'Holiday Flag', w: 0.05 },
              { name: 'Price Index', w: 0.02 }
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" interval={0} tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 0.35]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
              <Bar dataKey="w" radius={[0, 4, 4, 0]}>
                {[0.31,0.24,0.18,0.12,0.08,0.05,0.02].map((w, i) => (
                  <Cell key={i} fill={w > 0.2 ? '#1d4ed8' : w > 0.1 ? '#3b82f6' : '#93c5fd'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default DemandPlannerView;
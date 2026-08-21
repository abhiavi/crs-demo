import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

const DistributorView: React.FC = () => {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    sku: '',
    quantity: '',
    reason: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(`Request submitted — pending Demand Planner approval (Ref: REQ-${Date.now()})`);
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const projectedData = useMemo(() => {
    const data = [];
    for (let day = 0; day <= 13; day++) {
      const soloStock = Math.max(0, 1200 - day * 85 + (day >= 3 ? 1440 : 0));
      const powerStock = Math.max(0, 340 - day * 42 + (day >= 4 ? 360 : 0));
      const gcStock = Math.max(0, 180 - day * 28 + (day >= 7 ? 240 : 0));
      data.push({
        day,
        solo: soloStock,
        powerade: powerStock,
        gc: gcStock,
      });
    }
    return data;
  }, []);

  const inTransitData = [
    { id: 'PO-20260819-001', sku: 'Solo Lemon 375mL Can 24pk', qty: 1440, eta: '24 Aug', status: 'IN_TRANSIT', pct: 60 },
    { id: 'PO-20260820-003', sku: 'Powerade Mountain Blast 600mL 12pk', qty: 360, eta: '25 Aug', status: 'RELEASED', pct: 20 },
    { id: 'PO-20260821-007', sku: 'Golden Circle Orange Juice 2L 6pk', qty: 240, eta: '28 Aug', status: 'RELEASED', pct: 20 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header Bar */}
      <div className="bg-blue-700 text-white px-6 py-4 flex justify-between items-center rounded-lg mb-6">
        <div className="font-semibold text-lg">Sydney Beverage Distributors Pty Ltd (DIST-AU-SYD)</div>
        <div className="flex items-center space-x-4">
          <span>Credit: $458K / $750K (61%)</span>
          <div className="relative w-32 h-2 bg-blue-100 rounded-full">
            <div className="bg-yellow-400 h-2 rounded-full" style={{ width: '61%' }}></div>
          </div>
        </div>
      </div>

      {/* In-Transit Shipments */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">In-Transit Shipments</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PO Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ETA</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {inTransitData.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.sku}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.qty}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.eta}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        item.status === 'IN_TRANSIT'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-24 h-2 bg-blue-100 rounded-full">
                      <div
                        className="h-2 bg-blue-500 rounded-full"
                        style={{ width: `${item.pct}%` }}
                      ></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Projected Days of Supply */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Projected Days of Supply — Forward 14 Days</h2>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={projectedData}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <ReferenceLine
              x={3}
              stroke="#2563eb"
              strokeDasharray="4 4"
              label={{ position: 'insideTop', angle: -90, offset: 10, children: 'Solo arrival' }}
            />
            <ReferenceLine
              x={4}
              stroke="#10b981"
              strokeDasharray="4 4"
              label={{ position: 'insideTop', angle: -90, offset: 10, children: 'PWD arrival' }}
            />
            <ReferenceLine
              x={7}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ position: 'insideTop', angle: -90, offset: 10, children: 'GC arrival' }}
            />
            <XAxis dataKey="day" label={{ value: 'Days from Today', position: 'insideBottom', offset: 12, angle: 0 }} />
            <YAxis label={{ value: 'Units on Hand', position: 'insideLeft', offset: -8, angle: -90 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="solo" stroke="#2563eb" />
            <Line type="monotone" dataKey="powerade" stroke="#10b981" />
            <Line type="monotone" dataKey="gc" stroke="#f59e0b" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Adjustment Request */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Adjustment Request</h2>
        {successMessage && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {successMessage}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SKU</label>
              <select
                name="sku"
                value={formData.sku}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select SKU</option>
                <option value="Solo Lemon 375mL Can 24pk">Solo Lemon 375mL Can 24pk</option>
                <option value="Powerade Mountain Blast 600mL 12pk">Powerade Mountain Blast 600mL 12pk</option>
                <option value="Golden Circle Orange Juice 2L 6pk">Golden Circle Orange Juice 2L 6pk</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
            <textarea
              name="reason"
              value={formData.reason}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-700 text-white px-4 py-2 rounded-md hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Submit Request
          </button>
        </form>
      </div>
    </div>
  );
};

export default DistributorView;
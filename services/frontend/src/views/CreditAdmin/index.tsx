import React, { useState } from 'react';

const CreditAdminView: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedDistributor, setSelectedDistributor] = useState<{ name: string; wfId: string } | null>(null);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerTimeout, setBannerTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  const openModal = (distributor: { name: string; wfId: string }) => {
    setSelectedDistributor(distributor);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedDistributor(null);
  };

  const handleConfirmRelease = () => {
    if (selectedDistributor) {
      setBannerMessage(`Credit hold released — orders resuming for ${selectedDistributor.name}`);
      if (bannerTimeout) clearTimeout(bannerTimeout);
      const timeout = setTimeout(() => {
        setBannerMessage(null);
      }, 5000);
      setBannerTimeout(timeout);
    }
    closeModal();
  };

  const formatCurrency = (value: number): string => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    return `$${(value / 1000).toFixed(0)}k`;
  };

  const getUtilizationColor = (util: number): string => {
    if (util < 60) return 'bg-green-500';
    if (util < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStatusBadge = (status: string): { bg: string; text: string } => {
    if (status === 'CREDIT_HOLD') return { bg: 'bg-red-100', text: 'text-red-800' };
    return { bg: 'bg-green-100', text: 'text-green-800' };
  };

  const getTierBadge = (tier: string): { bg: string; text: string } => {
    if (tier.startsWith('T1')) return { bg: 'bg-blue-100', text: 'text-blue-800' };
    if (tier.startsWith('T2')) return { bg: 'bg-gray-100', text: 'text-gray-700' };
    return { bg: 'bg-red-100', text: 'text-red-700' };
  };

  const getCappedStatus = (capped: boolean | string): { label: string; color: string } => {
    if (capped === 'blocked') return { label: 'Blocked', color: 'text-red-600' };
    if (capped === true) return { label: 'Capped', color: 'text-orange-600' };
    return { label: 'Fulfilled', color: 'text-green-600' };
  };

  const creditUtilizationData = [
    { name: 'Sydney Beverage Distributors', limit: 750000, ar: 225000, unbilled: 75000 },
    { name: 'Melbourne Drinks Co', limit: 1200000, ar: 480000, unbilled: 120000 },
    { name: 'Brisbane Refreshments Group', limit: 550000, ar: 385000, unbilled: 55000, status: 'CREDIT_HOLD' },
    { name: 'Perth Liquid Assets', limit: 480000, ar: 192000, unbilled: 48000 },
    { name: 'Adelaide Premium Beverages', limit: 320000, ar: 256000, unbilled: 32000, status: 'CREDIT_HOLD' }
  ];

  const solverResultsData = [
    { sku: 'Solo Lemon 375mL Can 24pk', tier: 'T1 / AX', req: 1440, alloc: 1440, dos: '58d', capped: false },
    { sku: 'Powerade Mountain Blast 600mL', tier: 'T1 / BX', req: 720, alloc: 720, dos: '45d', capped: false },
    { sku: 'Golden Circle OJ 2L 6pk', tier: 'T1 / AY', req: 480, alloc: 480, dos: '52d', capped: false },
    { sku: 'Bundaberg Ginger Beer 375mL', tier: 'T2 / BY', req: 360, alloc: 210, dos: '22d', capped: true },
    { sku: 'V Energy 250mL 24pk', tier: 'T2 / CX', req: 240, alloc: 140, dos: '18d', capped: true },
    { sku: 'Rockstar Xdurance 500mL', tier: 'T3 / AZ', req: 120, alloc: 0, dos: '0d', capped: 'blocked' }
  ];

  const pendingReleases = [
    { name: 'Brisbane Refreshments Group', wfId: 'WF-20260821-BNE-003' },
    { name: 'Adelaide Premium Beverages', wfId: 'WF-20260821-ADL-001' }
  ];

  return (
    <div className="space-y-6 p-4">
      {/* Credit Utilization Table */}
      <div className="border rounded-lg shadow p-4">
        <h2 className="text-xl font-semibold mb-4">Distributor Credit Utilization — Live</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Distributor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Credit Limit</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AR Outstanding</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unbilled Pipeline</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Available</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Utilization</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {creditUtilizationData.map((row) => {
                const available = row.limit - row.ar - row.unbilled;
                const utilization = ((row.ar + row.unbilled) / row.limit) * 100;
                const status = row.status || 'ACTIVE';
                const { bg: statusBg, text: statusText } = getStatusBadge(status);
                return (
                  <tr key={row.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row.limit)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row.ar)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(row.unbilled)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(available)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className={`${getUtilizationColor(utilization)} h-2.5 rounded-full`}
                          style={{ width: `${utilization}%` }}
                        ></div>
                      </div>
                      <span className="mt-1 block text-xs text-gray-500">{utilization.toFixed(0)}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusBg} ${statusText}`}>
                        {status === 'CREDIT_HOLD' ? 'CREDIT HOLD' : 'ACTIVE'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* OR-Tools Solver Results */}
      <div className="border rounded-lg shadow p-4">
        <h2 className="text-xl font-semibold mb-4">Last Fair-Share Allocation — Brisbane Refreshments Group</h2>
        <div className="text-sm text-gray-500 mb-4">
          Run: 2026-08-21 09:14 UTC | Status: OPTIMAL | Min DOS: 18d | Budget: $98,450 / $110,000 | Solver: 347ms
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tier</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ROQ Req.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Allocated</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DOS Proj.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {solverResultsData.map((row) => {
                const { bg: tierBg, text: tierText } = getTierBadge(row.tier);
                const { label: statusLabel, color: statusColor } = getCappedStatus(row.capped);
                return (
                  <tr key={row.sku} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.sku}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${tierBg} ${tierText}`}>
                        {row.tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.req}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.alloc}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.dos}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{statusColor} {statusLabel}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Credit Hold Release Panel */}
      <div className="border rounded-lg shadow p-4">
        <h2 className="text-xl font-semibold mb-4">Accounts Pending Manual Credit Release</h2>
        <div className="space-y-4">
          {pendingReleases.map((dist) => (
            <div key={dist.wfId} className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{dist.name}</p>
                <p className="text-xs text-gray-500">{dist.wfId}</p>
              </div>
              <button
                onClick={() => openModal(dist)}
                className="px-3 py-1.5 text-sm font-medium text-red-600 border border-red-200 rounded hover:bg-red-50"
              >
                Release Hold
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Banner Message */}
      {bannerMessage && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-green-100 border border-green-200 text-green-800 px-4 py-3 rounded shadow-lg z-50">
          {bannerMessage}
        </div>
      )}

      {/* Modal Overlay */}
      {modalOpen && selectedDistributor && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-96 max-w-full p-6">
              <h3 className="text-lg font-semibold mb-4">Confirm Credit Release</h3>
              <p className="mb-6 text-gray-700">
                Inject manual credit release signal into Temporal workflow {selectedDistributor.wfId}? This will immediately resume order generation for {selectedDistributor.name}.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={closeModal}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmRelease}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded"
                >
                  Confirm Release
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default CreditAdminView;
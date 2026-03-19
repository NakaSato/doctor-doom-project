import { useState, useMemo } from 'react';
import { useDefects } from '@/hooks/useQueries';
import { useSelectionStore } from '@/stores/selectionStore';
import { useUIStore } from '@/stores/uiStore';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import type { Defect, Severity } from '@/types';
import { formatDistanceToNow } from 'date-fns';

const columnHelper = createColumnHelper<Defect>();

function DefectLog() {
  const { data: defects = [], isLoading } = useDefects();
  const { setSelectedDefect } = useSelectionStore();
  const { openModal } = useUIStore();
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const columns = useMemo(
    () => [
      columnHelper.accessor('defect_type', {
        header: 'Type',
        cell: (info) => (
          <span className="capitalize">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('severity', {
        header: 'Severity',
        cell: (info) => (
          <span
            className={`badge-${info.getValue()}`}
          >
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('confidence', {
        header: 'Confidence',
        cell: (info) => `${(info.getValue() * 100).toFixed(1)}%`,
      }),
      columnHelper.accessor('temperature_delta', {
        header: 'ΔT (°C)',
        cell: (info) => (
          <span
            className={
              info.getValue() > 20
                ? 'text-red-500 font-bold'
                : info.getValue() > 10
                ? 'text-orange-500'
                : 'text-gray-600 dark:text-gray-400'
            }
          >
            +{info.getValue().toFixed(1)}
          </span>
        ),
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => (
          <span className="capitalize">{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor('detected_at', {
        header: 'Detected',
        cell: (info) =>
          formatDistanceToNow(new Date(info.getValue()), {
            addSuffix: true,
          }),
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: (info) => (
          <button
            onClick={() => {
              setSelectedDefect(info.row.original);
              openModal(<DefectDetailModal defect={info.row.original} />);
            }}
            className="text-primary-500 hover:text-primary-600 text-sm font-medium"
          >
            View
          </button>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data: defects,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      globalFilter: severityFilter,
    },
    onGlobalFilterChange: setSeverityFilter,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin text-4xl">⏳</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Defect Log
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Sortable, filterable table with severity, ΔT, confidence
        </p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-4 flex gap-4">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="detected">Detected</option>
          <option value="reviewed">Reviewed</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>

        <input
          type="text"
          placeholder="Search..."
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          onChange={(e) => table.setGlobalFilter(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id}>
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="card p-4 mt-4 flex justify-between items-center">
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Page {table.getState().pagination.pageIndex + 1} of{' '}
          {table.getPageCount()}
        </span>
        <div className="space-x-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="btn-outline px-4 py-2 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="btn-outline px-4 py-2 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

function DefectDetailModal({ defect }: { defect: Defect }) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Defect Details</h2>
      <dl className="space-y-3">
        <div>
          <dt className="text-sm font-medium text-gray-500">Type</dt>
          <dd className="text-gray-900 dark:text-white capitalize">
            {defect.defect_type}
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-gray-500">Severity</dt>
          <dd>
            <span className={`badge-${defect.severity}`}>{defect.severity}</span>
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-gray-500">Confidence</dt>
          <dd className="text-gray-900 dark:text-white">
            {(defect.confidence * 100).toFixed(1)}%
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-gray-500">Temperature Delta</dt>
          <dd className="text-gray-900 dark:text-white">
            +{defect.temperature_delta.toFixed(1)}°C
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-gray-500">Status</dt>
          <dd className="text-gray-900 dark:text-white capitalize">
            {defect.status}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export default DefectLog;

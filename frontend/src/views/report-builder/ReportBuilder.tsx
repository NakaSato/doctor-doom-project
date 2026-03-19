import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useSites, useInspections, useGenerateReport, useReports } from '@/hooks/useQueries';
import { useUIStore } from '@/stores/uiStore';
import { format } from 'date-fns';

function ReportBuilder() {
  const { data: sites = [] } = useSites();
  const { data: inspections = [] } = useInspections();
  const { data: reports = [] } = useReports();
  const generateReport = useGenerateReport();
  const { addToast } = useUIStore();

  const { register, handleSubmit, watch, formState: { isSubmitting } } = useForm({
    defaultValues: {
      site_id: '',
      inspection_id: '',
      report_type: 'inspection',
      format: 'pdf',
      include_thermal: true,
      include_recommendations: true,
    },
  });

  const selectedSite = watch('site_id');

  const onSubmit = async (data: any) => {
    try {
      await generateReport.mutateAsync({
        siteId: data.site_id,
        inspectionId: data.inspection_id,
        format: data.format,
      });
      addToast({
        type: 'success',
        title: 'Report queued',
        message: 'Your report is being generated',
      });
    } catch {
      addToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to generate report',
      });
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Report Builder
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure, preview, and export IEC 62446-3 compliant PDF reports
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report configuration */}
        <div className="card p-6 lg:col-span-1">
          <h2 className="text-lg font-semibold mb-4">Configuration</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Site</label>
              <select
                {...register('site_id', { required: true })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="">Select a site</option>
                {sites.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Inspection</label>
              <select
                {...register('inspection_id', { required: true })}
                disabled={!selectedSite}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 disabled:opacity-50"
              >
                <option value="">Select an inspection</option>
                {inspections
                  .filter((i) => i.site_id === selectedSite)
                  .map((inspection) => (
                    <option key={inspection.id} value={inspection.id}>
                      {format(new Date(inspection.started_at), 'MMM dd, yyyy')}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Report Type</label>
              <select
                {...register('report_type')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="inspection">Inspection Report</option>
                <option value="summary">Summary Report</option>
                <option value="compliance">IEC 62446-3 Compliance</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Format</label>
              <select
                {...register('format')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="pdf">PDF</option>
                <option value="html">HTML</option>
                <option value="json">JSON</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('include_thermal')}
                  className="w-4 h-4 text-primary-500 rounded"
                />
                <span className="ml-2 text-sm">Include thermal images</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('include_recommendations')}
                  className="w-4 h-4 text-primary-500 rounded"
                />
                <span className="ml-2 text-sm">Include recommendations</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full btn-primary py-2.5 disabled:opacity-50"
            >
              {isSubmitting ? 'Generating...' : 'Generate Report'}
            </button>
          </form>
        </div>

        {/* Recent reports */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Recent Reports</h2>

          {reports.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">No reports yet</p>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div>
                    <p className="font-medium">{report.id}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {report.report_type} • {report.format.toUpperCase()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        report.status === 'completed'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : report.status === 'generating'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                      }`}
                    >
                      {report.status}
                    </span>
                    {report.status === 'completed' && (
                      <button className="btn-outline px-3 py-1 text-sm">
                        Download
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportBuilder;

'use client';

import React, { useState } from 'react';
import { FileUpload } from '@/components/file-upload';
import { DocumentViewer } from '@/components/document-viewer';
import { uploadDocuments, pollJobStatus, UploadJob, getJobStatus } from './api';
import { Loader2 } from 'lucide-react';

// Job type for frontend state
interface Job {
  jobId: string;
  filename: string;
  status: string;
  summary: string;
  markdown: string;
}

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Add or update a job in the jobs array
  const upsertJob = (job: Job) => {
    setJobs(prev => {
      const idx = prev.findIndex(j => j.jobId === job.jobId);
      if (idx !== -1) {
        const updated = [...prev];
        updated[idx] = job;
        return updated;
      }
      return [...prev, job];
    });
  };

  const handleSubmit = async (files: File[], parser: string) => {
    try {
      setIsUploading(true);
      setError(null);
      // Upload files
      const uploadJobs = await uploadDocuments(files, parser);
      // Add jobs to state and start polling
      uploadJobs.forEach(({ job_id, filename }) => {
        const newJob: Job = {
          jobId: job_id,
          filename,
          status: 'pending',
          summary: '',
          markdown: '',
        };
        upsertJob(newJob);
        // Start polling for each job
        pollJobStatus(job_id, (jobStatus) => {
          upsertJob({
            jobId: job_id,
            filename,
            status: jobStatus.status,
            summary: jobStatus.summary,
            markdown: jobStatus.markdown,
          });
        }).catch(error => {
          upsertJob({
            jobId: job_id,
            filename,
            status: 'error',
            summary: '',
            markdown: 'Error checking job status. Please try again.'
          });
        });
      });
      // Select the first job by default
      if (uploadJobs.length > 0) {
        setSelectedJobId(uploadJobs[0].job_id);
      }
    } catch (error) {
      console.error('Error uploading documents:', error);
      setError('Error uploading documents. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Sidebar UI for job history
  const Sidebar = () => (
    <aside className="w-64 bg-secondary border-r min-h-screen p-4 flex flex-col">
      <h2 className="font-bold mb-4">Document History</h2>
      {jobs.length === 0 ? (
        <div className="text-muted-foreground text-sm">No documents yet. Upload to get started.</div>
      ) : (
        <ul className="space-y-2 flex-1 overflow-y-auto">
          {jobs.map(job => (
            <li key={job.jobId}>
              <button
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center justify-between ${selectedJobId === job.jobId ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
                onClick={() => setSelectedJobId(job.jobId)}
              >
                <span className="truncate">{job.filename}</span>
                <span className="ml-2 text-xs capitalize flex items-center gap-1">
                  {['pending', 'processing'].includes(job.status) && <Loader2 className="animate-spin h-4 w-4" />}
                  {job.status}
                </span>
              </button>
              {job.status === 'error' && (
                <div className="text-destructive text-xs mt-1 ml-2">Error processing document</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );

  // Get the selected job
  const selectedJob = jobs.find(j => j.jobId === selectedJobId) || null;

  return (
    <main className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar />
      {/* Main content */}
      <div className="flex-1 pl-8 overflow-y-auto">
        <div className="flex flex-col items-center justify-center mb-10">
          <h1 className="text-4xl font-bold tracking-tight">PDF Document Processor</h1>
          <p className="text-lg text-muted-foreground mt-2">
            Upload PDFs to extract content and generate summaries
          </p>
        </div>
        {jobs.length === 0 ? (
          <FileUpload onSubmit={handleSubmit} isUploading={isUploading} />
        ) : (
          selectedJob && (
            <DocumentViewer
              jobId={selectedJob.jobId}
              status={selectedJob.status}
              markdown={selectedJob.markdown}
              summary={selectedJob.summary}
            />
          )
        )}
        {error && (
          <div className="mt-6 p-4 bg-destructive/10 border border-destructive rounded-lg text-center">
            <p className="text-destructive">{error}</p>
          </div>
        )}
        {jobs.length > 0 && (
          <div className="mt-8 text-center">
            <button
              onClick={() => {
                setJobs([]);
                setSelectedJobId(null);
              }}
              className="text-primary hover:underline"
            >
              Process More Documents
            </button>
          </div>
        )}
      </div>
    </main>
  );
} 
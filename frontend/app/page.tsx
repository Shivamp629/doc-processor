'use client';

import React, { useState } from 'react';
import { FileUpload } from '@/components/file-upload';
import { DocumentViewer } from '@/components/document-viewer';
import { uploadDocuments, pollJobStatus } from './api';

export default function Home() {
  const [isUploading, setIsUploading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [markdown, setMarkdown] = useState<string>('');
  const [summary, setSummary] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (files: File[], parser: string) => {
    try {
      setIsUploading(true);
      setError(null);
      
      // Upload files
      const jobId = await uploadDocuments(files, parser);
      setJobId(jobId);
      setStatus('pending');
      
      // Start polling for status
      pollJobStatus(jobId, (jobStatus) => {
        setStatus(jobStatus.status);
        setMarkdown(jobStatus.markdown);
        setSummary(jobStatus.summary);
      }).catch(error => {
        console.error('Error polling job status:', error);
        setError('Error checking job status. Please try again.');
      });
      
    } catch (error) {
      console.error('Error uploading documents:', error);
      setError('Error uploading documents. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="container py-10">
      <div className="flex flex-col items-center justify-center mb-10">
        <h1 className="text-4xl font-bold tracking-tight">PDF Document Processor</h1>
        <p className="text-lg text-muted-foreground mt-2">
          Upload PDFs to extract content and generate summaries
        </p>
      </div>
      
      {!jobId ? (
        <FileUpload onSubmit={handleSubmit} isUploading={isUploading} />
      ) : (
        <DocumentViewer 
          jobId={jobId}
          status={status}
          markdown={markdown}
          summary={summary}
        />
      )}
      
      {error && (
        <div className="mt-6 p-4 bg-destructive/10 border border-destructive rounded-lg text-center">
          <p className="text-destructive">{error}</p>
        </div>
      )}
      
      {jobId && (
        <div className="mt-8 text-center">
          <button 
            onClick={() => {
              setJobId(null);
              setStatus('');
              setMarkdown('');
              setSummary('');
            }}
            className="text-primary hover:underline"
          >
            Process Another Document
          </button>
        </div>
      )}
    </main>
  );
} 
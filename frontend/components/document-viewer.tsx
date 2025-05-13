import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface DocumentViewerProps {
  jobId: string | null;
  status: string;
  markdown: string;
  summary: string;
}

export function DocumentViewer({ jobId, status, markdown, summary }: DocumentViewerProps) {
  if (!jobId) {
    return null;
  }

  const getStatusPercentage = () => {
    switch (status) {
      case 'pending':
        return 25;
      case 'processing':
        return 50;
      case 'done':
        return 100;
      case 'error':
        return 100;
      default:
        return 0;
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'pending':
        return 'Pending - Waiting for processing';
      case 'processing':
        return 'Processing - Converting document';
      case 'done':
        return 'Complete - Document processed successfully';
      case 'error':
        return 'Error - Document processing failed';
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="space-y-6 w-full max-w-4xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Document Processing Status</CardTitle>
          <CardDescription>Job ID: {jobId}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm font-medium">
              <span>{getStatusLabel()}</span>
              <span>{getStatusPercentage()}%</span>
            </div>
            <Progress value={getStatusPercentage()} />
          </div>
        </CardContent>
      </Card>

      {status === 'done' && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Document Summary</CardTitle>
              <CardDescription>
                AI-generated summary of the document
              </CardDescription>
            </CardHeader>
            <CardContent className="prose prose-sm dark:prose-invert">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {summary}
              </ReactMarkdown>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Document Content</CardTitle>
              <CardDescription>
                Full document content in markdown format
              </CardDescription>
            </CardHeader>
            <CardContent className="prose prose-sm dark:prose-invert max-h-[500px] overflow-y-auto">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdown}
              </ReactMarkdown>
            </CardContent>
          </Card>
        </>
      )}

      {status === 'error' && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
            <CardDescription>
              An error occurred during document processing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p>{markdown || 'Unknown error'}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 
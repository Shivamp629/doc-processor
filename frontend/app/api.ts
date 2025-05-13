import axios from 'axios';
import { API_BASE_URL } from '@/lib/utils';

interface JobStatus {
    job_id: string;
    status: string;
    markdown: string;
    summary: string;
}

// Create API client
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'multipart/form-data',
    },
});

// Upload documents
export async function uploadDocuments(files: File[], parser: string): Promise<string> {
    const formData = new FormData();

    files.forEach(file => {
        formData.append('files', file);
    });

    formData.append('parser', parser);

    try {
        const response = await apiClient.post<{ job_id: string }>(
            '/api/v1/documents/upload',
            formData
        );
        return response.data.job_id;
    } catch (error) {
        console.error('Error uploading documents:', error);
        throw new Error('Failed to upload documents. Please try again.');
    }
}

// Get job status
export async function getJobStatus(jobId: string): Promise<JobStatus> {
    try {
        const response = await apiClient.get<JobStatus>(`/api/v1/documents/${jobId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching job status:', error);
        throw new Error('Failed to fetch job status. Please try again.');
    }
}

// Poll job status until done or error
export async function pollJobStatus(
    jobId: string,
    onStatusUpdate: (status: JobStatus) => void,
    interval = 2000,
    maxAttempts = 60 // 2 minutes max
): Promise<void> {
    let attempts = 0;

    const poll = async () => {
        if (attempts >= maxAttempts) {
            throw new Error('Polling timeout reached');
        }

        try {
            const status = await getJobStatus(jobId);
            onStatusUpdate(status);

            if (status.status === 'done' || status.status === 'error') {
                return;
            }

            attempts++;
            setTimeout(poll, interval);
        } catch (error) {
            console.error('Error polling job status:', error);
            // Continue polling even on error
            attempts++;
            setTimeout(poll, interval);
        }
    };

    await poll();
} 
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
export interface UploadJob {
    job_id: string;
    filename: string;
}

export async function uploadDocuments(files: File[], parser: string): Promise<UploadJob[]> {
    const formData = new FormData();

    files.forEach(file => {
        formData.append('files', file);
    });

    formData.append('parser', parser);

    try {
        const response = await apiClient.post<UploadJob[]>(
            '/api/v1/documents/upload',
            formData
        );
        return response.data;
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
    initialInterval = 100,
    slowInterval = 500,
    fastPollDurationMs = 5000
): Promise<void> {
    let startTime = Date.now();

    const poll = async () => {
        try {
            const status = await getJobStatus(jobId);
            onStatusUpdate(status);

            if (status.status === 'done' || status.status === 'error') {
                return;
            }

            // Adaptive polling: fast for first 5s, then slow
            const elapsed = Date.now() - startTime;
            const interval = elapsed < fastPollDurationMs ? initialInterval : slowInterval;
            setTimeout(poll, interval);
        } catch (error) {
            console.error('Error polling job status:', error);
            // Retry quickly on error
            setTimeout(poll, initialInterval);
        }
    };

    await poll();
} 
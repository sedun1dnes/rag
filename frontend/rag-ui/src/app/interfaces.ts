import type { DocumentStatus } from '../interfaces/documents';

export type DocumentDto = {
    id: string;
    original_name: string;
    status: DocumentStatus;
    created_at: string;
};

export type ListDocumentsRequest = {
    limit?: number;
    search?: string;
};

export type ListDocumentsResponse = {
    documents: DocumentDto[];
    limit: number;
};

export type UploadDocumentsRequest = {
    files: File[];
};

export type UploadDocumentsResponse = {
    batch_id: string;
    time_utc: string;
    docs_dir: string;
    saved: Array<{
        original: string;
        saved_as: string;
        path: string;
        status: 'uploaded' | string;
    }>;
    rejected: Array<{
        filename: string | null;
        reason: string;
    }>;
    status_url: string;
};

export type SendMessageRequest = {
    message: string;
}

export type SendMessageResponse = {
    response: string;
}
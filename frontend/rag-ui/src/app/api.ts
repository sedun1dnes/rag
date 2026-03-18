import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { DocumentStatus } from '../interfaces/documents';

export type DocumentDto = {
  id: string;
  original_name: string;
  status: DocumentStatus;
  created_at: string;
};

export type ListDocumentsRequest = {
  limit?: number;
  query?: string;
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

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:5000',
  }),
  endpoints: (build) => ({
    listDocuments: build.query<ListDocumentsResponse, ListDocumentsRequest | void>({
      query: (arg) => ({
        url: '/documents',
        method: 'GET',
        params: arg?.limit ? { limit: arg.limit } : undefined,
      }),
    }),
    uploadDocuments: build.mutation<UploadDocumentsResponse, UploadDocumentsRequest>({
      query: ({ files }) => {
        const body = new FormData();
        for (const file of files) body.append('files', file);

        return {
          url: '/documents/upload',
          method: 'POST',
          body,
        };
      },
    }),
  }),
});

export const { useListDocumentsQuery, useUploadDocumentsMutation } = api;

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  ListDocumentsRequest,
  ListDocumentsResponse,
  UploadDocumentsRequest,
  UploadDocumentsResponse,
  SendMessageResponse,
  SendMessageRequest,
} from './interfaces';


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
        params: arg?.search ? { limit: arg.limit, search: arg.search } : undefined,
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
    sendMessage: build.mutation<SendMessageResponse, SendMessageRequest>({
      query: ({ message }) => {
        return {
          url: 'chat/new-message',
          method: 'POST',
          body: { message },
        }
      }
    })
  }),
});

export const { useListDocumentsQuery, useUploadDocumentsMutation, useSendMessageMutation } = api;

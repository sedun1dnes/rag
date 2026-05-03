import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
    KnowledgeBaseDto,
    KnowledgeBaseDetailDto,
    CreateKnowledgeBaseRequest,
    UploadDocumentsRequest,
    UploadDocumentsResponse,
    ChatDto,
    CreateChatRequest,
    MessageDto,
    SendMessageRequest,
    SendMessageResponse,
} from './interfaces';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

export const api = createApi({
    reducerPath: 'api',
    baseQuery: fetchBaseQuery({ baseUrl: BASE_URL }),
    tagTypes: ['KnowledgeBase', 'Document', 'Chat', 'Message'],
    endpoints: (build) => ({

        // --- Knowledge Bases ---

        listKnowledgeBases: build.query<KnowledgeBaseDto[], void>({
            query: () => '/knowledge-bases',
            providesTags: ['KnowledgeBase'],
        }),

        createKnowledgeBase: build.mutation<KnowledgeBaseDto, CreateKnowledgeBaseRequest>({
            query: (body) => ({ url: '/knowledge-bases', method: 'POST', body }),
            invalidatesTags: ['KnowledgeBase'],
        }),

        getKnowledgeBase: build.query<KnowledgeBaseDetailDto, string>({
            query: (id) => `/knowledge-bases/${id}`,
            providesTags: (_r, _e, id) => [{ type: 'KnowledgeBase', id }, 'Document'],
        }),

        deleteKnowledgeBase: build.mutation<void, string>({
            query: (id) => ({ url: `/knowledge-bases/${id}`, method: 'DELETE' }),
            invalidatesTags: ['KnowledgeBase'],
        }),

        // --- Documents ---

        uploadDocuments: build.mutation<UploadDocumentsResponse, UploadDocumentsRequest>({
            query: ({ kb_id, files }) => {
                const body = new FormData();
                for (const file of files) body.append('files', file);
                return { url: `/knowledge-bases/${kb_id}/documents`, method: 'POST', body };
            },
            invalidatesTags: ['Document', 'KnowledgeBase'],
        }),

        deleteDocument: build.mutation<void, string>({
            query: (id) => ({ url: `/documents/${id}`, method: 'DELETE' }),
            invalidatesTags: ['Document', 'KnowledgeBase'],
        }),

        // --- Chats ---

        listChats: build.query<ChatDto[], string>({
            query: (session_id) => `/chats?session_id=${session_id}`,
            providesTags: ['Chat'],
        }),

        createChat: build.mutation<ChatDto, CreateChatRequest>({
            query: (body) => ({ url: '/chats', method: 'POST', body }),
            invalidatesTags: ['Chat'],
        }),

        deleteChat: build.mutation<void, string>({
            query: (id) => ({ url: `/chats/${id}`, method: 'DELETE' }),
            invalidatesTags: ['Chat'],
        }),

        // --- Messages ---

        getMessages: build.query<MessageDto[], string>({
            query: (chat_id) => `/chats/${chat_id}/messages`,
            providesTags: (_r, _e, chat_id) => [{ type: 'Message', id: chat_id }],
        }),

        sendMessage: build.mutation<SendMessageResponse, SendMessageRequest>({
            query: ({ chat_id, ...body }) => ({
                url: `/chats/${chat_id}/messages`,
                method: 'POST',
                body,
            }),
            invalidatesTags: (_r, _e, { chat_id }) => [{ type: 'Message', id: chat_id }],
        }),
    }),
});

export const {
    useListKnowledgeBasesQuery,
    useCreateKnowledgeBaseMutation,
    useGetKnowledgeBaseQuery,
    useDeleteKnowledgeBaseMutation,
    useUploadDocumentsMutation,
    useDeleteDocumentMutation,
    useListChatsQuery,
    useCreateChatMutation,
    useDeleteChatMutation,
    useGetMessagesQuery,
    useSendMessageMutation,
} = api;

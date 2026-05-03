import type { DocumentStatus } from '../interfaces/documents';

// Knowledge Bases

export type KnowledgeBaseDto = {
    id: string;
    name: string;
    description: string | null;
    document_count: number;
    created_at: string | null;
};

export type KnowledgeBaseDetailDto = KnowledgeBaseDto & {
    documents: DocumentDto[];
};

export type CreateKnowledgeBaseRequest = {
    name: string;
    description?: string;
};

// Documents

export type DocumentDto = {
    id: string;
    filename: string;
    status: DocumentStatus;
    downloaded_at: string;
    knowledge_base_id?: string;
};

export type UploadDocumentsRequest = {
    kb_id: string;
    files: File[];
};

export type UploadDocumentsResponse = {
    saved: Array<{ id: string; filename: string; downloaded_at: string; status: string }>;
    rejected: Array<{ filename: string | null; reason: string }>;
};

// Chats

export type ChatDto = {
    id: string;
    title: string;
    session_id: string;
    updated_at: string | null;
};

export type CreateChatRequest = {
    title?: string;
    session_id: string;
};

// Messages

export type MessageDto = {
    id: string;
    text: string;
    type: 'user' | 'assistant';
    created_at: string;
    knowledge_base_id: string | null;
};

export type SendMessageRequest = {
    chat_id: string;
    text: string;
    knowledge_base_id?: string | null;
};

export type SendMessageResponse = {
    user_message: MessageDto;
    assistant_message: MessageDto;
};

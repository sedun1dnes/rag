import { useState, useRef, useEffect } from 'react';
import { Text, Divider } from '@gravity-ui/uikit';
import {
    MessageList,
    PromptInput,
} from '@gravity-ui/aikit';
import type { TChatMessage, TSubmitData } from '@gravity-ui/aikit';

export const Chats = () => {
    const [messages, setMessages] = useState<TChatMessage[]>([
        {
            id: '1',
            role: 'user',
            content: 'Hello!',
            timestamp: '2024-01-01T12:00:00Z',
        },
        {
            id: '2',
            role: 'assistant',
            content: 'Hi! How can I help you today?',
            timestamp: '2024-01-01T12:00:01Z',
        },
    ]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const addMessage = async (data: TSubmitData): Promise<void> => {
        const message: TChatMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            content: data.content,
            timestamp: new Date().toISOString(),
        };
    
        setMessages(prev => [...prev, message]);
    };

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100vh',
            }}
        >
            <div style={{ padding: '8px 16px' }}>
                <Text variant="header-1">Чат</Text>
            </div>
            <Divider style={{ margin: 0 }} />

            <div
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 16,
                    padding: 16,
                }}
            >
                <MessageList messages={messages} showTimestamp />
                <div ref={messagesEndRef} />
            </div>

            <div style={{ padding: '0 16px 16px 16px' }}>
                <PromptInput
                    onSend={addMessage}
                    view="full"
                    bodyProps={{ placeholder: 'Ваш вопрос' }}
                />
            </div>
        </div>
    );
};
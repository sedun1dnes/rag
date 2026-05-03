import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
    Button,
    Divider,
    Icon,
    Loader,
    Select,
    Text,
} from '@gravity-ui/uikit';
import { ArrowUp } from '@gravity-ui/icons';
import {
    useGetMessagesQuery,
    useListKnowledgeBasesQuery,
} from '../app/api';
import type { MessageDto } from '../app/interfaces';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

function MessageBubble({ message }: { message: Pick<MessageDto, 'id' | 'text' | 'type'> }) {
    const isUser = message.type === 'user';

    if (isUser) {
        return (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div
                    style={{
                        maxWidth: '60%',
                        padding: '10px 14px',
                        borderRadius: 12,
                        background: 'var(--g-color-base-selection)',
                        fontSize: 14,
                        lineHeight: '20px',
                    }}
                >
                    {message.text}
                </div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
                style={{
                    maxWidth: '75%',
                    fontSize: 14,
                    lineHeight: '22px',
                    color: 'var(--g-color-text-primary)',
                    whiteSpace: 'pre-wrap',
                }}
            >
                {message.text}
            </div>
        </div>
    );
}

export function ChatPage() {
    const { chatId = '' } = useParams<{ chatId: string }>();
    const { data: msgs, isLoading: msgsLoading, refetch } = useGetMessagesQuery(chatId);
    const { data: kbs } = useListKnowledgeBasesQuery();
    const [selectedKbId, setSelectedKbId] = useState<string>('');
    const [inputText, setInputText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingText, setStreamingText] = useState('');
    const [pendingUserText, setPendingUserText] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [msgs, streamingText]);

    const handleSend = async () => {
        const text = inputText.trim();
        if (!text || !selectedKbId || isStreaming) return;

        setInputText('');
        setPendingUserText(text);
        setIsStreaming(true);
        setStreamingText('');

        try {
            const response = await fetch(`${BASE_URL}/chats/${chatId}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, knowledge_base_id: selectedKbId }),
            });

            const reader = response.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() ?? '';

                for (const part of parts) {
                    if (!part.startsWith('data: ')) continue;
                    try {
                        const event = JSON.parse(part.slice(6));
                        if (event.type === 'token') {
                            setStreamingText((prev) => prev + event.token);
                        } else if (event.type === 'done') {
                            setIsStreaming(false);
                            refetch().then(() => {
                                setPendingUserText(null);
                                setStreamingText('');
                            });
                        }
                    } catch {
                        // skip malformed event
                    }
                }
            }
        } catch {
            setIsStreaming(false);
            setPendingUserText(null);
            setStreamingText('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const kbOptions = (kbs ?? []).map((kb) => ({ value: kb.id, content: kb.name }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ padding: '12px 24px' }}>
                <Text variant="header-1">Чат</Text>
            </div>
            <Divider />

            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 24px',
                    borderBottom: '1px solid var(--g-color-line-generic)',
                }}
            >
                <Text variant="body-2" color="secondary">
                    База знаний <span style={{ color: 'var(--g-color-text-danger)' }}>*</span>
                </Text>
                <Select
                    placeholder="Выберите базу знаний"
                    value={selectedKbId ? [selectedKbId] : []}
                    onUpdate={([v]) => setSelectedKbId(v ?? '')}
                    options={kbOptions}
                    width={240}
                />
            </div>

            <div
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px 24px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12,
                }}
            >
                {msgsLoading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 32 }}>
                        <Loader />
                    </div>
                ) : (
                    <>
                        {(msgs ?? []).map((msg) => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))}
                        {pendingUserText && (
                            <MessageBubble
                                message={{ id: '__pending_user', text: pendingUserText, type: 'user' }}
                            />
                        )}
                        {streamingText && (
                            <MessageBubble
                                message={{ id: '__streaming', text: streamingText, type: 'assistant' }}
                            />
                        )}
                        {isStreaming && !streamingText && (
                            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                <Loader size="s" />
                                <Text color="secondary" variant="body-1">Генерация ответа...</Text>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            <div
                style={{
                    padding: '12px 24px 8px',
                    borderTop: '1px solid var(--g-color-line-generic)',
                }}
            >
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'flex-end',
                        gap: 8,
                        padding: '8px 12px',
                        border: '1px solid var(--g-color-line-generic)',
                        borderRadius: 8,
                        background: 'var(--g-color-base-background)',
                    }}
                >
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Введите ваше сообщение..."
                        rows={1}
                        style={{
                            flex: 1,
                            border: 'none',
                            outline: 'none',
                            resize: 'none',
                            background: 'transparent',
                            fontSize: 14,
                            lineHeight: '20px',
                            fontFamily: 'inherit',
                            color: 'var(--g-color-text-primary)',
                            maxHeight: 120,
                            overflowY: 'auto',
                        }}
                    />
                    <Button
                        view="outlined"
                        size="m"
                        onClick={handleSend}
                        disabled={!inputText.trim() || !selectedKbId || isStreaming}
                    >
                        <Icon data={ArrowUp} />
                    </Button>
                </div>
                <Text
                    variant="caption-2"
                    color="hint"
                    style={{ display: 'block', textAlign: 'center', marginTop: 6 }}
                >
                    ИИ может ошибаться. Проверяйте важную информацию.
                </Text>
            </div>
        </div>
    );
}

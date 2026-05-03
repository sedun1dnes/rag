import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Divider, Icon, Loader, Select, Text, TextArea } from '@gravity-ui/uikit';
import { ArrowUp } from '@gravity-ui/icons';
import { MarkdownRenderer } from '@gravity-ui/aikit';
import { useGetMessagesQuery, useListKnowledgeBasesQuery, api } from '../app/api';
import { useDispatch } from 'react-redux';
import type { MessageDto } from '../app/interfaces';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:5000';

function MessageBubble({ message }: { message: Pick<MessageDto, 'id' | 'text' | 'type'> }) {
    if (message.type === 'user') {
        return (
            <div className="flex justify-end">
                <div className="max-w-[60%] px-3.5 py-2.5 rounded-xl bg-[var(--g-color-base-selection)] text-sm leading-5">
                    {message.text}
                </div>
            </div>
        );
    }

    return (
        <div className="flex justify-start">
            <div className="max-w-[75%] text-sm leading-[22px]">
                <MarkdownRenderer content={message.text} />
            </div>
        </div>
    );
}

export function ChatPage() {
    const { chatId = '' } = useParams<{ chatId: string }>();
    const dispatch = useDispatch();
    const { data: msgs, isLoading: msgsLoading } = useGetMessagesQuery(chatId);
    const { data: kbs } = useListKnowledgeBasesQuery();
    const [selectedKbId, setSelectedKbId] = useState<string>('');
    const [inputText, setInputText] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingText, setStreamingText] = useState('');
    const [pendingUserText, setPendingUserText] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'instant' });
    }, [msgs, streamingText, pendingUserText]);

    useEffect(
        () => {
            if (kbs) {
                setSelectedKbId(kbs[0].id);
            }
        },
        [kbs],
    )

    const handleSend = async () => {
        const text = inputText.trim();
        if (!text || !selectedKbId || isStreaming) return;

        setInputText('');
        setPendingUserText(text);
        setIsStreaming(true);
        setStreamingText('');

        let capturedUserMsg: MessageDto | null = null;

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
                        if (event.type === 'user_message') {
                            capturedUserMsg = event.message as MessageDto;
                        } else if (event.type === 'token') {
                            setStreamingText((prev: string) => prev + event.token);
                        } else if (event.type === 'chat_updated') {
                            dispatch(api.util.invalidateTags(['Chat']));
                        } else if (event.type === 'done') {
                            dispatch(api.util.updateQueryData('getMessages', chatId, (draft) => {
                                if (capturedUserMsg) draft.push(capturedUserMsg);
                                draft.push(event.message as MessageDto);
                            }));
                            setIsStreaming(false);
                            setPendingUserText(null);
                            setStreamingText('');
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

    const kbOptions = (kbs ?? []).map((kb: { id: string; name: string }) => ({ value: kb.id, content: kb.name }));

    return (
        <div className="absolute inset-0 flex flex-col overflow-hidden">
            <div className="px-6 py-3">
                <Text variant="header-1">Чат</Text>
            </div>
            <Divider />
            <div className="flex items-center gap-3 px-6 py-3 border-b border-[var(--g-color-line-generic)]">
                <Text variant="body-2" color="secondary">
                    База знаний
                </Text>
                <Select
                    placeholder="Выберите базу знаний"
                    value={selectedKbId ? [selectedKbId] : []}
                    onUpdate={([v]: [string]) => setSelectedKbId(v ?? '')}
                    options={kbOptions}
                    width={240}
                />
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4 flex flex-col gap-3">
                {msgsLoading ? (
                    <div className="flex justify-center pt-8">
                        <Loader />
                    </div>
                ) : (
                    <>
                        {(msgs ?? []).map((msg: MessageDto) => (
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
                            <div className="flex gap-1.5 items-center">
                                <Loader size="s" />
                                <Text color="secondary" variant="body-1">Генерация ответа...</Text>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            <div className="px-6 pt-3 pb-2 border-t border-[var(--g-color-line-generic)]">
                <div className="flex items-end gap-2 px-3 py-2 border border-[var(--g-color-line-generic)] rounded-lg bg-[var(--g-color-base-background)]">
                    <TextArea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Введите ваше сообщение..."
                        view="clear"
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
                    className="block text-center mt-1.5"
                >
                    ИИ может ошибаться. Проверяйте важную информацию.
                </Text>
            </div>
        </div>
    );
}

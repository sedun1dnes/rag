import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { PageLayout, PageLayoutAside } from '@gravity-ui/navigation';
import type { AsideHeaderItem } from '@gravity-ui/navigation';
import { FileText, Comments, SparklesFill, Plus } from '@gravity-ui/icons';
import { Button, Icon } from '@gravity-ui/uikit';
import { KnowledgeBases, KnowledgeBaseDetailPage, Chats, ChatPage } from './pages';
import { useState } from 'react';
import { useCreateChatMutation } from './app/api';
import { getSessionId } from './app/session';
import './index.css';

const SESSION_ID = getSessionId();

function App() {
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
    const navigate = useNavigate();
    const location = useLocation();
    const [createChat, { isLoading: isCreatingChat }] = useCreateChatMutation();

    const handleNewChat = async () => {
        const chat = await createChat({ session_id: SESSION_ID }).unwrap();
        navigate(`/chats/${chat.id}`);
    };

    const asideHeaderItems: AsideHeaderItem[] = [
        {
            id: 'knowledge-bases',
            title: 'Базы знаний',
            icon: FileText,
            current: location.pathname.startsWith('/knowledge-bases'),
            onItemClick: () => navigate('/knowledge-bases'),
        },
        {
            id: 'chats',
            title: 'Чаты',
            icon: Comments,
            current: location.pathname.startsWith('/chats'),
            onItemClick: () => navigate('/chats'),
        },
    ];

    return (
        <PageLayout compact={sidebarOpen}>
            <PageLayoutAside
                logo={{
                    text: 'RAG',
                    icon: SparklesFill,
                    iconSize: 24,
                    href: '/',
                    'aria-label': 'RAG',
                }}
                onChangeCompact={setSidebarOpen}
                menuItems={asideHeaderItems}
                renderFooter={({ compact }) =>
                    compact ? null : (
                        <div className="px-3 py-2">
                            <Button
                                view="outlined"
                                width="max"
                                size="l"
                                loading={isCreatingChat}
                                onClick={handleNewChat}
                            >
                                <Icon data={Plus} />
                                Новый чат
                            </Button>
                        </div>
                    )
                }
            />

            <PageLayout.Content
                renderContent={() => (
                    <main className="h-full">
                        <Routes>
                            <Route path="/" element={<Navigate to="/knowledge-bases" replace />} />
                            <Route path="/knowledge-bases" element={<KnowledgeBases />} />
                            <Route path="/knowledge-bases/:kbId" element={<KnowledgeBaseDetailPage />} />
                            <Route path="/chats" element={<Chats onNewChat={handleNewChat} isCreating={isCreatingChat} />} />
                            <Route path="/chats/:chatId" element={<ChatPage />} />
                        </Routes>
                    </main>
                )}
            />
        </PageLayout>
    );
}

export default App;

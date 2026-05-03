import { useNavigate } from 'react-router-dom';
import {
    Button,
    Divider,
    Icon,
    Loader,
    Table,
    Text,
} from '@gravity-ui/uikit';
import { Plus, TrashBin } from '@gravity-ui/icons';
import {
    useListChatsQuery,
    useDeleteChatMutation,
} from '../app/api';
import { getSessionId } from '../app/session';

const SESSION_ID = getSessionId();

type Props = {
    onNewChat: () => void;
    isCreating: boolean;
};

export function Chats({ onNewChat, isCreating }: Props) {
    const navigate = useNavigate();
    const { data: chats, isLoading } = useListChatsQuery(SESSION_ID);
    const [deleteChat] = useDeleteChatMutation();

    const columns = [
        { id: 'title', name: 'Название' },
        { id: 'updated_at', name: 'Дата последнего обновления' },
        { id: 'remove', name: '' },
    ];

    const rows = (chats ?? []).map((chat) => ({
        id: chat.id,
        title: chat.title,
        updated_at: chat.updated_at
            ? new Date(chat.updated_at).toLocaleDateString('ru-RU')
            : '—',
        remove: (
            <Button
                view="flat"
                onClick={async (e) => {
                    e.stopPropagation();
                    await deleteChat(chat.id);
                }}
            >
                <Icon data={TrashBin} color="complementary" />
            </Button>
        ),
    }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '12px 24px',
                    alignItems: 'center',
                }}
            >
                <Text variant="header-1">Чаты</Text>
                <Button view="action" loading={isCreating} onClick={onNewChat}>
                    <Icon data={Plus} />
                    Новый чат
                </Button>
            </div>
            <Divider />

            <div style={{ flex: 1, padding: '12px 24px', overflowY: 'auto' }}>
                {isLoading ? (
                    <Loader />
                ) : (
                    <Table
                        columns={columns}
                        data={rows}
                        width="max"
                        onRowClick={(row) => navigate(`/chats/${(row as { id: string }).id}`)}
                    />
                )}
            </div>
        </div>
    );
}

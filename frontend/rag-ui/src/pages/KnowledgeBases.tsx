import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Button,
    Icon,
    Loader,
    Modal,
    Table,
    Text,
    TextArea,
    TextInput,
    Divider,
} from '@gravity-ui/uikit';
import { Plus, TrashBin } from '@gravity-ui/icons';
import {
    useListKnowledgeBasesQuery,
    useCreateKnowledgeBaseMutation,
    useDeleteKnowledgeBaseMutation,
} from '../app/api';

function CreateKbModal({ onClose }: { onClose: () => void }) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [createKb, { isLoading }] = useCreateKnowledgeBaseMutation();

    const handleCreate = async () => {
        if (!name.trim()) return;
        await createKb({ name: name.trim(), description: description.trim() || undefined });
        onClose();
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: 24, minWidth: 400 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text variant="header-1">Новая база знаний</Text>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <Text variant="body-2">Название</Text>
                <TextInput
                    value={name}
                    onUpdate={setName}
                    placeholder="Не заполнено"
                    size="l"
                />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <Text variant="body-2">Описание</Text>
                <TextArea
                    value={description}
                    onUpdate={setDescription}
                    placeholder="Не заполнено"
                    minRows={4}
                />
            </div>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
                <Button view="normal" onClick={onClose}>
                    Отмена
                </Button>
                <Button view="action" loading={isLoading} onClick={handleCreate}>
                    Создать
                </Button>
            </div>
        </div>
    );
}

export function KnowledgeBases() {
    const navigate = useNavigate();
    const { data: kbs, isLoading } = useListKnowledgeBasesQuery();
    const [deleteKb] = useDeleteKnowledgeBaseMutation();
    const [search, setSearch] = useState('');
    const [createOpen, setCreateOpen] = useState(false);

    const filtered = (kbs ?? []).filter((kb) =>
        kb.name.toLowerCase().includes(search.toLowerCase())
    );

    const kbColumns = [
        { id: 'name', name: 'Название' },
        { id: 'description', name: 'Описание' },
        { id: 'document_count', name: 'Документы' },
        { id: 'created_at', name: 'Дата создания' },
        { id: 'remove', name: '' },
    ];

    const kbRows = filtered.map((kb) => ({
        id: kb.id,
        name: kb.name,
        description: kb.description ?? '—',
        document_count: kb.document_count,
        created_at: kb.created_at
            ? new Date(kb.created_at).toLocaleDateString('ru-RU')
            : '—',
        remove: (
            <Button
                view="flat"
                onClick={async (e) => {
                    e.stopPropagation();
                    await deleteKb(kb.id);
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
                <Text variant="header-1">Базы знаний</Text>
                <Button view="action" onClick={() => setCreateOpen(true)}>
                    <Icon data={Plus} />
                    Новая база знаний
                </Button>
            </div>
            <Divider />

            <div style={{ padding: '12px 24px 0' }}>
                <TextInput
                    placeholder="Поиск по названию...."
                    value={search}
                    onUpdate={setSearch}
                    hasClear
                    size="l"
                />
            </div>

            <div style={{ flex: 1, padding: '12px 24px', overflowY: 'auto' }}>
                {isLoading ? (
                    <Loader />
                ) : (
                    <Table
                        columns={kbColumns}
                        data={kbRows}
                        width="max"
                        onRowClick={(row) => navigate(`/knowledge-bases/${(row as { id: string }).id}`)}
                    />
                )}
            </div>

            <Modal open={createOpen} onClose={() => setCreateOpen(false)}>
                <CreateKbModal onClose={() => setCreateOpen(false)} />
            </Modal>
        </div>
    );
}

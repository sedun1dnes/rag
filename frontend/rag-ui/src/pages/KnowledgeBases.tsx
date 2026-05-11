import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Divider, Icon, Loader, Modal, Table, Text, TextArea, TextInput } from '@gravity-ui/uikit';
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
        <div className="flex flex-col gap-4 p-6 min-w-[400px]">
            <Text variant="header-1">Новая база знаний</Text>
            <div className="flex flex-col gap-1">
                <Text variant="body-2">Название</Text>
                <TextInput value={name} onUpdate={setName} placeholder="Не заполнено" size="l" />
            </div>
            <div className="flex flex-col gap-1">
                <Text variant="body-2">Описание</Text>
                <TextArea value={description} onUpdate={setDescription} placeholder="Не заполнено" minRows={4} />
            </div>
            <div className="flex gap-3 justify-end mt-2">
                <Button view="normal" size="l" onClick={onClose}>Отмена</Button>
                <Button view="action" size="l" loading={isLoading} onClick={handleCreate}>Создать</Button>
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
        created_at: kb.created_at ? new Date(kb.created_at).toLocaleDateString('ru-RU') : '—',
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
        <div className="flex flex-col h-full">
            <div className="flex justify-between px-6 py-3 items-center">
                <Text variant="header-1">Базы знаний</Text>
                <Button onClick={() => setCreateOpen(true)}>
                    <Icon data={Plus} />
                    Новая база знаний
                </Button>
            </div>
            <Divider />

            <div className="px-6 pt-3">
                <TextInput
                    placeholder="Поиск по названию...."
                    value={search}
                    onUpdate={setSearch}
                    hasClear
                    size="l"
                />
            </div>

            <div className="flex-1 px-6 py-3 overflow-y-auto">
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

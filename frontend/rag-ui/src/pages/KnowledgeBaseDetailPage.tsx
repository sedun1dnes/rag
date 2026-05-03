import { useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
    Button,
    Divider,
    Icon,
    Label,
    Loader,
    Table,
    Text,
    TextInput,
    type LabelProps,
} from '@gravity-ui/uikit';
import { Plus, TrashBin } from '@gravity-ui/icons';
import {
    useGetKnowledgeBaseQuery,
    useUploadDocumentsMutation,
    useDeleteDocumentMutation,
} from '../app/api';
import { statusMap } from './consts';

export function KnowledgeBaseDetailPage() {
    const { kbId = '' } = useParams<{ kbId: string }>();
    const fileRef = useRef<HTMLInputElement | null>(null);
    const [search, setSearch] = useState('');
    const { data, isLoading, refetch } = useGetKnowledgeBaseQuery(kbId);
    const [uploadDocuments, uploadState] = useUploadDocumentsMutation();
    const [deleteDocument] = useDeleteDocumentMutation();

    const docColumns = [
        { id: 'name', name: 'Название' },
        { id: 'status', name: 'Статус' },
        { id: 'date', name: 'Дата добавления' },
        { id: 'remove', name: '' },
    ];

    const filtered = (data?.documents ?? []).filter((doc) =>
        doc.filename.toLowerCase().includes(search.toLowerCase())
    );

    const docRows = filtered.map((doc) => {
        const { name: statusName, theme: statusTheme } = statusMap[doc.status] ?? {
            name: 'Неизвестно',
            theme: 'default',
        };
        return {
            id: doc.id,
            name: doc.filename,
            status: (
                <Label size="m" theme={statusTheme as LabelProps['theme']}>
                    {statusName}
                </Label>
            ),
            date: new Date(doc.downloaded_at.replace(/\.\d+/, '')).toLocaleDateString('ru-RU'),
            remove: (
                <Button
                    view="flat"
                    onClick={async (e) => {
                        e.stopPropagation();
                        await deleteDocument(doc.id);
                        refetch();
                    }}
                >
                    <Icon data={TrashBin} color="complementary" />
                </Button>
            ),
        };
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px 24px',
                }}
            >
                <Text variant="header-1" style={{ flex: 1 }}>
                    {data ? data.name : '...'}
                </Text>
                <Button
                    view="action"
                    size="l"
                    loading={uploadState.isLoading}
                    onClick={() => fileRef.current?.click()}
                >
                    <Icon data={Plus} />
                    Добавить документ
                </Button>
                <input
                    ref={fileRef}
                    type="file"
                    hidden
                    multiple
                    onChange={async (e) => {
                        const files = Array.from(e.target.files ?? []);
                        if (!files.length) return;
                        await uploadDocuments({ kb_id: kbId, files });
                        refetch();
                        e.currentTarget.value = '';
                    }}
                />
            </div>
            <Divider />

            {data?.description && (
                <div style={{ padding: '8px 24px' }}>
                    <Text color="secondary">{data.description}</Text>
                </div>
            )}

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
                    <Table columns={docColumns} data={docRows} width="max" />
                )}
            </div>
        </div>
    );
}

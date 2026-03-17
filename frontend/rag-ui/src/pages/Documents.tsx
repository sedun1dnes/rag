import { Button, Loader, Icon, TextInput, Text, Divider, Table, Label, type LabelProps } from '@gravity-ui/uikit';
import { Magnifier, ArrowShapeDownToLine, TrashBin } from '@gravity-ui/icons';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useListDocumentsQuery, useUploadDocumentsMutation } from '../app/api';
import { statusMap } from './consts';

type DocItem = {
  id: string;
  file: File;
};

export function Documents() {
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [query, setQuery] = useState('');
    const [docs, setDocs] = useState<DocItem[]>([]);
    const [uploadDocuments, uploadState] = useUploadDocumentsMutation();
    const {data, isLoading, isError, refetch} = useListDocumentsQuery({limit: 200});

  const imageUrlsById = useMemo(() => {
    const map = new Map<string, string>();
    for (const doc of docs) {
      if (doc.file.type.startsWith('image/')) {
        map.set(doc.id, URL.createObjectURL(doc.file));
      }
    }
    return map;
  }, [docs]);

  useEffect(() => {
    return () => {
      for (const url of imageUrlsById.values()) URL.revokeObjectURL(url);
    };
  }, [imageUrlsById]);

  const tableColumns = [
    {
        id: 'download',
        name: ''
    },
    {
        id: 'name',
        name: 'Название'
    },
    {
        id: 'date',
        name: 'Дата загрузки'
    },
    {
        id: 'status',
        name: 'Статус'
    },
    {
        id: 'remove',
        name: ''
    }
  ];

  const tableData = useMemo(
    () => {
        if (data?.documents) {
            return data.documents.map(document => {
                const { name: statusName, theme: statusTheme } = statusMap[document.status] || {
                    name: "Неизвестно",
                    theme: "default",
                };
                return {
                    download: <Button view='flat'>
                        <Icon data={ArrowShapeDownToLine} color='complementary'/>
                    </Button>,
                    name: document.original_name,
                    date: new Date(document.created_at.replace(/\.\d+/, '')).toLocaleString(
                        "ru-RU", 
                        {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        }
                    ),
                    status: <Label size='m' theme={statusTheme as LabelProps['theme']}>
                        {statusName}
                    </Label>,
                    remove: <Button view='flat'>
                        <Icon data={TrashBin} color='complementary'/>
                    </Button>,
                }
            })
        }
    },
    [data]
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            paddingLeft: 16,
            paddingRight: 16,
            paddingTop: 8,
            paddingBottom: 8,
        }}>
            <Text
                variant='header-1'
            >
                Документы
            </Text>
            <Button
                view="action"
                onClick={() => inputRef.current?.click()}
                loading={uploadState.isLoading}
            >
                Загрузить
            </Button>
        </div>
        <Divider style={{ padding: 0 }}/>
        <div style={{ display: 'flex', flexDirection: 'column', paddingTop: 16, paddingLeft: 16, paddingRight: 16 }}>
            <TextInput
                style={{ flex: 1 }}
                disabled={true}
                placeholder="Search documents"
                value={query}
                onUpdate={setQuery}
                startContent={<Icon data={Magnifier} color="secondary" style={{ margin: 8 }} />}
                hasClear
            />
            <input
              ref={inputRef}
              type="file"
              hidden
              multiple
              onChange={async (e) => {
                const files = Array.from(e.target.files ?? []);
                if (files.length === 0) return;

                setDocs((prev) => [
                  ...files.map((file) => ({id: crypto.randomUUID(), file})),
                  ...prev,
                ]);

                try {
                  await uploadDocuments({files}).unwrap();
                  refetch();
                } finally {
                  e.currentTarget.value = '';
                }
              }}
            />
        </div>

        <div style={{padding: 16}}>
          {isLoading && <Loader/>}
          {!isLoading && !isError && (
            <Table
                columns={tableColumns}
                data={tableData ?? []}
                width='max'
            />
          )}
        </div>
    </div>
  );
}
import { PageLayout, PageLayoutAside } from '@gravity-ui/navigation';
import type { AsideHeaderItem } from '@gravity-ui/navigation';
import { FileText, Comments, SparklesFill } from '@gravity-ui/icons';
import { Documents, Chats } from './pages';
import { useState } from 'react';
import './index.css';

function App() {
  const [open, setOpen] = useState<boolean>(false);
  const [activePage, setActivePage] = useState<'documents' | 'chats'>('documents');

  const asideHeaderItems: AsideHeaderItem[] = [
    {
      id: 'documents',
      title: 'Документы',
      icon: FileText,
      current: activePage === 'documents',
      onItemClick: () => setActivePage('documents'),
    },
    {
      id: 'chats',
      title: 'Чат',
      icon: Comments,
      current: activePage === 'chats',
      onItemClick: () => setActivePage('chats'),
    },
  ];

  return (
    <PageLayout compact={open}>
      <PageLayoutAside
        logo={{
          text: 'RAG',
          icon: SparklesFill,
          iconSize: 24,
          href: '/',
          'aria-label': 'RAG',
        }}
        onChangeCompact={setOpen}
        menuItems={asideHeaderItems}
      />

      <PageLayout.Content
        renderContent={() => (
          <main>
            {activePage === 'documents' && <Documents/>}
            {activePage === 'chats' && <Chats/>}
          </main>
        )}
      />
    </PageLayout>
  );
}

export default App;
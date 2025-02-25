// src/pages/documents/DocumentsPage.jsx
import React, { useState } from 'react';
import { Tabs, Button } from 'antd';
import ContractsTab from '../../components/documents/tabs/ContractsTab';
import SpecificationsTab from '../../components/documents/tabs/SpecificationsTab';
import InvoicesTab from '../../components/documents/tabs/InvoicesTab';
import UPDsTab from '../../components/documents/tabs/UPDsTab';

const DocumentsPage = () => {
  const [activeTab, setActiveTab] = useState('contract');

  const items = [
    {
      key: 'contract',
      label: 'Договор',
      children: <ContractsTab />
    },
    {
      key: 'specification',
      label: 'Спецификация',
      children: <SpecificationsTab />
    },
    {
      key: 'invoice',
      label: 'Счет на оплату',
      children: <InvoicesTab />
    },
    {
      key: 'upd',
      label: 'УПД',
      children: <UPDsTab />
    }
  ];

  return (
    <div className="container" style={{ padding: '24px' }}>
      <h1>Документы</h1>

      <div style={{ display: 'flex', justifyContent: 'space-between', margin: '16px 0' }}>
        <Button type="primary">Добавить документ</Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={items}
      />
    </div>
  );
};

export default DocumentsPage;
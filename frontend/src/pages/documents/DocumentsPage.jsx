// src/pages/documents/DocumentsPage.jsx
import React, { useState } from 'react';
import { Tabs, Button } from 'antd';
import ContractsTab from '../../components/documents/tabs/ContractsTab';
import SpecificationsTab from '../../components/documents/tabs/SpecificationsTab';
import InvoicesTab from '../../components/documents/tabs/InvoicesTab';
import UPDsTab from '../../components/documents/tabs/UPDsTab';
import CreateDocumentModal from '../../components/documents/CreateDocumentModal';
import CreateContractModal from '../../components/documents/CreateContractModal';

const DocumentsPage = () => {
  const [activeTab, setActiveTab] = useState('contract');
  const [isCreateDocumentModalVisible, setIsCreateDocumentModalVisible] = useState(false);
  const [isCreateContractModalVisible, setIsCreateContractModalVisible] = useState(false);

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

  const handleAddDocument = () => {
    setIsCreateDocumentModalVisible(true);
  };

  const handleSelectDocumentType = (type) => {
    setIsCreateDocumentModalVisible(false);

    // Открываем соответствующее модальное окно в зависимости от типа
    if (type === 'contract') {
      setIsCreateContractModalVisible(true);
    }
    // Здесь можно добавить обработку для других типов документов
  };

  return (
    <div className="container" style={{ padding: '24px' }}>
      <h1>Документы</h1>

      <div style={{ display: 'flex', justifyContent: 'space-between', margin: '16px 0' }}>
        <Button type="primary" onClick={handleAddDocument}>Добавить документ</Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={items}
      />

      {/* Модальные окна */}
      <CreateDocumentModal
        visible={isCreateDocumentModalVisible}
        onCancel={() => setIsCreateDocumentModalVisible(false)}
        onSelectDocumentType={handleSelectDocumentType}
      />

      <CreateContractModal
        visible={isCreateContractModalVisible}
        onCancel={() => setIsCreateContractModalVisible(false)}
      />
    </div>
  );
};

export default DocumentsPage;
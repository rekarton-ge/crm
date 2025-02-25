// src/components/documents/tabs/InvoicesTab.jsx
import React, { useState } from 'react';
import { useGetInvoicesQuery, useDeleteInvoiceMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';
import { message, Button } from 'antd';

const InvoicesTab = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  const {
    data: invoicesData,
    isLoading: isInvoicesLoading,
    error: invoicesError
  } = useGetInvoicesQuery();

  const [deleteInvoice] = useDeleteInvoiceMutation();

  const handleDeleteMultiple = async () => {
    try {
      const deletionPromises = selectedRowKeys.map(id => deleteInvoice(id));
      await Promise.all(deletionPromises);
      message.success(`Удалено ${selectedRowKeys.length} счетов`);
      setSelectedRowKeys([]);
    } catch (error) {
      message.error('Не удалось удалить счета');
      console.error(error);
    }
  };

  const columns = [
    { key: 'number', title: 'Номер' },
    { key: 'date', title: 'Дата' },
    {
      key: 'client',
      title: 'Клиент',
      format: (client) => client?.name || '-'
    },
    {
      key: 'total_amount',
      title: 'Сумма',
      format: (amount) => amount ? `${amount.toLocaleString()} ₽` : '-'
    },
    {
      key: 'contract',
      title: 'Договор',
      format: (contract) => contract?.number || '-'
    },
    {
      key: 'specification',
      title: 'Спецификация',
      format: (specification) => specification?.number || '-'
    },
    { key: 'status', title: 'Статус' }
  ];


  return (
    <>
      {selectedRowKeys.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Button onClick={handleDeleteMultiple}>
            Удалить выбранные счета
          </Button>
        </div>
      )}
      <DocumentTable
        isLoading={isInvoicesLoading}
        error={invoicesError}
        errorMessage="Ошибка загрузки счетов"
        data={invoicesData}
        columns={columns}
        emptyMessage="Счета не найдены"
        onDelete={deleteInvoice}
        selectedRowKeys={selectedRowKeys}
        onSelectChange={setSelectedRowKeys}
        documentType="invoice"
      />
    </>
  );
};

export default InvoicesTab;

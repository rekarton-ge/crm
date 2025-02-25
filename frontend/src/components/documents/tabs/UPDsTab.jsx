// src/components/documents/tabs/UPDsTab.jsx
import React from 'react';
import { useGetUPDsQuery, useDeleteUPDMutation } from '../../../api/documentsApi';
import DocumentTable from '../DocumentTable';
import { message } from 'antd';

const UPDsTab = () => {
  const {
    data: updsData,
    isLoading: isUPDsLoading,
    error: updsError
  } = useGetUPDsQuery();

  const [deleteUPD] = useDeleteUPDMutation();

  const handleDeleteMultiple = async (ids) => {
    try {
      const deletionPromises = ids.map(id => deleteUPD(id));
      await Promise.all(deletionPromises);
      message.success(`Удалено ${ids.length} УПД`);
    } catch (error) {
      message.error('Не удалось удалить УПД');
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
    <DocumentTable
      isLoading={isUPDsLoading}
      error={updsError}
      errorMessage="Ошибка загрузки УПД"
      data={updsData}
      columns={columns}
      emptyMessage="УПД не найдены"
      onDelete={deleteUPD}
      onDeleteMultiple={handleDeleteMultiple}
      documentType="upd"
    />
  );
};

export default UPDsTab;
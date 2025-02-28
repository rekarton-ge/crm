// src/components/documents/tabs/ContractsTab.jsx
import React from 'react';
import { useGetContractsQuery, useDeleteContractMutation } from '../../../api/documentsApi';
import { useGetClientQuery } from '../../../api/clientsApi';
import DocumentTable from '../DocumentTable';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Tooltip } from 'antd';
import { EyeOutlined } from '@ant-design/icons';

// Компонент для отображения имени клиента
const ClientName = ({ clientId }) => {
  const { data: client } = useGetClientQuery(clientId, { skip: !clientId });
  return <span>{client?.name || '-'}</span>;
};

const ContractsTab = () => {
  const navigate = useNavigate();

  const {
    data: contractsData,
    isLoading: isContractsLoading,
    error: contractsError
  } = useGetContractsQuery();

  const [deleteContract] = useDeleteContractMutation();

  const handleViewContract = (contractId) => {
    navigate(`/documents/contracts/${contractId}`);
  };

  const columns = [
    {
      key: 'number',
      title: 'Номер',
      render: (_, record) => (
        <Link to={`/documents/contracts/${record.id}`}>
          {record.number}
        </Link>
      )
    },
    { key: 'date', title: 'Дата' },
    {
      key: 'client',
      title: 'Клиент',
      render: (clientId) => <ClientName clientId={clientId} />
    },
    { key: 'name', title: 'Название' },
    { key: 'status', title: 'Статус' },
    {
      key: 'actions',
      title: 'Действия',
      render: (_, record) => (
        <Tooltip title="Просмотреть">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewContract(record.id)}
          />
        </Tooltip>
      )
    }
  ];

  return (
    <DocumentTable
      isLoading={isContractsLoading}
      error={contractsError}
      errorMessage="Ошибка загрузки договоров"
      data={contractsData}
      columns={columns}
      emptyMessage="Договоры не найдены"
      onDelete={deleteContract}
      documentType="contract"
    />
  );
};

export default ContractsTab;
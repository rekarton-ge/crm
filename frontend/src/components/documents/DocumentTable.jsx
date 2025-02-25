// src/components/documents/DocumentTable.jsx
import React from 'react';
import { Table, Spin, Alert, Button, Popconfirm } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

// Общий компонент таблицы документов
const DocumentTable = ({
  isLoading,
  error,
  errorMessage,
  data,
  columns,
  emptyMessage,
  onDelete,
  documentType
}) => {
  // Форматирование даты
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'dd.MM.yyyy', { locale: ru });
    } catch (e) {
      return dateString;
    }
  };

  if (error) return <Alert message={errorMessage} description={error.message} type="error" showIcon />;

  const documents = data?.results || [];

  // Преобразуем колонки для Ant Design Table
  const tableColumns = [
    ...columns.map(column => ({
      title: column.title,
      dataIndex: column.key,
      key: column.key,
      render: (text, record) => {
        if (column.format) {
          return column.format(record[column.key], record);
        } else if (column.key === 'date') {
          return formatDate(text);
        } else {
          return text || '-';
        }
      }
    })),
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record) => (
        <Popconfirm
          title="Удаление документа"
          description="Вы уверены, что хотите удалить этот документ?"
          onConfirm={() => onDelete(record.id)}
          okText="Да"
          cancelText="Нет"
        >
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
          >
            Удалить
          </Button>
        </Popconfirm>
      ),
    }
  ];

  return (
    <Table
      columns={tableColumns}
      dataSource={documents}
      rowKey="id"
      loading={isLoading}
      locale={{ emptyText: emptyMessage }}
      pagination={{
        showSizeChanger: true,
        showTotal: (total) => `Всего: ${total}`,
        defaultPageSize: 10,
        pageSizeOptions: ['10', '20', '50']
      }}
    />
  );
};

export default DocumentTable;
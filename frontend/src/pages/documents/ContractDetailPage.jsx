// frontend/src/pages/documents/ContractDetailPage.jsx
// Страница для просмотра подробной информации о договоре
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetContractByIdQuery, useDeleteContractMutation } from '../../api/documentsApi';
import { useGetClientQuery } from '../../api/clientsApi';
import {
  Row,
  Col,
  Typography,
  Button,
  Descriptions,
  Space,
  Spin,
  Card,
  Tag,
  Alert,
  Popconfirm,
  message
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  FilePdfOutlined,
  FileAddOutlined
} from '@ant-design/icons';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const { Title, Text } = Typography;

const ContractDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    data: contract,
    isLoading: isContractLoading,
    error: contractError
  } = useGetContractByIdQuery(id);

  const [deleteContract] = useDeleteContractMutation();

  // Загружаем информацию о клиенте, если контракт загружен
  const {
    data: client,
    isLoading: isClientLoading
  } = useGetClientQuery(
    contract?.client,
    { skip: !contract?.client }
  );

  const handleBack = () => {
    navigate('/documents');
  };

  const handleDelete = async () => {
    try {
      await deleteContract(id).unwrap();
      message.success('Договор успешно удален');
      navigate('/documents');
    } catch (error) {
      console.error('Failed to delete contract:', error);
      message.error('Не удалось удалить договор');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'dd.MM.yyyy', { locale: ru });
    } catch (e) {
      return dateString;
    }
  };

  const getStatusTag = (status) => {
    const statusColors = {
      'Подписан': 'green',
      'Не подписан': 'red',
      'На согласовании': 'orange'
    };
    return (
      <Tag color={statusColors[status] || 'default'}>
        {status}
      </Tag>
    );
  };

  if (isContractLoading || isClientLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (contractError) {
    return (
      <div style={{ padding: '20px' }}>
        <Button type="link" onClick={handleBack} icon={<ArrowLeftOutlined />} style={{ marginBottom: 16 }}>
          Назад к списку договоров
        </Button>
        <Alert
          message="Ошибка"
          description="Не удалось загрузить данные договора"
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Верхняя панель с навигацией и действиями */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Button type="link" onClick={handleBack} icon={<ArrowLeftOutlined />}>
            Назад к списку договоров
          </Button>
        </Col>
        <Col>
          <Space>
            <Button type="default" icon={<EditOutlined />}>
              Редактировать
            </Button>
            <Popconfirm
              title="Вы уверены, что хотите удалить этот договор?"
              onConfirm={handleDelete}
              okText="Да"
              cancelText="Нет"
              placement="bottomRight"
            >
              <Button danger icon={<DeleteOutlined />}>
                Удалить
              </Button>
            </Popconfirm>
          </Space>
        </Col>
      </Row>

      {/* Заголовок договора */}
      <Card style={{ marginBottom: 16 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              Договор №{contract?.number}
            </Title>
            <Text type="secondary">
              от {formatDate(contract?.date)}
            </Text>
          </Col>
          <Col>
            {getStatusTag(contract?.status)}
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* Левая колонка - основная информация */}
        <Col span={16}>
          <Card title="Информация о договоре" style={{ marginBottom: 16 }}>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Номер договора">{contract?.number || '-'}</Descriptions.Item>
              <Descriptions.Item label="Название">{contract?.name || '-'}</Descriptions.Item>
              <Descriptions.Item label="Дата">{formatDate(contract?.date)}</Descriptions.Item>
              <Descriptions.Item label="Клиент">{client?.name || '-'}</Descriptions.Item>
              <Descriptions.Item label="Статус">{getStatusTag(contract?.status)}</Descriptions.Item>
              {contract?.igk_number && (
                <Descriptions.Item label="Номер ИГК">{contract?.igk_number}</Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          <Card title="Связанные документы" style={{ marginBottom: 16 }}>
            <Alert
              message="Информация"
              description="К данному договору пока не привязано документов"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Button type="dashed" icon={<FileAddOutlined />} block>
              Добавить спецификацию
            </Button>
          </Card>
        </Col>

        {/* Правая колонка - файл и действия */}
        <Col span={8}>
          <Card title="Файл договора" style={{ marginBottom: 16 }}>
            {contract?.file ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  icon={<FilePdfOutlined />}
                  href={`http://localhost:8000${contract.file}`}
                  target="_blank"
                  block
                >
                  Открыть файл договора
                </Button>
              </Space>
            ) : (
              <Alert
                message="Внимание"
                description="К договору не прикреплен файл"
                type="warning"
                showIcon
              />
            )}
          </Card>

          <Card title="Информация о клиенте" style={{ marginBottom: 16 }}>
            {client ? (
              <>
                <p><strong>Наименование:</strong> {client.name}</p>
                <p><strong>Email:</strong> {client.email}</p>
                <p><strong>Телефон:</strong> {client.phone}</p>
                {client.inn && <p><strong>ИНН:</strong> {client.inn}</p>}
                <Button
                  type="link"
                  onClick={() => navigate(`/card/${client.id}`)}
                  style={{ padding: 0 }}
                >
                  Перейти к карточке клиента
                </Button>
              </>
            ) : (
              <Text type="secondary">Информация о клиенте недоступна</Text>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ContractDetailPage;
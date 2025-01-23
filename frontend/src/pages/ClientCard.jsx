// src/pages/ClientCard.jsx
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetClientQuery } from '../api/clientsApi';
import {
    Row,
    Col,
    Spin,
    Alert,
    Typography,
    Tag,
    Button,
    Descriptions,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

// Объект для перевода названий полей
const fieldLabels = {
    name: 'Название',
    company: 'Компания',
    phone: 'Телефон',
    email: 'E-mail',
    director_full_name: 'Директор ФИО',
    director_position: 'Директор Должность',
    director_basis: 'Основание директора',
    signatory_full_name: 'Подписант ФИО',
    signatory_position: 'Подписант Должность',
    signatory_basis: 'Основание подписанта',
    contact_person: 'Контактное лицо',
    contact_name: 'Имя контакта',
    contact_phone: 'Телефон контакта',
    group: 'Группа',
    client_type: 'Вид клиента',
    inn: 'ИНН',
    created_at: 'Дата создания',
};

// Объект для перевода типов клиентов
const clientTypeMap = {
    LEGAL: 'Юридическое лицо',
    IP: 'Индивидуальный предприниматель',
};

const ClientCard = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { data: client, isLoading, isError } = useGetClientQuery(id);

    // Форматирование даты в формат ДД.ММ.ГГ
    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = String(date.getFullYear()).slice(-2);
        return `${day}.${month}.${year}`;
    };

    if (isLoading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>Загрузка...</div>
            </div>
        );
    }

    if (isError) {
        return (
            <Alert
                message="Ошибка"
                description="Не удалось загрузить данные клиента."
                type="error"
                showIcon
                style={{ margin: '20px' }}
            />
        );
    }

    // Фильтрация полей: исключаем 'id' и 'tags', и оставляем только заполненные
    const filteredFields = Object.entries(client).filter(
        ([key, value]) =>
            key !== 'id' &&
            key !== 'tags' &&
            value !== null &&
            value !== '' &&
            !(key === 'client_type' && !client.client_type) &&
            !(key === 'inn' && !client.inn) &&
            !(key === 'created_at' && !client.created_at)
    );

    return (
        <div style={{ padding: '20px' }}>
            {/* Кнопка Назад */}
            <Button
                type="link"
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate(-1)}
                style={{ marginBottom: '20px' }}
            >
                Назад
            </Button>

            {/* Заголовок с именем клиента */}
            <Title level={2}>{client.name}</Title>

            <Row gutter={16}>
                {/* Левый блок реквизитов */}
                <Col xs={24} md={8}>
                    <div style={{ position: 'relative', padding: '20px', background: '#f0f2f5', borderRadius: '8px' }}>
                        {/* Теги в правом верхнем углу */}
                        {client.tags && client.tags.length > 0 && (
                            <div style={{ position: 'absolute', top: '20px', right: '20px' }}>
                                {client.tags.map(tag => (
                                    <Tag color="blue" key={tag.id}>{tag.name}</Tag>
                                ))}
                            </div>
                        )}
                        <Title level={4}>Реквизиты</Title>
                        <Descriptions column={1} bordered size="small">
                            {filteredFields.map(([key, value]) => {
                                let displayValue = value;

                                // Обработка связанных объектов
                                if (typeof value === 'object' && value !== null) {
                                    displayValue = value.name || JSON.stringify(value);
                                }

                                // Специальная обработка для client_type, inn и created_at
                                if (key === 'client_type') {
                                    displayValue = clientTypeMap[value] || value;
                                }

                                if (key === 'created_at') {
                                    displayValue = formatDate(value);
                                }

                                return (
                                    <Descriptions.Item key={key} label={fieldLabels[key] || key}>
                                        {displayValue}
                                    </Descriptions.Item>
                                );
                            })}

                            {/* Специальная обработка для client_type, inn и created_at */}
                            {client.client_type && (
                                <Descriptions.Item label={fieldLabels['client_type']}>
                                    {clientTypeMap[client.client_type] || client.client_type}
                                </Descriptions.Item>
                            )}

                            {client.inn && (
                                <Descriptions.Item label={fieldLabels['inn']}>
                                    {client.inn}
                                </Descriptions.Item>
                            )}

                            {client.created_at && (
                                <Descriptions.Item label={fieldLabels['created_at']}>
                                    {formatDate(client.created_at)}
                                </Descriptions.Item>
                            )}
                        </Descriptions>
                    </div>
                </Col>

                {/* Правый блок рабочей области */}
                <Col xs={24} md={16}>
                    <div style={{ padding: '20px', background: '#fff', borderRadius: '8px', minHeight: '400px' }}>
                        {/* Рабочая область - пока пусто */}
                        <Title level={4}>Рабочая область</Title>
                        <p>Здесь будет содержимое рабочей области.</p>
                    </div>
                </Col>
            </Row>
        </div>
    );
};

export default ClientCard;
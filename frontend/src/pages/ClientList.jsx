// src/pages/ClientList.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { useGetClientsQuery, useDeleteClientMutation } from '../api/clientsApi';
import { Link } from 'react-router-dom';
import {
    Table,
    Input,
    Button,
    Space,
    Spin,
    Alert,
    Pagination,
    message,
    Popconfirm,
    Row,
    Col,
    Tooltip,
} from 'antd';
import { SearchOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'; // Добавляем EditOutlined
import 'antd/dist/reset.css'; // Убедитесь, что стили Ant Design импортированы

const { Search } = Input;

const ClientList = () => {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const { data: response, isLoading, isError } = useGetClientsQuery({ page, search });
    const [deleteClient] = useDeleteClientMutation();

    // Обработчик изменения страницы
    const handlePageChange = (pageNumber) => {
        setPage(pageNumber);
    };

    // Обработчик поиска с задержкой (debounce)
    const [searchTerm, setSearchTerm] = useState(search);
    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            setSearch(searchTerm);
            setPage(1); // Сбросить на первую страницу при новом поиске
        }, 500); // Задержка 500 мс

        return () => clearTimeout(delayDebounceFn);
    }, [searchTerm]);

    // Обработчик удаления клиента
    const handleDelete = async (id) => {
        try {
            await deleteClient(id).unwrap();
            message.success('Клиент удален успешно');
            // Нет необходимости вызывать refetch(), RTK Query сам перезапросит данные
        } catch (error) {
            message.error('Не удалось удалить клиента');
        }
    };

    // Определение колонок для таблицы
    const columns = useMemo(() => [
        {
            title: 'Имя',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => <Link to={`/card/${record.id}`}>{text}</Link>, // Изменили маршрут на /card/:id
            sorter: (a, b) => a.name.localeCompare(b.name),
        },
        {
            title: 'Компания',
            dataIndex: 'company',
            key: 'company',
            sorter: (a, b) => (a.company || '').localeCompare(b.company || ''),
        },
        {
            title: 'Телефон',
            dataIndex: 'phone',
            key: 'phone',
            sorter: (a, b) => a.phone.localeCompare(b.phone),
        },
        {
            title: 'E-mail',
            dataIndex: 'email',
            key: 'email',
            sorter: (a, b) => a.email.localeCompare(b.email),
        },
        {
            title: 'Действия',
            key: 'actions',
            render: (_, record) => (
                <Space size="middle">
                    <Link to={`/edit/${record.id}`}>
                        <Tooltip title="Редактировать">
                            <Button type="link" icon={<EditOutlined />} />
                        </Tooltip>
                    </Link>
                    <Popconfirm
                        title="Вы уверены, что хотите удалить этого клиента?"
                        onConfirm={() => handleDelete(record.id)}
                        okText="Да"
                        cancelText="Нет"
                    >
                        <Tooltip title="Удалить">
                            <Button type="link" danger icon={<DeleteOutlined />} />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ], [handleDelete]);

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
                description="Не удалось загрузить данные."
                type="error"
                showIcon
                style={{ margin: '20px' }}
            />
        );
    }

    return (
        <div style={{ padding: '20px' }}>
            {/* Используем Row и Col для лучшего управления макетом */}
            <Row justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
                <Col flex="auto" style={{ marginRight: '16px' }}>
                    <Search
                        placeholder="Поиск по имени, телефону, email..."
                        onChange={(e) => setSearchTerm(e.target.value)}
                        enterButton={<SearchOutlined />}
                        allowClear
                        style={{ width: '100%' }} // Растягиваем на всю ширину доступного пространства
                    />
                </Col>
                <Col flex="none">
                    <Link to="/create">
                        <Button type="primary" icon={<PlusOutlined />}>
                            Добавить клиента
                        </Button>
                    </Link>
                </Col>
            </Row>

            <Table
                rowKey="id"
                columns={columns}
                dataSource={response?.results}
                pagination={false}
                bordered
            />

            <Pagination
                current={page}
                pageSize={10} // Установите соответствующий pageSize в зависимости от вашего API
                total={response?.count}
                onChange={handlePageChange}
                showSizeChanger={false}
                showQuickJumper
                style={{ marginTop: '20px', textAlign: 'right' }}
            />
        </div>
    );
};

export default ClientList;
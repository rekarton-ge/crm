// src/pages/ClientForm.jsx

import React, { useEffect, useCallback } from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
    useCreateClientMutation,
    useUpdateClientMutation,
    useGetClientQuery,
    useGetClientGroupsQuery,
    useGetTagsQuery,
} from '../api/clientsApi';
import { useNavigate, useParams } from 'react-router-dom';
import {
    Form,
    Input,
    Select,
    Radio,
    Button,
    Spin,
    Alert,
    message,
    Space,
    Row,
    Col,
    Modal,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import 'antd/dist/reset.css'; // Убедитесь, что стили Ant Design импортированы

const { Option } = Select;

const ClientForm = () => {
    const { id } = useParams(); // Получаем ID клиента из URL (если он есть)
    const navigate = useNavigate(); // Хук для навигации

    // Запросы данных
    const { data: client, isLoading: isClientLoading, error: clientError } = useGetClientQuery(id, { skip: !id }); // Загружаем данные клиента, если ID есть
    const {
        data: groups = [],
        isLoading: isGroupsLoading,
        error: groupsError,
    } = useGetClientGroupsQuery(); // Загружаем список групп
    const {
        data: tags = [],
        isLoading: isTagsLoading,
        error: tagsError,
    } = useGetTagsQuery(); // Загружаем список тегов

    // Мутации для создания и обновления клиента
    const [createClient] = useCreateClientMutation();
    const [updateClient] = useUpdateClientMutation();

    // Определяем, в режиме ли редактирования
    const isEditMode = Boolean(id);

    // Проверка загрузки данных клиента и других зависимостей
    const isLoading = isEditMode ? isClientLoading || isGroupsLoading || isTagsLoading : isGroupsLoading || isTagsLoading;
    const hasError = clientError || groupsError || tagsError;

    // Инициализация Formik с enableReinitialize
    const formik = useFormik({
        enableReinitialize: true, // Позволяет Formik обновлять initialValues при их изменении
        initialValues: isEditMode && client ? {
            client_type: client.client_type,
            name: client.name,
            company: client.company || '',
            phone: client.phone,
            email: client.email,
            inn: client.inn || '',
            legal_address: client.legal_address || '',
            fact_address: client.fact_address || '',
            kpp: client.kpp || '',
            ogrn: client.ogrn || '',
            account_number: client.account_number || '',
            correspondent_account: client.correspondent_account || '',
            bik: client.bik || '',
            bank_name: client.bank_name || '',
            director_full_name: client.director_full_name || '',
            director_position: client.director_position || '',
            director_basis: client.director_basis || '',
            signatory_full_name: client.signatory_full_name || '',
            signatory_position: client.signatory_position || '',
            signatory_basis: client.signatory_basis || '',
            contact_person: client.contact_person || '',
            contact_name: client.contact_name || '',
            contact_phone: client.contact_phone || '',
            group_id: client.group?.id || null, // Группа может быть null
            tag_ids: client.tags?.map(tag => tag.id) || [], // Массив ID тегов
        } : {
            client_type: 'LEGAL', // По умолчанию "Юридическое лицо"
            name: '',
            company: '',
            phone: '',
            email: '',
            inn: '',
            legal_address: '',
            fact_address: '',
            kpp: '',
            ogrn: '',
            account_number: '',
            correspondent_account: '',
            bik: '',
            bank_name: '',
            director_full_name: '',
            director_position: '',
            director_basis: '',
            signatory_full_name: '',
            signatory_position: '',
            signatory_basis: '',
            contact_person: '',
            contact_name: '',
            contact_phone: '',
            group_id: null, // Группа может быть null
            tag_ids: [], // Теги могут быть пустым массивом
        },
        // Схема валидации
        validationSchema: Yup.object({
            name: Yup.string().required('Обязательное поле'),
            email: Yup.string().email('Некорректный email').required('Обязательное поле'),
            phone: Yup.string().required('Обязательное поле'),
            group_id: Yup.string().nullable(), // Группа не обязательна
            tag_ids: Yup.array().nullable(), // Теги не обязательны
        }),
        // Обработчик отправки формы
        onSubmit: async (values) => {
            try {
                if (isEditMode) {
                    await updateClient({ id, ...values }).unwrap(); // Обновляем клиента
                    message.success('Клиент успешно обновлен');
                } else {
                    await createClient(values).unwrap(); // Создаем нового клиента
                    message.success('Клиент успешно создан');
                }
                navigate('/'); // Перенаправляем на страницу со списком клиентов
            } catch (error) {
                console.error('Ошибка при сохранении клиента:', error); // Логируем ошибку
                message.error('Не удалось сохранить клиента');
            }
        },
    });

    // Добавление логов для отладки (опционально)
    useEffect(() => {
        if (isEditMode) {
            console.log('Client data:', client);
        }
        console.log('Formik initialValues:', formik.initialValues);
    }, [client, isEditMode, formik.initialValues]);

    // Обработчик кнопки "Назад" с подтверждением
    const handleBack = useCallback(() => {
        Modal.confirm({
            title: 'Вы уверены, что хотите вернуться назад?',
            content: 'Все несохраненные изменения будут потеряны.',
            okText: 'Да',
            cancelText: 'Нет',
            onOk: () => navigate('/'),
        });
    }, [navigate]);

    // Условный рендеринг: отображаем форму только если данные загружены и нет ошибок
    if (isLoading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
                <div>{isEditMode ? 'Загрузка данных клиента...' : 'Загрузка данных...'}</div>
            </div>
        );
    }

    if (hasError) {
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
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <h1>{isEditMode ? 'Редактирование клиента' : 'Создание клиента'}</h1>
            <Form
                layout="vertical"
                onFinish={formik.handleSubmit}
                // Удаляем initialValues, чтобы избежать конфликтов
            >
                <Row gutter={16}>
                    {/* Вид клиента */}
                    <Col span={12}>
                        <Form.Item label="Вид клиента">
                            <Radio.Group
                                name="client_type"
                                onChange={formik.handleChange}
                                value={formik.values.client_type}
                            >
                                <Radio value="IP">Индивидуальный предприниматель</Radio>
                                <Radio value="LEGAL">Юридическое лицо</Radio>
                            </Radio.Group>
                        </Form.Item>
                    </Col>

                    {/* Наименование клиента */}
                    <Col span={12}>
                        <Form.Item
                            label="Наименование клиента"
                            validateStatus={formik.touched.name && formik.errors.name ? 'error' : ''}
                            help={formik.touched.name && formik.errors.name ? formik.errors.name : null}
                        >
                            <Input
                                name="name"
                                value={formik.values.name}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur}
                                placeholder="Введите наименование клиента"
                                autoFocus
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Остальные поля формы */}
                <Row gutter={16}>
                    {/* Компания */}
                    <Col span={12}>
                        <Form.Item label="Компания">
                            <Input
                                name="company"
                                value={formik.values.company}
                                onChange={formik.handleChange}
                                placeholder="Введите название компании"
                            />
                        </Form.Item>
                    </Col>

                    {/* Телефон */}
                    <Col span={12}>
                        <Form.Item
                            label="Телефон"
                            validateStatus={formik.touched.phone && formik.errors.phone ? 'error' : ''}
                            help={formik.touched.phone && formik.errors.phone ? formik.errors.phone : null}
                        >
                            <Input
                                name="phone"
                                value={formik.values.phone}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur}
                                placeholder="Введите номер телефона"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                <Row gutter={16}>
                    {/* Email */}
                    <Col span={12}>
                        <Form.Item
                            label="Email"
                            validateStatus={formik.touched.email && formik.errors.email ? 'error' : ''}
                            help={formik.touched.email && formik.errors.email ? formik.errors.email : null}
                        >
                            <Input
                                name="email"
                                type="email"
                                value={formik.values.email}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur}
                                placeholder="Введите email"
                            />
                        </Form.Item>
                    </Col>

                    {/* ИНН */}
                    <Col span={12}>
                        <Form.Item label="ИНН">
                            <Input
                                name="inn"
                                value={formik.values.inn}
                                onChange={formik.handleChange}
                                placeholder="Введите ИНН"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Адреса */}
                <Row gutter={16}>
                    {/* Юридический адрес */}
                    <Col span={12}>
                        <Form.Item label="Юридический адрес">
                            <Input
                                name="legal_address"
                                value={formik.values.legal_address}
                                onChange={formik.handleChange}
                                placeholder="Введите юридический адрес"
                            />
                        </Form.Item>
                    </Col>

                    {/* Фактический адрес */}
                    <Col span={12}>
                        <Form.Item label="Фактический адрес">
                            <Input
                                name="fact_address"
                                value={formik.values.fact_address}
                                onChange={formik.handleChange}
                                placeholder="Введите фактический адрес"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Финансовая информация */}
                <Row gutter={16}>
                    {/* КПП */}
                    <Col span={8}>
                        <Form.Item label="КПП">
                            <Input
                                name="kpp"
                                value={formik.values.kpp}
                                onChange={formik.handleChange}
                                placeholder="Введите КПП"
                                disabled={formik.values.client_type === 'IP'}
                            />
                        </Form.Item>
                    </Col>

                    {/* ОГРН */}
                    <Col span={8}>
                        <Form.Item label="ОГРН">
                            <Input
                                name="ogrn"
                                value={formik.values.ogrn}
                                onChange={formik.handleChange}
                                placeholder="Введите ОГРН"
                            />
                        </Form.Item>
                    </Col>

                    {/* Расчётный счёт */}
                    <Col span={8}>
                        <Form.Item label="Расчётный счёт">
                            <Input
                                name="account_number"
                                value={formik.values.account_number}
                                onChange={formik.handleChange}
                                placeholder="Введите расчётный счёт"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                <Row gutter={16}>
                    {/* Корреспондентский счёт */}
                    <Col span={8}>
                        <Form.Item label="Корреспондентский счёт">
                            <Input
                                name="correspondent_account"
                                value={formik.values.correspondent_account}
                                onChange={formik.handleChange}
                                placeholder="Введите корреспондентский счёт"
                            />
                        </Form.Item>
                    </Col>

                    {/* БИК Банка */}
                    <Col span={8}>
                        <Form.Item label="БИК Банка">
                            <Input
                                name="bik"
                                value={formik.values.bik}
                                onChange={formik.handleChange}
                                placeholder="Введите БИК Банка"
                            />
                        </Form.Item>
                    </Col>

                    {/* Наименование Банка */}
                    <Col span={8}>
                        <Form.Item label="Наименование Банка">
                            <Input
                                name="bank_name"
                                value={formik.values.bank_name}
                                onChange={formik.handleChange}
                                placeholder="Введите наименование банка"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Директор */}
                <Row gutter={16}>
                    {/* ФИО Директора */}
                    <Col span={8}>
                        <Form.Item label="ФИО Директора">
                            <Input
                                name="director_full_name"
                                value={formik.values.director_full_name}
                                onChange={formik.handleChange}
                                placeholder="Введите ФИО директора"
                            />
                        </Form.Item>
                    </Col>

                    {/* Должность Директора */}
                    <Col span={8}>
                        <Form.Item label="Должность Директора">
                            <Input
                                name="director_position"
                                value={formik.values.director_position}
                                onChange={formik.handleChange}
                                placeholder="Введите должность директора"
                            />
                        </Form.Item>
                    </Col>

                    {/* Основание */}
                    <Col span={8}>
                        <Form.Item label="Основание">
                            <Input
                                name="director_basis"
                                value={formik.values.director_basis}
                                onChange={formik.handleChange}
                                placeholder="Введите основание директора"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Подписант */}
                <Row gutter={16}>
                    {/* ФИО Подписанта */}
                    <Col span={8}>
                        <Form.Item label="ФИО Подписанта">
                            <Input
                                name="signatory_full_name"
                                value={formik.values.signatory_full_name}
                                onChange={formik.handleChange}
                                placeholder="Введите ФИО подписанта"
                            />
                        </Form.Item>
                    </Col>

                    {/* Должность Подписанта */}
                    <Col span={8}>
                        <Form.Item label="Должность Подписанта">
                            <Input
                                name="signatory_position"
                                value={formik.values.signatory_position}
                                onChange={formik.handleChange}
                                placeholder="Введите должность подписанта"
                            />
                        </Form.Item>
                    </Col>

                    {/* Основание Подписанта */}
                    <Col span={8}>
                        <Form.Item label="Основание Подписанта">
                            <Input
                                name="signatory_basis"
                                value={formik.values.signatory_basis}
                                onChange={formik.handleChange}
                                placeholder="Введите основание подписанта"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Контактное лицо */}
                <Row gutter={16}>
                    {/* Контактное лицо компании */}
                    <Col span={8}>
                        <Form.Item label="Контактное лицо компании">
                            <Input
                                name="contact_person"
                                value={formik.values.contact_person}
                                onChange={formik.handleChange}
                                placeholder="Введите контактное лицо компании"
                            />
                        </Form.Item>
                    </Col>

                    {/* Имя контактного лица */}
                    <Col span={8}>
                        <Form.Item label="Имя контактного лица">
                            <Input
                                name="contact_name"
                                value={formik.values.contact_name}
                                onChange={formik.handleChange}
                                placeholder="Введите имя контактного лица"
                            />
                        </Form.Item>
                    </Col>

                    {/* Телефон контактного лица */}
                    <Col span={8}>
                        <Form.Item label="Телефон контактного лица">
                            <Input
                                name="contact_phone"
                                value={formik.values.contact_phone}
                                onChange={formik.handleChange}
                                placeholder="Введите телефон контактного лица"
                            />
                        </Form.Item>
                    </Col>
                </Row>

                {/* Группа и Теги */}
                <Row gutter={16}>
                    {/* Группа */}
                    <Col span={12}>
                        <Form.Item label="Группа">
                            <Select
                                name="group_id"
                                value={formik.values.group_id || undefined}
                                onChange={(value) => formik.setFieldValue('group_id', value)}
                                placeholder="Выберите группу"
                                allowClear
                            >
                                {groups.map(group => (
                                    <Option key={group.id} value={group.id}>
                                        {group.name}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>

                    {/* Теги */}
                    <Col span={12}>
                        <Form.Item label="Теги">
                            <Select
                                mode="multiple"
                                name="tag_ids"
                                value={formik.values.tag_ids}
                                onChange={(value) => formik.setFieldValue('tag_ids', value)}
                                placeholder="Выберите теги"
                                allowClear
                            >
                                {tags.map(tag => (
                                    <Option key={tag.id} value={tag.id}>
                                        {tag.name}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                </Row>

                {/* Кнопки отправки и назад */}
                <Form.Item>
                    <Space>
                        <Button type="primary" htmlType="submit">
                            Сохранить
                        </Button>
                        <Button
                            type="default"
                            icon={<ArrowLeftOutlined />}
                            onClick={handleBack}
                        >
                            Назад
                        </Button>
                    </Space>
                </Form.Item>
            </Form>
        </div>
    );

};

export default ClientForm;
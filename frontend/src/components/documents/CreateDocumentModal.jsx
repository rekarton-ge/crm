// src/components/documents/CreateDocumentModal.jsx
import React from 'react';
import { Modal, Button, Space } from 'antd';
import { FileAddOutlined, SnippetsOutlined, FileTextOutlined, FileDoneOutlined } from '@ant-design/icons';

const CreateDocumentModal = ({ visible, onCancel, onSelectDocumentType }) => {
  return (
    <Modal
      title="Выберите тип документа"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Button
          type="default"
          icon={<FileAddOutlined />}
          onClick={() => onSelectDocumentType('contract')}
          style={{ width: '100%', textAlign: 'left', height: '50px' }}
        >
          Создать договор
        </Button>
        <Button
          type="default"
          icon={<SnippetsOutlined />}
          onClick={() => onSelectDocumentType('specification')}
          style={{ width: '100%', textAlign: 'left', height: '50px' }}
        >
          Создать спецификацию
        </Button>
        <Button
          type="default"
          icon={<FileTextOutlined />}
          onClick={() => onSelectDocumentType('invoice')}
          style={{ width: '100%', textAlign: 'left', height: '50px' }}
        >
          Создать счет на оплату
        </Button>
        <Button
          type="default"
          icon={<FileDoneOutlined />}
          onClick={() => onSelectDocumentType('upd')}
          style={{ width: '100%', textAlign: 'left', height: '50px' }}
        >
          Создать УПД
        </Button>
      </Space>
    </Modal>
  );
};

export default CreateDocumentModal;
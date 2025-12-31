/**
 * 数据编辑弹窗组件
 * 用于新增或编辑数据
 */

import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, InputNumber, message, Divider, Typography } from 'antd';
import { createData, updateData } from '@/services/data';
import { CATEGORY_ICONS, CATEGORY_NAMES, CATEGORY_COLORS } from '@/config/constants';
import type { ExperimentalData, DatasetSchemaResponse, Field } from '@/types';
import './DataEditModal.css';

const { Title } = Typography;

/**
 * 数据编辑弹窗 Props
 */
interface DataEditModalProps {
  visible: boolean;
  datasetId: string;
  schema: DatasetSchemaResponse;
  data: ExperimentalData | null; // null 表示新增，非 null 表示编辑
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * 数据编辑弹窗组件
 */
const DataEditModal: React.FC<DataEditModalProps> = ({
  visible,
  datasetId,
  schema,
  data,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const isEditing = !!data;

  /**
   * 当弹窗打开时，设置表单初始值
   */
  useEffect(() => {
    if (visible && data) {
      form.setFieldsValue(data);
    } else if (visible) {
      form.resetFields();
    }
  }, [visible, data, form]);

  /**
   * 处理表单提交
   */
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      setLoading(true);

      if (isEditing) {
        // 更新数据
        await updateData(datasetId, data.id, values);
        message.success('数据更新成功');
      } else {
        // 创建数据
        await createData(datasetId, values);
        message.success('数据创建成功');
      }

      onSuccess();
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        message.error('请检查表单填写是否正确');
      } else {
        console.error('保存数据失败:', error);
        const errorMsg = error.response?.data?.detail || error.message || '保存数据失败';
        message.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * 根据字段类型渲染表单项
   */
  const renderFormItem = (field: Field) => {
    const isRequired = schema.required_fields.includes(field.name);
    const displayName = field.display_name || field.name;
    const label = field.unit ? `${displayName} (${field.unit})` : displayName;

    // 判断字段类型
    const isNumeric = field.type === 'float' || field.type === 'int' || field.type === 'decimal';

    return (
      <Form.Item
        key={field.name}
        name={field.name}
        label={label}
        rules={[
          {
            required: isRequired,
            message: `请输入${displayName}`,
          },
        ]}
      >
        {isNumeric ? (
          <InputNumber
            style={{ width: '100%' }}
            placeholder={`请输入${displayName}`}
            precision={field.type === 'int' ? 0 : 2}
          />
        ) : (
          <Input placeholder={`请输入${displayName}`} />
        )}
      </Form.Item>
    );
  };

  /**
   * 按分类渲染字段
   */
  const renderFieldsByCategory = () => {
    // 将字段按分类分组，处理没有分类的情况
    const groupedFields: Record<string, Field[]> = {};
    
    schema.fields.forEach(field => {
      const cat = field.category || '其他';
      if (!groupedFields[cat]) {
        groupedFields[cat] = [];
      }
      groupedFields[cat].push(field);
    });

    // 按照 CATEGORY_NAMES 的顺序渲染，确保顺序一致
    return Object.keys(CATEGORY_NAMES).map(category => {
      const fields = groupedFields[category];
      if (!fields || fields.length === 0) return null;

      const icon = CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS];
      const name = CATEGORY_NAMES[category as keyof typeof CATEGORY_NAMES];
      const color = CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS];

      return (
        <div key={category} className="field-category">
          <Divider orientation="left">
            <span style={{ color, fontWeight: 'bold', fontSize: '16px' }}>
              {icon} {name}
            </span>
          </Divider>
          <div className="field-grid">
            {fields.map(field => renderFormItem(field))}
          </div>
        </div>
      );
    });
  };

  return (
    <Modal
      title={
        <Title level={4} style={{ margin: 0 }}>
          {isEditing ? `📝 编辑数据 (ID: ${data.id})` : '➕ 新增数据'}
        </Title>
      }
      open={visible}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={800}
      okText="保存"
      cancelText="取消"
      className="data-edit-modal"
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        className="data-edit-form"
        autoComplete="off"
      >
        {renderFieldsByCategory()}
      </Form>
    </Modal>
  );
};

export default DataEditModal;

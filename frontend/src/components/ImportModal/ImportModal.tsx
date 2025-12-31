/**
 * CSV 导入弹窗组件
 * 支持文件上传、数据集选择、导入预览
 */

import React, { useState, useMemo, useEffect } from 'react';
import {
  Modal,
  Upload,
  Radio,
  Input,
  Select,
  Alert,
  Typography,
  Space,
  message,
  Progress,
} from 'antd';
import { InboxOutlined, FileExcelOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd';
import { importFile } from '@/services/data';
import { UPLOAD_CONFIG } from '@/config/constants';
import type { Dataset, BatchImportResponse } from '@/types';
import './ImportModal.css';

const { Title, Text } = Typography;
const { Dragger } = Upload;

/**
 * 导入模式
 */
type ImportMode = 'new' | 'append';

/**
 * 导入弹窗 Props
 */
interface ImportModalProps {
  visible: boolean;
  currentDatasetId: string | null;
  datasets: Dataset[];
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * CSV 导入弹窗组件
 */
const ImportModal: React.FC<ImportModalProps> = ({
  visible,
  currentDatasetId,
  datasets,
  onClose,
  onSuccess,
}) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [importMode, setImportMode] = useState<ImportMode>('new');
  const [newDatasetName, setNewDatasetName] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [importResult, setImportResult] = useState<BatchImportResponse | null>(null);

  // 当弹窗打开且有当前数据集时，默认选中
  useEffect(() => {
    if (visible && currentDatasetId) {
      setSelectedDatasetId(currentDatasetId);
      setImportMode('append');
    } else if (visible) {
      setSelectedDatasetId('');
      setImportMode('new');
    }
  }, [visible, currentDatasetId]);

  /**
   * 缓存数据集选项，避免重复计算
   */
  const datasetOptions = useMemo(() => {
    return datasets.map(d => ({
      label: d.display_name,
      value: d.id,
    }));
  }, [datasets]);

  /**
   * 重置表单
   */
  const resetForm = () => {
    setFileList([]);
    setImportMode('new');
    setNewDatasetName('');
    setSelectedDatasetId(currentDatasetId || '');
    setImportResult(null);
  };

  /**
   * 处理文件变化
   */
  const handleFileChange = (info: any) => {
    // 优化：只在文件列表真正变化时更新状态
    const { fileList: newFiles } = info;
    setFileList(newFiles.slice(-1));
  };

  /**
   * 文件上传前的检查
   */
  const beforeUpload = (file: File) => {
    // 检查文件大小
    const isLtMaxSize = file.size <= UPLOAD_CONFIG.MAX_SIZE;
    if (!isLtMaxSize) {
      message.error(`文件大小不能超过 ${UPLOAD_CONFIG.MAX_SIZE / 1024 / 1024}MB`);
      return Upload.LIST_IGNORE;
    }

    // 检查文件类型
    const fileExt = file.name.toLowerCase().split('.').pop();
    const isValidType = fileExt && UPLOAD_CONFIG.ACCEPTED_TYPES.some(type => type.includes(fileExt));
    if (!isValidType) {
      message.error('只支持 CSV 和 Excel 文件格式');
      return Upload.LIST_IGNORE;
    }

    return false; // 阻止自动上传
  };

  /**
   * 处理导入
   */
  const handleImport = async () => {
    if (fileList.length === 0) {
      message.warning('请选择要导入的文件');
      return;
    }

    const fileObj = fileList[0].originFileObj || (fileList[0] as unknown as File);
    if (!fileObj) {
      message.error('文件对象无效，请重新选择');
      return;
    }

    if (importMode === 'new' && !newDatasetName.trim()) {
      message.warning('请输入新数据集名称');
      return;
    }

    if (importMode === 'append' && !selectedDatasetId) {
      message.warning('请选择要追加的数据集');
      return;
    }

    const targetDatasetId = importMode === 'new' ? newDatasetName.trim() : selectedDatasetId;

    setLoading(true);
    try {
      const result = await importFile(targetDatasetId, fileObj as File);
      setImportResult(result);
      message.success('文件导入成功！');
      
      // 延迟关闭，显示导入结果
      setTimeout(() => {
        onSuccess();
        resetForm();
      }, 2000);
    } catch (error) {
      console.error('导入失败:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理弹窗关闭
   */
  const handleClose = () => {
    if (!loading) {
      resetForm();
      onClose();
    }
  };

  /**
   * 计算导入成功率
   */
  const getSuccessRate = (): number => {
    if (!importResult || importResult.total === 0) return 0;
    return Math.min(100, Math.round((importResult.success / importResult.total) * 100));
  };

  return (
    <Modal
      title={
        <Title level={4} style={{ margin: 0 }}>
          📥 数据导入向导
        </Title>
      }
      open={visible}
      onCancel={handleClose}
      onOk={handleImport}
      confirmLoading={loading}
      width={600}
      okText="确认导入"
      cancelText="取消"
      className="import-modal"
      destroyOnClose
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 步骤1：选择文件 */}
        <div>
          <Text strong>1. 选择文件</Text>
          <Dragger
            fileList={fileList}
            onChange={handleFileChange}
            beforeUpload={beforeUpload}
            accept={UPLOAD_CONFIG.ACCEPTED_TYPES.join(',')}
            maxCount={1}
            style={{ marginTop: 8 }}
            customRequest={() => {}} // 阻止默认上传行为
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 CSV 和 Excel 格式，文件大小不超过 {UPLOAD_CONFIG.MAX_SIZE / 1024 / 1024}MB
            </p>
          </Dragger>

          {fileList.length > 0 && (
            <div className="file-info">
              <FileExcelOutlined style={{ color: '#52c41a', fontSize: 24 }} />
              <div>
                <Text strong>{fileList[0].name}</Text>
                <br />
                <Text type="secondary">{(fileList[0].size! / 1024).toFixed(2)} KB</Text>
              </div>
            </div>
          )}
        </div>

        {/* 步骤2：导入目标 */}
        <div>
          <Text strong>2. 导入目标</Text>
          <Radio.Group
            value={importMode}
            onChange={e => setImportMode(e.target.value)}
            style={{ marginTop: 8, width: '100%' }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Radio value="new">
                <Text strong>新建数据集 (New Table)</Text>
              </Radio>
              {importMode === 'new' && (
                <Input
                  placeholder="输入新数据集名称，如: batch_5"
                  value={newDatasetName}
                  onChange={e => setNewDatasetName(e.target.value)}
                  style={{ marginLeft: 24, width: 'calc(100% - 24px)' }}
                />
              )}

              <Radio value="append">
                <Text strong>追加到现有数据集 (Append)</Text>
              </Radio>
              {importMode === 'append' && (
                <Select
                  placeholder="选择数据集"
                  value={selectedDatasetId}
                  onChange={setSelectedDatasetId}
                  style={{ marginLeft: 24, width: 'calc(100% - 24px)' }}
                  options={datasetOptions}
                />
              )}
            </Space>
          </Radio.Group>
        </div>

        {/* 提示信息 */}
        {!importResult && (
          <Alert
            message="ℹ️ 预览分析"
            description="系统将自动检测 CSV 表头，识别字段分类（物性、工艺、状态、性能），并验证数据完整性。"
            type="info"
            showIcon
          />
        )}

        {/* 导入结果 */}
        {importResult && (
          <Alert
            message="✅ 导入完成"
            description={
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text>总数据: {importResult.total} 条</Text>
                <Text type="success">成功: {importResult.success} 条</Text>
                {importResult.duplicates > 0 && (
                  <Text type="warning">重复: {importResult.duplicates} 条</Text>
                )}
                {importResult.failed > 0 && (
                  <Text type="danger">失败: {importResult.failed} 条</Text>
                )}
                <Progress percent={getSuccessRate()} status="success" />
                {importResult.dataset_created && (
                  <Text type="success">{importResult.creation_message}</Text>
                )}
              </Space>
            }
            type="success"
            showIcon
          />
        )}
      </Space>
    </Modal>
  );
};

export default ImportModal;

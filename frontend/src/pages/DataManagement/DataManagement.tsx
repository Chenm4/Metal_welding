/**
 * 数据管理页面
 * 展示数据列表、提供搜索、CRUD 功能
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Input,
  Checkbox,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  Progress,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useAuth } from '@/contexts/AuthContext';
import { getDataList, searchData, deleteData, batchDeleteData } from '@/services/data';
import { getDatasetSchema } from '@/services/dataset';
import { getDatasetCoverage } from '@/services/coverage';
import { CATEGORY_COLORS, CATEGORY_NAMES, DEFAULT_PAGE_SIZE } from '@/config/constants';
import DataEditModal from '@/components/DataEditModal/DataEditModal';
import type { ExperimentalData, DatasetSchemaResponse, Field, CoverageResponse } from '@/types';
import type { TableColumnsType, TablePaginationConfig } from 'antd';
import { Resizable } from 'react-resizable';
import 'react-resizable/css/styles.css';
import './DataManagement.css';
import { Tooltip } from 'antd';

const { Text } = Typography;
const { Search } = Input;

/**
 * 可调整列宽的标题组件
 */
const ResizableTitle = (props: any) => {
  const { onResize, width, ...restProps } = props;

  if (!width) {
    return <th {...restProps} />;
  }

  return (
    <Resizable
      width={width}
      height={0}
      handle={
        <span
          className="react-resizable-handle react-resizable-handle-se"
          onClick={e => {
            e.stopPropagation();
          }}
        />
      }
      onResize={onResize}
      draggableOpts={{ enableUserSelectHack: false }}
    >
      <th {...restProps} />
    </Resizable>
  );
};

/**
 * 数据管理页面组件
 */
const DataManagement: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const { isAdmin } = useAuth();

  const [dataList, setDataList] = useState<ExperimentalData[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [loading, setLoading] = useState(false);
  const [schema, setSchema] = useState<DatasetSchemaResponse | null>(null);
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    total: 0,
  });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([
    '物性',
    '工艺',
    '状态',
    '性能',
    '其他',
  ]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingData, setEditingData] = useState<ExperimentalData | null>(null);
  const columnWidths = useRef<Record<string, number>>({});
  const [, forceUpdate] = useState({});

  /**
   * 处理列宽调整
   */
  const handleResize = useCallback((key: string) => {
    return (_: React.SyntheticEvent, { size }: any) => {
      columnWidths.current[key] = size.width;
      forceUpdate({});
    };
  }, []);

  /**
   * 加载数据集结构
   */
  const loadSchema = useCallback(async () => {
    if (!datasetId) return;
    try {
      const response = await getDatasetSchema(datasetId);
      console.log('Loaded schema:', response);
      setSchema(response);
    } catch (error) {
      console.error('加载数据集结构失败:', error);
      message.error('加载数据集结构失败，请检查网络或后端配置');
    }
  }, [datasetId]);

  /**
   * 加载覆盖率统计
   */
  const loadCoverage = useCallback(async () => {
    if (!datasetId) return;
    try {
      const response = await getDatasetCoverage(datasetId);
      setCoverage(response);
    } catch (error) {
      console.error('加载覆盖率失败:', error);
    }
  }, [datasetId]);

  /**
   * 加载数据列表
   */
  const loadData = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    try {
      const response = searchKeyword
        ? await searchData(datasetId, searchKeyword, {
            page: pagination.current,
            page_size: pagination.pageSize,
          })
        : await getDataList(datasetId, {
            page: pagination.current,
            page_size: pagination.pageSize,
          });

      console.log('Loaded data:', response.data);
      setDataList(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total,
      }));
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据列表失败');
    } finally {
      setLoading(false);
    }
  }, [datasetId, pagination.current, pagination.pageSize, searchKeyword]);

  /**
   * 初始化加载
   */
  useEffect(() => {
    if (datasetId) {
      loadSchema();
      loadCoverage();
      // 重置分页和搜索
      setPagination(prev => ({ ...prev, current: 1 }));
      setSearchKeyword('');
    }
  }, [datasetId, loadSchema, loadCoverage]);

  /**
   * 数据加载副作用
   */
  useEffect(() => {
    loadData();
  }, [loadData]);

  /**
   * 处理搜索
   */
  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  /**
   * 处理分页变化
   */
  const handleTableChange = (newPagination: TablePaginationConfig) => {
    setPagination(prev => ({
      ...prev,
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || DEFAULT_PAGE_SIZE,
    }));
  };

  /**
   * 处理新增数据
   */
  const handleCreate = () => {
    setEditingData(null);
    setEditModalVisible(true);
  };

  /**
   * 处理编辑数据
   */
  const handleEdit = useCallback((record: ExperimentalData) => {
    setEditingData(record);
    setEditModalVisible(true);
  }, []);

  /**
   * 处理删除单条数据
   */
  const handleDelete = useCallback(async (id: number) => {
    if (!datasetId) return;
    try {
      await deleteData(datasetId, id);
      message.success('数据删除成功');
      loadData();
      loadCoverage();
    } catch (error) {
      console.error('删除失败:', error);
    }
  }, [datasetId, loadData, loadCoverage]);

  /**
   * 处理批量删除
   */
  const handleBatchDelete = async () => {
    if (!datasetId || selectedRowKeys.length === 0) return;

    try {
      await batchDeleteData(datasetId, selectedRowKeys as number[]);
      message.success(`成功删除 ${selectedRowKeys.length} 条数据`);
      setSelectedRowKeys([]);
      loadData();
      loadCoverage();
    } catch (error) {
      console.error('批量删除失败:', error);
    }
  };

  /**
   * 处理分类筛选
   */
  const handleCategoryChange = (categories: any) => {
    setSelectedCategories(categories as string[]);
  };

  /**
   * 获取要显示的字段（根据分类筛选）
   */
  const visibleFields = useMemo(() => {
    if (!schema) return [];
    return schema.fields.filter(field => {
      const category = field.category || '其他';
      return selectedCategories.includes(category);
    });
  }, [schema, selectedCategories]);

  /**
   * 获取列宽
   */
  const getColumnWidth = useCallback((fieldName: string, defaultWidth: number): number => {
    return columnWidths.current[fieldName] || defaultWidth;
  }, []);

  /**
   * 构建表格列
   */
  const columns = useMemo((): TableColumnsType<ExperimentalData> => {
    const cols: TableColumnsType<ExperimentalData> = [
      {
        title: 'ID',
        dataIndex: 'id',
        key: 'id',
        width: 80,
        fixed: 'left',
        sorter: (a, b) => a.id - b.id,
        onHeaderCell: () => ({
          width: 80,
          onResize: handleResize('id'),
        }),
      },
    ];

    // 动态字段列
    visibleFields.forEach(field => {
      const category = field.category || '其他';
      let displayName = field.display_name || field.name;
      
      // 去除分类前缀 (物性-、工艺-、状态-、性能- 或 物性_、工艺_、状态_、性能_)
      displayName = displayName.replace(/^(物性|工艺|状态|性能)[-_]/, '');
      
      const categoryColor = CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || '#666666';
      
      // 根据列名长度估算初始宽度，最小 80
      const defaultWidth = Math.max(displayName.length * 18 + 30, 80);
      const width = getColumnWidth(field.name, defaultWidth);
      
      // 截断过长的字段名，并用 Tooltip 显示完整名称
      const MAX_FIELD_NAME_LENGTH = 10; // 最大显示字符数
      const truncatedDisplayName = displayName.length > MAX_FIELD_NAME_LENGTH
        ? `${displayName.substring(0, MAX_FIELD_NAME_LENGTH)}...`
        : displayName;
      
      cols.push({
        title: (
          <Tooltip title={displayName}>
            <span style={{ color: categoryColor }}>
              {truncatedDisplayName}
            </span>
          </Tooltip>
        ),
        dataIndex: field.name,
        key: field.name,
        width: width,
        ellipsis: true,
        align: 'center',
        onHeaderCell: () => ({
          width: width,
          onResize: handleResize(field.name),
          style: { overflow: 'visible' }, // 确保 Tooltip 不会被截断
        }),
        render: (value: any) => (value !== null && value !== undefined ? String(value) : '-'),
      });
    });

    // 操作列（仅管理员可见）
    if (isAdmin) {
      cols.push({
        title: '操作',
        key: 'action',
        width: 150,
        fixed: 'right',
        render: (_, record) => (
          <Space size="small">
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
              编辑
            </Button>
            <Popconfirm
              title="确认删除这条数据吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确认"
              cancelText="取消"
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      });
    }

    return cols;
  }, [visibleFields, isAdmin, handleEdit, handleDelete, handleResize, getColumnWidth]);

  /**
   * 行选择配置
   */
  const rowSelection = useMemo(() => isAdmin
    ? {
        selectedRowKeys,
        onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
      }
    : undefined, [isAdmin, selectedRowKeys]);

  return (
    <div className="data-management">
      <Card className="data-card">
        {/* 筛选栏 */}
        <div className="filter-bar">
          <div className="filter-left">
            <Text strong style={{ marginRight: 16 }}>
              特征筛选:
            </Text>
            <Checkbox.Group value={selectedCategories} onChange={handleCategoryChange}>
              {Object.entries(CATEGORY_NAMES).map(([key, label]) => (
                <Checkbox key={key} value={key}>
                  <span style={{ color: CATEGORY_COLORS[key as keyof typeof CATEGORY_COLORS] }}>
                    {label}
                  </span>
                </Checkbox>
              ))}
            </Checkbox.Group>
          </div>

          <Space>
            {/* 搜索框 */}
            <Search
              placeholder="搜索关键词"
              allowClear
              onSearch={handleSearch}
              style={{ width: 250 }}
              enterButton={<SearchOutlined />}
            />

            {/* 刷新按钮 */}
            <Button icon={<ReloadOutlined />} onClick={loadData}>
              刷新
            </Button>

            {/* 管理员操作按钮 */}
            {isAdmin && (
              <>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                  新增数据
                </Button>
                {selectedRowKeys.length > 0 && (
                  <Popconfirm
                    title={`确认删除选中的 ${selectedRowKeys.length} 条数据吗？`}
                    onConfirm={handleBatchDelete}
                    okText="确认"
                    cancelText="取消"
                  >
                    <Button danger icon={<DeleteOutlined />}>
                      批量删除 ({selectedRowKeys.length})
                    </Button>
                  </Popconfirm>
                )}
              </>
            )}
          </Space>
        </div>

        {/* 覆盖率显示 */}
        {coverage && (
          <div className="coverage-info">
            <Space>
              <Text type="secondary">📊 数据集完整度:</Text>
              <Progress
                percent={Number(coverage.comprehensive_coverage.toFixed(1))}
                size="small"
                style={{ width: 120 }}
                status={coverage.meets_threshold ? 'success' : 'exception'}
              />
              <Tag color={coverage.meets_threshold ? 'success' : 'warning'}>
                {coverage.comprehensive_coverage.toFixed(1)}%
              </Tag>
            </Space>
          </div>
        )}

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={dataList}
          rowKey="id"
          rowSelection={rowSelection}
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 条数据`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 'max-content', y: 600 }}
          tableLayout="fixed"
          className="data-table"
          components={{
            header: {
              cell: ResizableTitle,
            },
          }}
        />
      </Card>

      {/* 编辑弹窗 */}
      {isAdmin && datasetId && schema && (
        <DataEditModal
          visible={editModalVisible}
          datasetId={datasetId}
          schema={schema}
          data={editingData}
          onClose={() => setEditModalVisible(false)}
          onSuccess={() => {
            setEditModalVisible(false);
            loadData();
            loadCoverage();
          }}
        />
      )}
    </div>
  );
};

export default DataManagement;

/**
 * 覆盖率概览页面
 * 展示所有数据集的覆盖率统计
 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Typography, Tag, Space, message, Button, Collapse, Descriptions, Checkbox, Popover } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  ArrowRightOutlined,
  PieChartOutlined,
  FieldNumberOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getAllCoverage } from '@/services/coverage';
import { getDatasetSchema } from '@/services/dataset';
import type { AllCoverageResponse, DatasetSchemaResponse } from '@/types';
import './CoverageOverview.css';

const { Title, Text } = Typography;
const { Panel } = Collapse;

const CoverageOverview: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AllCoverageResponse | null>(null);
  const [expandedDataset, setExpandedDataset] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<Record<string, DatasetSchemaResponse>>({});
  const [visibleColumns, setVisibleColumns] = useState<Record<string, string[]>>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await getAllCoverage();
      console.log('Coverage data:', response);
      setData(response);
    } catch (error) {
      console.error('加载覆盖率概览失败:', error);
      message.error('加载覆盖率概览失败');
    } finally {
      setLoading(false);
    }
  };

  const loadSchema = async (datasetId: string) => {
    if (schemas[datasetId]) return;
    try {
      const schema = await getDatasetSchema(datasetId);
      setSchemas(prev => ({ ...prev, [datasetId]: schema }));
      
      // 默认显示前5个字段
      if (!visibleColumns[datasetId]) {
        const defaultCols = schema.fields.slice(0, 5).map(f => f.name);
        setVisibleColumns(prev => ({ ...prev, [datasetId]: defaultCols }));
      }
    } catch (error) {
      console.error(`加载数据集 ${datasetId} 结构失败:`, error);
    }
  };

  useEffect(() => {
    if (expandedDataset) {
      loadSchema(expandedDataset);
    }
  }, [expandedDataset]);

  /**
   * 渲染字段覆盖率表格
   */
  const renderFieldCoverageTable = (fieldCoverage: Record<string, number>) => {
    const dataSource = Object.entries(fieldCoverage)
      .map(([field, coverage]) => ({
        field,
        coverage,
      }))
      .sort((a, b) => b.coverage - a.coverage); // 从高到低排序

    const columns = [
      {
        title: '字段名称',
        dataIndex: 'field',
        key: 'field',
        render: (text: string) => <Text strong>{text}</Text>,
      },
      {
        title: '覆盖率',
        dataIndex: 'coverage',
        key: 'coverage',
        sorter: (a: any, b: any) => a.coverage - b.coverage,
        render: (coverage: number) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Progress 
              percent={Number(coverage.toFixed(1))} 
              size="small" 
              status={coverage >= 90 ? 'success' : coverage >= 70 ? 'normal' : 'exception'}
              showInfo={false}
              style={{ width: '120px', marginBottom: 0 }}
            />
            <Text strong style={{ minWidth: '50px' }}>{coverage.toFixed(1)}%</Text>
          </div>
        ),
      },
    ];

    return (
      <Table
        dataSource={dataSource}
        columns={columns}
        rowKey="field"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: false,
          size: 'small',
        }}
        style={{ height: '480px' }}
      />
    );
  };

  /**
   * 渲染覆盖率分布表格（为了与字段覆盖率表格高度一致）
   */
  const renderDistributionTable = (distribution: Record<string, number>) => {
    const total = Object.values(distribution).reduce((sum, val) => sum + val, 0);
    const dataSource = Object.entries(distribution).map(([range, count]) => ({
      range,
      count,
      percentage: total > 0 ? (count / total * 100) : 0,
    }));

    const columns = [
      {
        title: '覆盖率区间',
        dataIndex: 'range',
        key: 'range',
        render: (text: string) => <Text strong>{text}</Text>,
      },
      {
        title: '分布情况',
        key: 'distribution',
        render: (_: any, record: any) => {
          const color = record.range === '90-100%' ? '#52c41a' : record.range === '80-90%' ? '#1890ff' : record.range === '70-80%' ? '#faad14' : '#f5222d';
          return (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Progress 
                percent={Number(record.percentage.toFixed(1))} 
                strokeColor={color}
                size="small"
                showInfo={false}
                style={{ width: '120px', marginBottom: 0 }}
              />
              <Text strong style={{ minWidth: '100px' }}>{record.count} 条 ({record.percentage.toFixed(1)}%)</Text>
            </div>
          );
        },
      },
    ];

    return (
      <Table
        dataSource={dataSource}
        columns={columns}
        rowKey="range"
        size="small"
        pagination={false}
        style={{ height: '480px' }}
      />
    );
  };

  if (!data) return null;

  const columns = [
    {
      title: '数据集',
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text: string, record: any) => (
        <Space>
          <DatabaseOutlined />
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>({record.dataset_id})</Text>
        </Space>
      ),
    },
    {
      title: '总记录数',
      dataIndex: 'total_records',
      key: 'total_records',
      sorter: (a: any, b: any) => a.total_records - b.total_records,
    },
    {
      title: '总字段数',
      dataIndex: 'total_fields',
      key: 'total_fields',
    },
    {
      title: '综合覆盖率',
      dataIndex: 'comprehensive_coverage',
      key: 'comprehensive_coverage',
      sorter: (a: any, b: any) => a.comprehensive_coverage - b.comprehensive_coverage,
      render: (val: number) => (
        <Space>
          <Progress 
            percent={Number(val.toFixed(1))} 
            size="small" 
            style={{ width: 100 }} 
            status={val >= 90 ? 'success' : 'normal'}
            showInfo={false}
          />
          <Text>{val.toFixed(1)}%</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'meets_threshold',
      key: 'meets_threshold',
      render: (meets: boolean) => (
        <Tag color={meets ? 'success' : 'warning'} icon={meets ? <CheckCircleOutlined /> : <WarningOutlined />}>
          {meets ? '已达标' : '未达标'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button 
            type="link" 
            icon={<ArrowRightOutlined />} 
            onClick={() => navigate(`/dataset/${record.dataset_id}`)}
          >
            查看数据
          </Button>
          <Button 
            type="link" 
            icon={<PieChartOutlined />} 
            onClick={() => setExpandedDataset(expandedDataset === record.dataset_id ? null : record.dataset_id)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="coverage-overview">
      <Title level={3}>📊 数据质量概览</Title>
      
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="总体综合覆盖率"
              value={data.overall_coverage}
              precision={1}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: data.meets_threshold ? '#52c41a' : '#faad14' }}
            />
            <div style={{ marginTop: 16 }}>
              <Progress 
                percent={Number(data.overall_coverage.toFixed(1))} 
                status={data.meets_threshold ? 'success' : 'active'}
                strokeColor={data.meets_threshold ? '#52c41a' : '#faad14'}
                showInfo={false}
              />
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card className="stat-card">
            <Statistic
              title="数据集总数"
              value={data.total_datasets}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="质量提示" className="info-card">
            {data.meets_threshold ? (
              <div className="status-msg success">
                <CheckCircleOutlined className="status-icon" />
                <div>
                  <Title level={4}>数据质量良好</Title>
                  <Text>所有数据集的平均覆盖率已达到 90% 的预设阈值。数据完整性符合科研分析要求。</Text>
                </div>
              </div>
            ) : (
              <div className="status-msg warning">
                <WarningOutlined className="status-icon" />
                <div>
                  <Title level={4}>数据质量待提升</Title>
                  <Text>当前总体覆盖率为 {data.overall_coverage.toFixed(1)}%，未达到 90% 的目标。请检查下方未达标的数据集并补充缺失字段。</Text>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="各数据集覆盖率详情" style={{ marginTop: 24 }}>
        <Table
          loading={loading}
          dataSource={data.datasets}
          rowKey="dataset_id"
          columns={columns}
          pagination={false}
          expandable={{
            expandedRowKeys: expandedDataset ? [expandedDataset] : [],
            onExpand: (expanded, record) => {
              setExpandedDataset(expanded ? record.dataset_id : null);
            },
            expandedRowRender: (record: any) => {
              const datasetId = record.dataset_id;
              const schema = schemas[datasetId];
              const selectedCols = visibleColumns[datasetId] || [];
              
              // 构建低覆盖率记录表格的列
              const lowCoverageColumns = [
                { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
                { title: '编号', dataIndex: 'identifier', key: 'identifier' },
                // 动态列
                ...selectedCols.map(colName => ({
                  title: schema?.fields.find(f => f.name === colName)?.display_name || colName,
                  dataIndex: ['full_data', colName],
                  key: colName,
                  render: (val: any) => val !== null && val !== undefined ? String(val) : <Text type="secondary">-</Text>
                })),
                { 
                  title: '覆盖率', 
                  dataIndex: 'coverage', 
                  key: 'coverage',
                  sorter: (a: any, b: any) => a.coverage - b.coverage,
                  render: (val: number) => (
                    <Space>
                      <Progress 
                        percent={Number(val.toFixed(1))} 
                        size="small" 
                        style={{ width: 120 }}
                        status={val < 50 ? 'exception' : val < 70 ? 'normal' : 'success'}
                        showInfo={false}
                      />
                      <Text strong>{val.toFixed(1)}%</Text>
                    </Space>
                  ),
                },
              ];

              const columnSelector = (
                <Popover
                  title="选择展示列"
                  trigger="click"
                  content={
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      <Checkbox.Group
                        options={schema?.fields.map(f => ({ label: f.display_name || f.name, value: f.name }))}
                        value={selectedCols}
                        onChange={(checkedValues) => {
                          setVisibleColumns(prev => ({ ...prev, [datasetId]: checkedValues as string[] }));
                        }}
                        style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
                      />
                    </div>
                  }
                >
                  <Button icon={<SettingOutlined />} size="small">设置展示列</Button>
                </Popover>
              );

              return (
                <Row gutter={[16, 16]} style={{ padding: '16px' }}>
                  <Col span={12}>
                    <Card title="📊 覆盖率分布" size="small">
                      {renderDistributionTable(record.coverage_distribution)}
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="📋 字段覆盖率详情" size="small">
                      {renderFieldCoverageTable(record.field_coverage)}
                    </Card>
                  </Col>
                  <Col span={24}>
                    <Card 
                      title="⚠️ 低覆盖率记录" 
                      size="small"
                      extra={columnSelector}
                    >
                      <Table
                        dataSource={record.low_coverage_records.sort((a: any, b: any) => b.coverage - a.coverage)}
                        rowKey="id"
                        size="small"
                        pagination={{
                          pageSize: 10,
                          showSizeChanger: true,
                          pageSizeOptions: ['10', '20', '50'],
                        }}
                        columns={lowCoverageColumns}
                      />
                    </Card>
                  </Col>
                </Row>
              );
            },
          }}
        />
      </Card>
    </div>
  );
};

export default CoverageOverview;

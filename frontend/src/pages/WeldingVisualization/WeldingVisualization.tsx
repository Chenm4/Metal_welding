/**
 * 激光焊接高速摄像过程可视化
 * 展示高速摄像、光谱信号、光强信号和合成视频
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Card, Slider, Button, Typography, Space, Image, Alert, Spin, Row, Col } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import './WeldingVisualization.css';

const { Title, Text } = Typography;

// 数据接口定义
interface WeldingExperiment {
  id: string;
  mat: string;
  power: string;
  speed: string;
  start_idx: number;
  total: number;
  digits: number;
  hs_ext: string;
  spec_path: string;
  pd_path: string;
  has_video: boolean;
  videos: Array<{
    fps: number;
    path: string;
    filename: string;
  }>;
}

// 数据基础路径
const BASE_PATH = '/data/3mm复合材料和铝合金焊接数据/3mm复合材料和铝合金焊接数据';

/**
 * 焊接可视化主组件
 */
const WeldingVisualization: React.FC = () => {
  const [experiments, setExperiments] = useState<WeldingExperiment[]>([]);
  const [currentExp, setCurrentExp] = useState<WeldingExperiment | null>(null);
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [imageError, setImageError] = useState<boolean>(false);
  const [selectedFps, setSelectedFps] = useState<number>(30);
  const [videoError, setVideoError] = useState<boolean>(false);
  
  // 使用ref直接操作DOM，避免React重渲染导致卡顿
  const imageRef = useRef<HTMLImageElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameDisplayRef = useRef<HTMLDivElement>(null);

  /**
   * 加载实验数据
   */
  useEffect(() => {
    loadExperiments();
  }, []);

  /**
   * 当选中实验变化时，初始化图片和视频
   */
  useEffect(() => {
    if (currentExp && imageRef.current) {
      const realIdx = currentExp.start_idx;
      const idxStr = realIdx.toString().padStart(currentExp.digits, '0');
      const filename = `File_${idxStr}${currentExp.hs_ext}`;
      const imgPath = `${BASE_PATH}/高速摄像/${currentExp.id}/${filename}`;
      console.log('初始化图片:', imgPath);
      imageRef.current.src = imgPath;
    }
    
    if (currentExp && currentExp.has_video && videoRef.current) {
      const videoPath = `${BASE_PATH}/高速摄像合成video/${currentExp.id}/${currentExp.id}_fps30.mp4`;
      const encodedPath = encodeURI(videoPath);
      console.log('初始化视频:', encodedPath);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:74',message:'视频路径构建',data:{videoPath,encodedPath,expId:currentExp.id,hasVideo:currentExp.has_video},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      
      // 先检查文件是否存在
      fetch(encodedPath, { method: 'HEAD' })
        .then(response => {
          // #region agent log
          fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:79',message:'HEAD请求响应',data:{status:response.status,statusText:response.statusText,contentType:response.headers.get('content-type'),url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
          // #endregion
          if (!response.ok) {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:82',message:'文件不存在或无法访问',data:{status:response.status,statusText:response.statusText,url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
            // #endregion
          }
          return response.text();
        })
        .then(text => {
          // #region agent log
          fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:88',message:'响应内容检查',data:{isHTML:text.startsWith('<!'),textPreview:text.substring(0,200),url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
          // #endregion
        })
        .catch(err => {
          // #region agent log
          fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:92',message:'HEAD请求失败',data:{error:err.message,url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
          // #endregion
        });
      
      videoRef.current.src = encodedPath;
      videoRef.current.load();
    }
  }, [currentExp]);

  /**
   * 从welding_data.js加载数据
   */
  const loadExperiments = async () => {
    try {
      setLoading(true);
      // 动态加载welding_data.js
      const response = await fetch('/welding_data.js');
      const text = await response.text();
      
      // 解析JS变量
      const match = text.match(/const WELDING_DB = (\[[\s\S]*?\]);/);
      if (match) {
        const data = JSON.parse(match[1]);
        setExperiments(data);
        if (data.length > 0) {
          setCurrentExp(data[0]);
        }
      }
    } catch (error) {
      console.error('加载实验数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 切换实验
   */
  const handleExpChange = useCallback((exp: WeldingExperiment) => {
    setCurrentExp(exp);
    setCurrentFrame(0);
    setImageError(false);
    setVideoError(false);
    setSelectedFps(30);
    
    // 立即更新图片
    if (imageRef.current) {
      const realIdx = exp.start_idx;
      const idxStr = realIdx.toString().padStart(exp.digits, '0');
      const filename = `File_${idxStr}${exp.hs_ext}`;
      imageRef.current.src = `${BASE_PATH}/高速摄像/${exp.id}/${filename}`;
    }
    
    // 立即更新视频（使用BASE_PATH保持路径一致性）
    if (videoRef.current && exp.has_video) {
      const videoPath = `${BASE_PATH}/高速摄像合成video/${exp.id}/${exp.id}_fps30.mp4`;
      const encodedPath = encodeURI(videoPath);
      console.log('初始视频路径:', encodedPath);
      videoRef.current.src = encodedPath;
      videoRef.current.load();
    }
  }, []);

  /**
   * 处理滑块变化（原生HTML版：纯DOM操作，无状态更新）
   */
  const handleFrameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!currentExp || !imageRef.current) return;
    
    const value = parseInt(e.target.value);
    
    // 直接修改img.src，完全不触发React状态更新
    const realIdx = currentExp.start_idx + value;
    const idxStr = realIdx.toString().padStart(currentExp.digits, '0');
    const filename = `File_${idxStr}${currentExp.hs_ext}`;
    const newSrc = `${BASE_PATH}/高速摄像/${currentExp.id}/${filename}`;
    
    imageRef.current.src = newSrc;
    
    // 更新帧数显示
    if (frameDisplayRef.current) {
      frameDisplayRef.current.textContent = `Frame ${value} / ${currentExp.total - 1}`;
    }
  }, [currentExp]);
  
  /**
   * 更新视频源
   */
  const updateVideoSource = useCallback((fps: number) => {
    if (!currentExp || !videoRef.current) return;
    
    setSelectedFps(fps);
    setVideoError(false);
    // 使用BASE_PATH保持路径一致性
    const videoPath = `${BASE_PATH}/高速摄像合成video/${currentExp.id}/${currentExp.id}_fps${fps}.mp4`;
    const encodedPath = encodeURI(videoPath);
    
    console.log('加载视频:', encodedPath);
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:167',message:'更新视频源',data:{fps,videoPath,encodedPath,expId:currentExp.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    // 检查文件是否存在
    fetch(encodedPath, { method: 'HEAD' })
      .then(response => {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:172',message:'updateVideoSource HEAD响应',data:{status:response.status,statusText:response.statusText,contentType:response.headers.get('content-type'),url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
      })
      .catch(err => {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:177',message:'updateVideoSource HEAD失败',data:{error:err.message,url:encodedPath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
      });
    
    videoRef.current.src = encodedPath;
    videoRef.current.load();
  }, [currentExp]);

  /**
   * 获取当前帧的图片路径（使用useMemo优化）
   */
  const currentFramePath = useMemo(() => {
    if (!currentExp) return '';
    
    const realIdx = currentExp.start_idx + currentFrame;
    const idxStr = realIdx.toString().padStart(currentExp.digits, '0');
    const filename = `File_${idxStr}${currentExp.hs_ext}`;
    
    return `${BASE_PATH}/高速摄像/${currentExp.id}/${filename}`;
  }, [currentExp, currentFrame]);

  /**
   * 判断是否有信号数据
   */
  const hasSpecData = useMemo(() => currentExp?.spec_path && currentExp.spec_path.length > 0, [currentExp]);
  const hasPdData = useMemo(() => currentExp?.pd_path && currentExp.pd_path.length > 0, [currentExp]);
  const hasAnySignalData = hasSpecData || hasPdData;

  /**
   * 计算当前时间（毫秒）
   */
  const getCurrentTime = (): string => {
    return (currentFrame * 0.25).toFixed(2);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="加载实验数据中..." />
      </div>
    );
  }

  return (
    <div className="welding-visualization">
      <Row gutter={16} style={{ height: '100%' }}>
        {/* 左侧实验列表 */}
        <Col span={6} className="experiment-list-container">
          <Card 
            title={
              <Space>
                <PlayCircleOutlined />
                <span>实验列表</span>
              </Space>
            }
            className="experiment-list-card"
            bodyStyle={{ padding: 0, maxHeight: 'calc(100vh - 180px)', overflowY: 'auto' }}
          >
            {experiments.map((exp) => (
              <div
                key={exp.id}
                className={`experiment-item ${currentExp?.id === exp.id ? 'active' : ''}`}
                onClick={() => handleExpChange(exp)}
              >
                <div className="exp-name">{exp.id}</div>
                <div className="exp-meta">
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {exp.mat} | {exp.power} | {exp.speed}mm/s
                  </Text>
                </div>
                <div className="exp-stats">
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {exp.total} 帧 | 视频: {exp.has_video ? '有' : '无'}
                  </Text>
                </div>
              </div>
            ))}
          </Card>
        </Col>

        {/* 右侧内容区 */}
        <Col span={18} className="content-area">
          {currentExp ? (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {/* 实验标题 */}
              <Card size="small" className="exp-header-card">
                <Title level={4} style={{ margin: 0 }}>
                  {currentExp.id}
                </Title>
                <Text type="secondary">
                  材料: {currentExp.mat} | 功率: {currentExp.power} | 速度: {currentExp.speed}mm/s
                </Text>
              </Card>

              {/* 高速摄像区域 */}
              <Card 
                title={
                  <Space>
                    <span>📷 高速摄像</span>
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      Frame: {currentFrame} / {currentExp.total - 1} | 时间: {getCurrentTime()}ms
                    </Text>
                  </Space>
                }
                className="high-speed-camera-card"
              >
                <div className="image-container">
                  {imageError ? (
                    <Alert
                      message="图片加载失败"
                      description={`无法加载当前帧图片`}
                      type="error"
                      showIcon
                    />
                  ) : (
                    <img
                      ref={imageRef}
                      alt={`Frame ${currentFrame}`}
                      className="hs-image"
                      onError={() => setImageError(true)}
                      style={{ maxHeight: 450, maxWidth: '100%', objectFit: 'contain' }}
                    />
                  )}
                </div>
                <div style={{ marginTop: 16, padding: '0 8px' }}>
                  <input
                    ref={(el) => {
                      if (el && currentExp) {
                        el.min = '0';
                        el.max = String(currentExp.total - 1);
                        el.value = String(currentFrame);
                      }
                    }}
                    type="range"
                    className="frame-slider"
                    onChange={handleFrameChange}
                    style={{ width: '100%' }}
                  />
                  <div ref={frameDisplayRef} style={{ textAlign: 'center', marginTop: 8, color: '#666' }}>
                    Frame {currentFrame} / {currentExp.total - 1}
                  </div>
                </div>
              </Card>

              {/* 信号图区域 - 条件渲染 */}
              {hasAnySignalData && (
                <Row gutter={16}>
                  {hasSpecData && (
                    <Col span={hasSpecData && hasPdData ? 12 : 24}>
                      <Card 
                        title="📊 光谱信号" 
                        className="signal-card"
                        bodyStyle={{ textAlign: 'center', padding: 16 }}
                      >
                        <Image
                          src={`${BASE_PATH}/${currentExp.spec_path}`}
                          alt="光谱信号"
                          preview
                          style={{ maxWidth: '100%', maxHeight: 280 }}
                        />
                      </Card>
                    </Col>
                  )}
                  {hasPdData && (
                    <Col span={hasSpecData && hasPdData ? 12 : 24}>
                      <Card 
                        title="📈 光强信号" 
                        className="signal-card"
                        bodyStyle={{ textAlign: 'center', padding: 16 }}
                      >
                        <Image
                          src={`${BASE_PATH}/${currentExp.pd_path}`}
                          alt="光强信号"
                          preview
                          style={{ maxWidth: '100%', maxHeight: 280 }}
                        />
                      </Card>
                    </Col>
                  )}
                </Row>
              )}

              {/* 视频播放区域 */}
              <Card 
                title="🎬 合成视频" 
                className="video-card"
                extra={
                  <Space>
                    <Text type="secondary">选择帧率:</Text>
                    {[30, 60, 90, 120, 160, 240].map((fps) => (
                      <Button
                        key={fps}
                        type={selectedFps === fps ? 'primary' : 'default'}
                        size="small"
                        onClick={() => updateVideoSource(fps)}
                      >
                        {fps} fps
                      </Button>
                    ))}
                  </Space>
                }
              >
                {currentExp.has_video ? (
                  <div style={{ textAlign: 'center' }}>
                    {videoError ? (
                      <Alert
                        message="视频加载失败"
                        description={
                          <div>
                            <p>无法加载视频文件。错误原因：视频编码格式不被浏览器支持。</p>
                            <p style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                              解决方案：需要将视频重新编码为H.264格式。请运行后端脚本重新生成视频文件。
                            </p>
                          </div>
                        }
                        type="error"
                        showIcon
                      />
                    ) : (
                      <video
                        ref={videoRef}
                        controls
                        preload="metadata"
                        playsInline
                        style={{ width: '100%', maxHeight: 600, background: '#000' }}
                        onError={(e) => {
                          const target = e.target as HTMLVideoElement;
                          const error = target.error;
                          const errorDetails = {
                            errorCode: error?.code,
                            errorMessage: error?.message,
                            networkState: target.networkState,
                            readyState: target.readyState,
                            src: target.src,
                            currentSrc: target.currentSrc
                          };
                          console.error('视频加载错误:', errorDetails);
                          // #region agent log
                          fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:385',message:'视频加载错误详情',data:errorDetails,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
                          // #endregion
                          setVideoError(true);
                        }}
                        onLoadedMetadata={() => {
                          const target = videoRef.current;
                          if (target) {
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:395',message:'视频元数据加载成功',data:{duration:target.duration,videoWidth:target.videoWidth,videoHeight:target.videoHeight,currentSrc:target.currentSrc},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
                            // #endregion
                          }
                          console.log('视频元数据加载成功');
                        }}
                        onLoadStart={() => {
                          const target = videoRef.current;
                          if (target) {
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:401',message:'视频开始加载',data:{src:target.src,networkState:target.networkState,readyState:target.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
                            // #endregion
                          }
                        }}
                        onProgress={() => {
                          const target = videoRef.current;
                          if (target && target.buffered.length > 0) {
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/62ea5bfd-61a9-47b8-b02e-bae10fabc3e3',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'WeldingVisualization.tsx:407',message:'视频加载进度',data:{bufferedEnd:target.buffered.end(0),duration:target.duration,networkState:target.networkState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
                            // #endregion
                          }
                        }}
                      >
                        <source type="video/mp4" />
                        您的浏览器不支持视频播放
                      </video>
                    )}
                  </div>
                ) : (
                  <Alert message="该实验暂无视频数据" type="info" showIcon />
                )}
              </Card>
            </Space>
          ) : (
            <Card>
              <Alert
                message="请选择实验"
                description="从左侧列表中选择一个实验以查看详细数据"
                type="info"
                showIcon
              />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default WeldingVisualization;

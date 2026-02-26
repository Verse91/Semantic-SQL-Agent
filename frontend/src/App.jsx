import { useState } from 'react';
import { Input, Button, Card, Space, Alert, Spin, Table, Upload, message, Select } from 'antd';
import { PlayCircleOutlined, SendOutlined, UploadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Option } = Select;

const API_BASE = 'http://localhost:8000';

function App() {
  const [mode, setMode] = useState('natural_language'); // natural_language | report_dsl
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [execTime, setExecTime] = useState(null);
  
  // Report DSL 模式
  const [reportSpec, setReportSpec] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleGenerate = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    setSql('');
    
    try {
      const response = await axios.post(`${API_BASE}/api/generate_sql`, {
        question: question
      });
      
      if (response.data.success) {
        setSql(response.data.data.sql);
      } else {
        setError(response.data.error || '生成SQL失败');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!sql.trim()) return;
    
    setExecuting(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await axios.post(`${API_BASE}/api/execute_sql`, {
        sql: sql
      });
      
      if (response.data.success) {
        setResult(response.data.data);
        setExecTime(response.data.data.execution_time_ms);
      } else {
        setError(response.data.error || '执行SQL失败');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || '请求失败');
    } finally {
      setExecuting(false);
    }
  };

  const handleUploadReport = async (file) => {
    setUploading(true);
    setError(null);
    setReportSpec(null);
    setSql('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`${API_BASE}/api/upload_report_spec`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.success) {
        setReportSpec(response.data.data);
        message.success('报表定义解析成功');
      } else {
        setError(response.data.error || '解析失败');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || '上传失败');
    } finally {
      setUploading(false);
    }
    return false; // 不让 Upload 组件自动发送
  };

  const handleGenerateFromSpec = async () => {
    if (!reportSpec) return;
    
    setLoading(true);
    setError(null);
    setSql('');
    
    try {
      const response = await axios.post(`${API_BASE}/api/generate_sql_from_spec`, {
        report_spec: reportSpec.parsed_structure
      });
      
      if (response.data.success) {
        setSql(response.data.data.sql);
        message.success('SQL 生成成功');
      } else {
        setError(response.data.error || '生成SQL失败');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = result?.columns?.map(col => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
  })) || [];

  const dataSource = result?.rows?.map((row, idx) => {
    const obj = {};
    result.columns.forEach((col, i) => {
      obj[col] = row[i];
    });
    obj.key = idx;
    return obj;
  }) || [];

  return (
    <div style={{ 
      padding: '24px', 
      maxWidth: '1200px', 
      margin: '0 auto',
      background: '#f5f5f5',
      minHeight: '100vh'
    }}>
      <h1 style={{ textAlign: 'center', marginBottom: '24px' }}>
        🔍 Semantic SQL Agent
      </h1>

      {/* 模式选择 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space>
          <span>选择模式:</span>
          <Select value={mode} onChange={setMode} style={{ width: 200 }}>
            <Option value="natural_language">自然语言查询</Option>
            <Option value="report_dsl">报表定义 (Report DSL)</Option>
          </Select>
        </Space>
      </Card>
      
      {/* 自然语言模式 */}
      {mode === 'natural_language' && (
        <>
          <Card title="Step 1: 输入自然语言查询" style={{ marginBottom: '16px' }}>
            <TextArea
              rows={3}
              placeholder="例如：查询前10个物料的中文名称"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              style={{ marginBottom: '12px' }}
            />
            <Button 
              type="primary" 
              icon={<SendOutlined />}
              onClick={handleGenerate}
              loading={loading}
              disabled={!question.trim()}
            >
              生成 SQL
            </Button>
          </Card>
        </>
      )}
      
      {/* Report DSL 模式 */}
      {mode === 'report_dsl' && (
        <>
          <Card title="Step 1: 上传 Markdown 报表定义" style={{ marginBottom: '16px' }}>
            <Upload.Dragger
              accept=".md,.txt"
              beforeUpload={handleUploadReport}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽 Markdown 文件到此区域</p>
              <p className="ant-upload-hint">
                支持 .md 和 .txt 格式
              </p>
            </Upload.Dragger>
            {uploading && <Spin style={{ marginTop: 16 }} />}
          </Card>

          {reportSpec && (
            <Card title="Step 2: 解析后的结构" style={{ marginBottom: '16px' }}>
              <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto', maxHeight: 300 }}>
                {JSON.stringify(reportSpec.parsed_structure, null, 2)}
              </pre>
              <Button 
                type="primary" 
                onClick={handleGenerateFromSpec}
                loading={loading}
                style={{ marginTop: 12 }}
              >
                生成 SQL
              </Button>
            </Card>
          )}
        </>
      )}
      
      {/* SQL 展示和执行 */}
      <Card title="Step 3: SQL 预览和执行" style={{ marginBottom: '16px' }}>
        <TextArea
          rows={5}
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          placeholder="生成的SQL将显示在这里，您可以手动修改"
          style={{ marginBottom: '12px', fontFamily: 'monospace' }}
        />
        <Button 
          type="primary"
          danger={sql.trim() !== ''}
          icon={<PlayCircleOutlined />}
          onClick={handleExecute}
          loading={executing}
          disabled={!sql.trim()}
        >
          执行 SQL
        </Button>
      </Card>
      
      {/* 错误提示 */}
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}
      
      {/* 结果展示 */}
      {result && (
        <Card title={`查询结果 (${result.row_count} 行, ${execTime}ms)`}>
          <Table
            columns={columns}
            dataSource={dataSource}
            pagination={{ 
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`
            }}
            scroll={{ x: true }}
            size="small"
            bordered
          />
        </Card>
      )}
      
      {/* Loading */}
      {(loading || executing) && (
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Spin size="large" />
          <p>{loading ? '正在生成 SQL...' : '正在执行查询...'}</p>
        </div>
      )}
    </div>
  );
}

export default App;

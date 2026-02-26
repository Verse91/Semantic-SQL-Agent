import { useState } from 'react';
import { Input, Button, Card, Space, Alert, Spin, Table } from 'antd';
import { PlayCircleOutlined, SendOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;

const API_BASE = 'http://localhost:8000';

function App() {
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [execTime, setExecTime] = useState(null);

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
      
      {/* 第一步：自然语言输入 */}
      <Card 
        title="Step 1: 输入自然语言查询" 
        style={{ marginBottom: '16px' }}
      >
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
      
      {/* 第二步：SQL 展示和执行 */}
      <Card 
        title="Step 2: SQL 预览和执行" 
        style={{ marginBottom: '16px' }}
      >
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
      
      {/* 第三步：结果展示 */}
      {result && (
        <Card 
          title={`查询结果 (${result.row_count} 行, ${execTime}ms)`}
        >
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
      
      {/* Loading 状态 */}
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

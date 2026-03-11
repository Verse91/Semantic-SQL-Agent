import React, { useState, useEffect } from 'react';
import { Input, Button, Table, Tag, Space, Card, Typography, message, Spin, Alert } from 'antd';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// V2 API 端口
const API_BASE = 'http://localhost:8001';

function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [error, setError] = useState(null);

  // 发送消息
  const handleSend = async () => {
    if (!question.trim()) return;
    
    const userQuestion = question.trim();
    setQuestion('');
    setLoading(true);
    setError(null);
    setCurrentResult(null);

    // 添加用户消息到历史
    const newMessages = [...messages, { role: 'user', content: userQuestion }];
    setMessages(newMessages);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        session_id: sessionId,
        query: userQuestion
      });

      const data = response.data;

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      if (data.error) {
        setError(data.error);
      } else {
        // 添加 AI 响应到历史
        setMessages([...newMessages, { 
          role: 'assistant', 
          content: data.sql || '执行完成',
          result: data.result 
        }]);
        setCurrentResult(data);
      }
    } catch (err) {
      setError(err.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 清空对话
  const handleClear = () => {
    setSessionId(null);
    setMessages([]);
    setCurrentResult(null);
    setError(null);
  };

  // 渲染消息
  const renderMessages = () => {
    return messages.map((msg, idx) => (
      <div key={idx} style={{
        marginBottom: 16,
        padding: 12,
        background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed',
        borderRadius: 8,
        textAlign: msg.role === 'user' ? 'right' : 'left'
      }}>
        <Text strong>{msg.role === 'user' ? '你' : 'AI'}：</Text>
        <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
      </div>
    ));
  };

  // 渲染表格
  const renderTable = () => {
    if (!currentResult?.result?.data || currentResult.result.data.length === 0) {
      return null;
    }

    const data = currentResult.result.data;
    const columns = currentResult.result.columns || Object.keys(data[0] || {});

    return (
      <div style={{ marginTop: 16 }}>
        <Text strong>执行结果 ({currentResult.result.row_count} 行)：</Text>
        <Table 
          dataSource={data}
          columns={columns.map(col => ({ title: col, dataIndex: col, key: col }))}
          size="small"
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
          style={{ marginTop: 8 }}
        />
      </div>
    );
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
        🔥 Semantic SQL Agent V2
      </Title>
      
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <TextArea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="输入你的问题，比如：查询销售订单、按客户分组统计金额..."
            autoSize={{ minRows: 2, maxRows: 6 }}
            onPressEnter={e => {
              if (e.ctrlKey || e.metaKey) {
                handleSend();
              }
            }}
            style={{ flex: 1 }}
          />
          <Space direction="vertical">
            <Button type="primary" onClick={handleSend} loading={loading}>
              发送
            </Button>
            <Button onClick={handleClear}>
              清空
            </Button>
          </Space>
        </div>
        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
          Ctrl + Enter 发送 | 支持多轮对话
        </Text>
      </Card>

      {error && (
        <Alert 
          message="错误" 
          description={error} 
          type="error" 
          showIcon 
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError(null)}
        />
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin size="large" />
          <div style={{ marginTop: 8 }}>AI 正在思考...</div>
        </div>
      )}

      {currentResult?.sql && (
        <Card 
          title="生成的 SQL" 
          size="small" 
          style={{ marginBottom: 16 }}
          extra={<Tag color="blue">PostgreSQL</Tag>}
        >
          <pre style={{ 
            background: '#f5f5f5', 
            padding: 12, 
            borderRadius: 4,
            overflow: 'auto',
            fontSize: 13
          }}>
            {currentResult.sql}
          </pre>
        </Card>
      )}

      {renderTable()}

      {messages.length > 0 && (
        <Card title="对话历史" size="small" style={{ marginTop: 16 }}>
          {renderMessages()}
        </Card>
      )}

      {!loading && !currentResult && messages.length === 0 && (
        <div style={{ textAlign: 'center', color: '#999', marginTop: 48 }}>
          <Title level={4}>欢迎使用 Semantic SQL Agent V2</Title>
          <Paragraph>
            直接用自然语言描述你的需求，AI 会自动生成 SQL 并执行。
          </Paragraph>
          <Paragraph>
            <Text code>查询销售订单</Text> <Text code>按客户统计金额</Text> <Text code>查看库存</Text>
          </Paragraph>
        </div>
      )}
    </div>
  );
}

export default App;

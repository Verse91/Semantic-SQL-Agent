import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Table, Tag, Card, Layout, Spin, Alert, Typography } from 'antd';
import { 
  SendOutlined, 
  DeleteOutlined, 
  PaperClipOutlined, 
  DatabaseOutlined, 
  ConsoleSqlOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const API_BASE = 'http://localhost:8001';

function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showSql, setShowSql] = useState(false);
  const [isChatting, setIsChatting] = useState(false); // 关键：对话状态
  const fileInputRef = useRef(null);

  const handleSend = async () => {
    if (!question.trim()) return;
    const userQuestion = question.trim();
    setQuestion('');
    setLoading(true);
    setError(null);
    setIsChatting(true);

    const newMessages = [...messages, { role: 'user', content: userQuestion }];
    setMessages(newMessages);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        session_id: sessionId,
        query: userQuestion
      });
      const data = response.data;
      if (data.session_id && !sessionId) setSessionId(data.session_id);

      if (data.error) {
        setError(data.error);
      } else {
        setMessages([...newMessages, { role: 'assistant', content: data.sql ? 'Query executed successfully.' : 'Done' }]);
        setCurrentResult(data);
      }
    } catch (err) {
      setError(err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setIsChatting(true);
    
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);

    try {
      const response = await axios.post(`${API_BASE}/api/upload_fs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const data = response.data;
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      
      setMessages([...messages, { role: 'user', content: `[Upload: ${file.name}]` }]);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Report parsed successfully.' }]);
      setCurrentResult(data);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    setSessionId(null);
    setMessages([]);
    setCurrentResult(null);
    setError(null);
    setIsChatting(false);
  };

  // 初始状态：居中布局
  const renderWelcome = () => (
    <div style={{ 
      flex: 1, 
      display: 'flex', 
      flexDirection: 'column', 
      justifyContent: 'center', 
      alignItems: 'center',
      transition: 'all 0.3s ease'
    }}>
      <Title level={1} style={{ 
        marginBottom: 16, 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        WebkitBackgroundClip: 'text', 
        WebkitTextFillColor: 'transparent' 
      }}>
        🔥 Semantic SQL Agent
      </Title>
      <Paragraph type="secondary" style={{ fontSize: 16, marginBottom: 32 }}>
        AI-Powered Data Analytics • Natural Language to SQL
      </Paragraph>
      
      {/* 居中的输入框 */}
      <div style={{ 
        width: '100%', 
        maxWidth: 600, 
        border: '1px solid #ddd', 
        borderRadius: 28, 
        padding: '12px 16px', 
        display: 'flex', 
        alignItems: 'center', 
        background: '#fff',
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
      }}>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".txt,.md,.pdf,.docx"
          onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])}
        />
        <Button 
          type="text" 
          icon={<PaperClipOutlined />} 
          onClick={() => fileInputRef.current?.click()}
          loading={uploading}
        />
        <Input
          bordered={false}
          placeholder="Ask a question about your data..."
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onPressEnter={handleSend}
          style={{ flex: 1, fontSize: 15 }}
        />
        <Button 
          type="primary" 
          shape="circle" 
          icon={<SendOutlined />} 
          onClick={handleSend}
          disabled={!question.trim()}
        />
      </div>
      
      <Paragraph type="secondary" style={{ marginTop: 16 }}>
        Try: "查询销售订单" or "按客户统计金额"
      </Paragraph>
    </div>
  );

  // 对话状态：输入框在底部
  const renderChatMode = () => (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24, paddingTop: 20 }}>
        <Title level={3} style={{ marginBottom: 4 }}>🔥 Semantic SQL Agent</Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>AI-Powered Data Analytics</Paragraph>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', marginBottom: 16 }}>
        {messages.map((msg, idx) => (
          <Card key={idx} size="small" style={{ marginBottom: 12, background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed' }}>
            <Text strong>{msg.role === 'user' ? '❓ Question: ' : '💡 Insight: '}</Text>
            <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          </Card>
        ))}
        
        {loading && <div style={{ textAlign: 'center', padding: 20 }}><Spin tip="AI is thinking..." /></div>}
      </div>

      {/* Result */}
      {currentResult && (
        <>
          {/* Show SQL */}
          <div style={{ marginBottom: 12 }}>
            <Button size="small" icon={<ConsoleSqlOutlined />} onClick={() => setShowSql(!showSql)}>
              {showSql ? "Hide SQL" : "Show SQL"}
            </Button>
            {showSql && currentResult.sql && (
              <Card size="small" style={{ marginTop: 8 }}>
                <pre style={{ background: '#1e1e1e', color: '#c5c5c5', padding: 12, borderRadius: 6, fontSize: 12, overflow: 'auto' }}>
                  {currentResult.sql}
                </pre>
              </Card>
            )}
          </div>

          {/* Table */}
          {currentResult.result?.data && (
            <Card title={<><DatabaseOutlined /> Query Result ({currentResult.result.row_count} rows)</>} style={{ marginBottom: 16 }}>
              <Table 
                dataSource={currentResult.result.data}
                columns={currentResult.result.columns?.map(col => ({ title: col, dataIndex: col, key: col }))}
                pagination={{ pageSize: 8 }}
                scroll={{ x: 'max-content' }}
                size="small"
              />
            </Card>
          )}
        </>
      )}

      {/* Error */}
      {error && (
        <Alert message="Error" description={error} type="error" showIcon closable onClose={() => setError(null)} style={{ marginBottom: 16 }} />
      )}

      {/* Input at bottom */}
      <div style={{ border: '1px solid #ddd', borderRadius: 28, padding: '8px 12px', display: 'flex', alignItems: 'center', background: '#fff' }}>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".txt,.md,.pdf,.docx"
          onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])}
        />
        <Button type="text" icon={<PaperClipOutlined />} onClick={() => fileInputRef.current?.click()} loading={uploading} />
        <Input
          bordered={false}
          placeholder="Ask a question..."
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onPressEnter={handleSend}
          style={{ flex: 1, fontSize: 15 }}
        />
        <Button type="primary" shape="circle" icon={<SendOutlined />} onClick={handleSend} disabled={!question.trim()} />
      </div>

      {/* Clear */}
      <div style={{ textAlign: 'center', marginTop: 8 }}>
        <Button size="small" icon={<DeleteOutlined />} onClick={handleClear}>Clear</Button>
      </div>
    </div>
  );

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      <Content style={{ maxWidth: 900, margin: '0 auto', padding: 24, display: 'flex', flexDirection: 'column' }}>
        {isChatting ? renderChatMode() : renderWelcome()}
      </Content>
    </Layout>
  );
}

export default App;

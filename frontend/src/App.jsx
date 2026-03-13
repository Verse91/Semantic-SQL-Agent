import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Table, Tag, Card, Layout, Space, Spin, Alert, Typography } from 'antd';
import { 
  SendOutlined, 
  DeleteOutlined, 
  PaperClipOutlined, 
  DatabaseOutlined, 
  ConsoleSqlOutlined,
  RobotOutlined,
  UserOutlined 
} from '@ant-design/icons';
import axios from 'axios';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const API_BASE = 'http://localhost:8001';

function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!question.trim()) return;
    const userQuestion = question.trim();
    setQuestion('');
    setLoading(true);
    setError(null);

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
        setMessages([...newMessages, { 
          role: 'assistant', 
          content: data.sql ? 'SQL 已生成并执行成功。' : '执行完成' 
        }]);
        setCurrentResult(data);
      }
    } catch (err) {
      setError(err.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);

    try {
      const response = await axios.post(`${API_BASE}/api/upload_fs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const data = response.data;
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      
      setMessages([...messages, 
        { role: 'user', content: `[上传文件: ${file.name}]` },
        { role: 'assistant', content: '报表解析完成，您可以开始提问了。' }
      ]);
      setCurrentResult(data);
    } catch (err) {
      setError(err.message || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const renderMessages = () => messages.map((msg, idx) => (
    <div key={idx} style={{ 
      display: 'flex', 
      justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
      marginBottom: 20 
    }}>
      <div style={{ display: 'flex', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', maxWidth: '90%' }}>
        <div style={{ 
          width: 32, height: 32, borderRadius: '50%', 
          background: msg.role === 'user' ? '#1677ff' : '#52c41a',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', flexShrink: 0,
          margin: msg.role === 'user' ? '0 0 0 8px' : '0 8px 0 0'
        }}>
          {msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
        </div>
        <div style={{
          padding: '10px 16px',
          borderRadius: msg.role === 'user' ? '18px 2px 18px 18px' : '2px 18px 18px 18px',
          background: msg.role === 'user' ? '#1677ff' : '#fff',
          color: msg.role === 'user' ? '#fff' : '#000',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          fontSize: '14px',
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap'
        }}>
          {msg.content}
        </div>
      </div>
    </div>
  ));

  return (
    <Layout style={{ height: '100vh', background: '#f0f2f5' }}>
      {/* 左侧对话区 */}
      <Sider width="40%" theme="light" style={{ display: 'flex', flexDirection: 'column', borderRight: '1px solid #e8e8e8' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>💬 Chat Agent</Title>
          <Button type="text" icon={<DeleteOutlined />} onClick={() => {setMessages([]); setSessionId(null); setCurrentResult(null);}} />
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
          {renderMessages()}
          {loading && <div style={{ textAlign: 'center' }}><Spin tip="AI 思考中..." /></div>}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ padding: '16px', background: '#fff' }}>
          <div style={{ border: '1px solid #d9d9d9', borderRadius: '12px', padding: '8px' }}>
            <TextArea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="问我任何关于数据的问题..."
              autoSize={{ minRows: 1, maxRows: 6 }}
              onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }}
              style={{ border: 'none', boxShadow: 'none', resize: 'none' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
              <Button type="text" icon={<PaperClipOutlined />} onClick={() => fileInputRef.current?.click()} loading={uploading} />
              <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={e => handleUpload(e.target.files[0])} />
              <Button type="primary" shape="round" icon={<SendOutlined />} onClick={handleSend} disabled={!question.trim()}>发送</Button>
            </div>
          </div>
        </div>
      </Sider>

      {/* 右侧结果展示区 */}
      <Content style={{ padding: '24px', overflowY: 'auto' }}>
        {error && <Alert message={error} type="error" showIcon closable style={{ marginBottom: 16 }} />}
        
        {!currentResult ? (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: '#bfbfbf' }}>
            <DatabaseOutlined style={{ fontSize: 64, marginBottom: 16 }} />
            <Paragraph>暂无执行结果，请在左侧提问</Paragraph>
          </div>
        ) : (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* SQL展示卡片 */}
            {currentResult.sql && (
              <Card title={<span><ConsoleSqlOutlined /> Generated SQL</span>} size="small" extra={<Tag color="blue">PostgreSQL</Tag>}>
                <pre style={{ background: '#1d1d1d', color: '#a9b7c6', padding: '16px', borderRadius: '8px', overflow: 'auto', fontSize: '13px' }}>
                  {currentResult.sql}
                </pre>
              </Card>
            )}

            {/* 数据表格卡片 */}
            {currentResult.result?.data && (
              <Card title={<span><DatabaseOutlined /> Execution Result</span>} size="small">
                <Table 
                  dataSource={currentResult.result.data}
                  columns={currentResult.result.columns?.map(col => ({ title: col, dataIndex: col, key: col }))}
                  size="small"
                  pagination={{ pageSize: 8 }}
                  scroll={{ x: 'max-content' }}
                />
              </Card>
            )}
          </Space>
        )}
      </Content>
    </Layout>
  );
}

export default App;

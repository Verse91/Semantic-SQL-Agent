import React, { useState, useEffect } from 'react';
import { Timeline, Card, Tag, Typography, Button, Spin } from 'antd';
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  DatabaseOutlined,
  CodeOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

export function TracePanel({ traceId, traceDate, onClose }) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (traceId) {
      fetchTrace();
    }
  }, [traceId, traceDate]);

  const fetchTrace = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
      // 用 trace 自己的日期查，不用 today（避免跨天查不到）
      const dateParam = traceDate || new Date().toISOString().slice(0, 10);
      const response = await fetch(`${API_BASE}/api/traces/${traceId}?date=${dateParam}`);
      const data = await response.json();
      setTrace(data);
    } catch (e) {
      console.error('Failed to fetch trace:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 20, textAlign: 'center' }}><Spin /></div>;
  }

  if (!trace || trace.error) {
    return <div style={{ padding: 20 }}>Trace not found</div>;
  }

  const getStepIcon = (stepName) => {
    if (stepName === 'schema_retriever') return <DatabaseOutlined />;
    if (stepName === 'generate_sql' || stepName === 'validate_sql') return <CodeOutlined />;
    if (stepName === 'execute_sql') return <PlayCircleOutlined />;
    return <ClockCircleOutlined />;
  };

  const getStatusColor = (status) => {
    if (status === 'success') return 'green';
    if (status === 'failed') return 'red';
    return 'blue';
  };

  return (
    <Card 
      size="small" 
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>🔍 Trace: {trace.query}</span>
          <Tag color={getStatusColor(trace.status)}>{trace.status}</Tag>
        </div>
      }
      extra={<Button size="small" onClick={onClose}>Close</Button>}
      style={{ marginTop: 16 }}
    >
      <div style={{ marginBottom: 12 }}>
        <Text type="secondary">
          {trace.start_time} → {trace.end_time}
        </Text>
      </div>
      
      <Timeline items={trace.steps.map((step, idx) => ({
        color: 'blue',
        children: (
          <div key={idx} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {getStepIcon(step.step_name)}
              <Text strong>{step.step_name}</Text>
            </div>
            
            {/* Input */}
            {step.input && Object.keys(step.input).length > 0 && (
              <div style={{ marginTop: 4, marginLeft: 24 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Input:</Text>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 8, 
                  borderRadius: 4, 
                  fontSize: 11,
                  marginTop: 2,
                  overflow: 'auto',
                  maxHeight: 100
                }}>
                  {JSON.stringify(step.input, null, 2)}
                </pre>
              </div>
            )}
            
            {/* Output */}
            {step.output && Object.keys(step.output).length > 0 && (
              <div style={{ marginTop: 4, marginLeft: 24 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Output:</Text>
                <pre style={{ 
                  background: '#f0f0f0', 
                  padding: 8, 
                  borderRadius: 4, 
                  fontSize: 11,
                  marginTop: 2,
                  overflow: 'auto',
                  maxHeight: 150
                }}>
                  {JSON.stringify(step.output, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )
      }))} />
    </Card>
  );
}

"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Square, Terminal, Settings, Activity, FileText, MessageSquare, Save, Sparkles, Book, Edit3, Code2, History, ChevronDown, RefreshCw, Plus } from 'lucide-react';
import { API_URL } from '@/config/api';
import ModularChatPanel from '../ModularChatPanel';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkBreaks from 'remark-breaks';

interface ModelTrainingModuleProps {
  taskId: string;
  subtask?: string;  // Optional subtask from global task selector
}

type TabType = 'config' | 'logs' | 'description' | 'code';

type AssistantMode = 'qa' | 'refine_problem' | 'refine_rubric' | 'improve_code';

interface CodeHistoryItem {
  id: string;
  code: string;
  summary: string;
  timestamp: number;
  result?: {
    success: boolean;
    images?: number;
  };
}

interface Subtask {
  name: string;
  description: string;
  has_description: boolean;
  has_rubric: boolean;
}

export default function ModelTrainingModule({ taskId, subtask }: ModelTrainingModuleProps) {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState('aide');
  const [selectedModel, setSelectedModel] = useState('');
  const [dataSource, setDataSource] = useState<'raw' | 'prepared'>('raw');

  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running'>('idle');
  const [logs, setLogs] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('config');
  const [assistantMode, setAssistantMode] = useState<AssistantMode>('qa');
  const [isRefreshingLogs, setIsRefreshingLogs] = useState(false);

  // Task description states
  const [taskDescription, setTaskDescription] = useState('');
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [isSavingDescription, setIsSavingDescription] = useState(false);
  const [descriptionLoaded, setDescriptionLoaded] = useState(false);

  // Rubric states
  const [rubricContent, setRubricContent] = useState('');
  const [isEditingRubric, setIsEditingRubric] = useState(false);
  const [isSavingRubric, setIsSavingRubric] = useState(false);
  const [rubricLoaded, setRubricLoaded] = useState(false);

  // Code execution states
  const [modelCode, setModelCode] = useState('');
  const [isEditingCode, setIsEditingCode] = useState(false);
  const [isExecutingCode, setIsExecutingCode] = useState(false);
  const [codeExecutionResult, setCodeExecutionResult] = useState<{
    success: boolean;
    stdout: string;
    stderr: string;
    images: string[];
  } | null>(null);
  const [codeHistory, setCodeHistory] = useState<CodeHistoryItem[]>([]);
  const [showCodeHistoryDropdown, setShowCodeHistoryDropdown] = useState(false);
  const [codeHistoryFiles, setCodeHistoryFiles] = useState<{name: string, filename: string, summary: string, timestamp: number}[]>([]);

  const logsEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Fetch workflows and models
  useEffect(() => {
    axios.get(`${API_URL}/workflows`)
      .then(res => {
        setWorkflows(res.data.workflows || []);
        if (res.data.workflows?.length > 0) {
          setSelectedWorkflow(res.data.workflows[0]);
        }
      })
      .catch(err => console.error("Failed to fetch workflows:", err));

    axios.get(`${API_URL}/models`)
      .then(res => {
        setModels(res.data.models || []);
        if (res.data.models?.length > 0) {
          setSelectedModel(res.data.models[0]);
        }
      })
      .catch(err => console.error("Failed to fetch models:", err));

    // Load task description and rubric
    fetchTaskDescription();
    fetchRubric();

    // Load initial logs and task status
    fetchLogs();
    checkTaskStatus();

    // Load code history
    fetchCodeHistory();
  }, [taskId]);

  // Refresh data when subtask changes
  useEffect(() => {
    if (subtask) {
      fetchTaskDescription();
      fetchRubric();
      fetchCodeHistory();
    }
  }, [subtask]);

  // Auto-refresh code history when switching to code tab
  useEffect(() => {
    if (activeTab === 'code') {
      console.log('🔄 Switched to code tab, refreshing code history...');
      fetchCodeHistory();
    }
  }, [activeTab]);

  // Auto-refresh logs when switching to logs tab
  useEffect(() => {
    if (activeTab === 'logs') {
      console.log('🔄 Switched to logs tab, refreshing logs...');
      fetchLogs();
    }
  }, [activeTab]);

  // Fetch task description
  const fetchTaskDescription = async () => {
    try {
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/subtasks/${subtask}`
        : `${API_URL}/tasks/${taskId}`;
      const res = await axios.get(url);
      setTaskDescription(res.data.description || '');
      setDescriptionLoaded(true);
    } catch (err) {
      console.error('Failed to fetch task description:', err);
      setDescriptionLoaded(true);
    }
  };

  // Fetch rubric
  const fetchRubric = async () => {
    try {
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/subtasks/${subtask}/rubric`
        : `${API_URL}/tasks/${taskId}/rubric`;
      const res = await axios.get(url);
      setRubricContent(res.data.content || '');
      setRubricLoaded(true);
    } catch (err) {
      console.error('Failed to fetch rubric:', err);
      setRubricLoaded(true);
    }
  };

  // Fetch logs from server
  const fetchLogs = async () => {
    setIsRefreshingLogs(true);
    try {
      const url = subtask
        ? `${API_URL}/logs/${taskId}?task=${subtask}`
        : `${API_URL}/logs/${taskId}`;
      console.log('🔄 Fetching logs from:', url);
      const res = await axios.get(url);
      const newLogs = res.data.logs || '';
      console.log('📡 Logs received, length:', newLogs.length);
      setLogs(newLogs);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      setLogs('');
    } finally {
      setIsRefreshingLogs(false);
    }
  };

  // Check if task is currently running
  const checkTaskStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/tasks/${taskId}`);
      const isRunning = res.data.is_running || false;
      if (isRunning) {
        setExecutionStatus('running');
      }
    } catch (err) {
      console.error('Failed to check task status:', err);
    }
  };

  // Fetch code history from backend
  const fetchCodeHistory = async () => {
    try {
      console.log('🔍 Fetching code history for task:', taskId, 'subtask:', subtask);
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/code-history?task=${subtask}`
        : `${API_URL}/tasks/${taskId}/code-history`;
      console.log('📍 API URL:', url);

      const res = await axios.get(url);
      console.log('📡 API Response status:', res.status);
      console.log('📡 API Response data keys:', Object.keys(res.data));
      console.log('📡 Number of files:', res.data.files?.length || 0);

      const allFiles = res.data.files || [];
      // Filter for model code only
      const historyFiles = allFiles.filter((f: any) => f.filename.includes("model_code"));

      console.log(`📦 Found ${historyFiles.length} model code history files`);

      if (historyFiles.length > 0) {
        console.log('📄 First file details:', {
          filename: historyFiles[0].filename,
          summary: historyFiles[0].summary,
          contentLength: historyFiles[0].content?.length || 0,
          timestamp: historyFiles[0].timestamp
        });
      }

      // Store file list for dropdown (without full content to save memory)
      const fileList = historyFiles.map((file: any) => ({
        name: file.summary || file.filename,
        filename: file.filename,
        summary: file.summary || `模型代码 - ${new Date(file.timestamp).toLocaleString()}`,
        timestamp: file.timestamp
      }));
      setCodeHistoryFiles(fileList);
      console.log('✅ File list updated:', fileList.length, 'items');

      // Convert to CodeHistoryItem format (with full content)
      const historyItems: CodeHistoryItem[] = historyFiles.map((file: any) => ({
        id: file.timestamp.toString(),
        code: file.content,
        summary: file.summary || `模型代码 - ${new Date(file.timestamp).toLocaleString()}`,
        timestamp: file.timestamp,
        result: {
          success: true, // Model code files are saved successfully
          images: 0
        }
      }));

      setCodeHistory(historyItems);
      console.log('✅ Code history state updated:', historyItems.length, 'items');

      // Load the most recent code into editor
      if (historyItems.length > 0) {
        const latestCode = historyItems[0].code;
        console.log('📝 Loading latest code into editor');
        console.log('  - Code length:', latestCode?.length || 0);
        console.log('  - Code preview (first 100 chars):', latestCode?.substring(0, 100) || 'NO CODE');

        setModelCode(latestCode);

        // Verify the state was updated
        setTimeout(() => {
          console.log('✅ State check after setModelCode - modelCode length:', modelCode.length);
        }, 100);

        console.log('✅ Loaded latest model code from history:', historyItems[0].summary);
      } else {
        console.log('⚠️ No code history items to load');
        setModelCode(''); // Ensure empty string if no history
      }
    } catch (err: any) {
      console.error('❌ No code history found or error loading:', err);
      console.error('  Error message:', err.message);
      console.error('  Error response:', err.response?.data);
      console.error('  Full error:', err);
      setCodeHistoryFiles([]);
      setCodeHistory([]);
      setModelCode(''); // Ensure empty string on error
    }
  };

  // Load code from history by filename
  const handleLoadCodeFromHistory = async (filename: string) => {
    try {
      console.log('📂 Loading code from history file:', filename);
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/code-history/file/${filename}?task=${subtask}`
        : `${API_URL}/tasks/${taskId}/code-history/file/${filename}`;
      const res = await axios.get(url);
      if (res.data && res.data.code) {
        setModelCode(res.data.code);
        setShowCodeHistoryDropdown(false);
        console.log('✅ Loaded code from history:', filename);
      }
    } catch (err) {
      console.error('❌ Failed to load code from history:', err);
      alert('加载代码失败');
    }
  };

  // Save task description
  const handleSaveDescription = async () => {
    setIsSavingDescription(true);
    try {
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/subtasks/${subtask}/description`
        : `${API_URL}/tasks/${taskId}/description/update`;
      await axios.post(url, {
        content: taskDescription
      });
      setIsEditingDescription(false);
      alert('任务描述已保存');
    } catch (err) {
      console.error('Failed to save task description:', err);
      alert('保存失败');
    } finally {
      setIsSavingDescription(false);
    }
  };

  // Save rubric
  const handleSaveRubric = async () => {
    setIsSavingRubric(true);
    try {
      const url = subtask
        ? `${API_URL}/tasks/${taskId}/subtasks/${subtask}/rubric`
        : `${API_URL}/tasks/${taskId}/rubric`;
      await axios.post(url, {
        content: rubricContent
      });
      setIsEditingRubric(false);
      alert('评估标准已保存');
    } catch (err) {
      console.error('Failed to save rubric:', err);
      alert('保存失败');
    } finally {
      setIsSavingRubric(false);
    }
  };

  // Poll logs and status when running
  useEffect(() => {
    let interval: any;
    if (executionStatus === 'running' && taskId) {
      interval = setInterval(() => {
        // Build logs URL with subtask parameter
        const logsUrl = subtask
          ? `${API_URL}/logs/${taskId}?task=${subtask}`
          : `${API_URL}/logs/${taskId}`;

        // Fetch both logs and status
        Promise.all([
          axios.get(logsUrl),
          axios.get(`${API_URL}/tasks/${taskId}`)
        ])
          .then(([logsRes, statusRes]) => {
            // Update logs
            setLogs(logsRes.data.logs || '');

            // Check if still running
            const isRunning = statusRes.data.is_running || false;
            if (!isRunning && executionStatus === 'running') {
              // Process has ended
              setExecutionStatus('idle');
            }
          })
          .catch(err => console.error('Failed to fetch logs/status:', err));
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [executionStatus, taskId, subtask]);

  const handleRun = async () => {
    if (!selectedWorkflow || !selectedModel) {
      alert('请选择工作流和模型');
      return;
    }

    setExecutionStatus('running');
    setActiveTab('logs');
    setLogs(''); // Clear previous logs

    try {
      const formData = new FormData();
      formData.append("workflow", selectedWorkflow);
      formData.append("task_id", taskId);
      formData.append("model", selectedModel);
      formData.append("data_source", dataSource); // Add data source parameter

      // Add subtask if in multi-task mode
      if (subtask) {
        formData.append("task", subtask);
      }

      await axios.post(`${API_URL}/run`, formData);
    } catch (e) {
      setExecutionStatus('idle');
      alert('启动失败: ' + (e as any).message);
    }
  };

  const handleStop = async () => {
    try {
      const response = await axios.post(`${API_URL}/tasks/${taskId}/stop`);
      const data = response.data;

      // 处理不同的停止状态
      if (data.status === 'stopped' || data.status === 'killed') {
        setExecutionStatus('idle');
        alert('训练已停止');
      } else if (data.status === 'already_stopped') {
        setExecutionStatus('idle');
        alert('训练已经结束');
      }
    } catch (e) {
      const errorMessage = (e as any).response?.data?.detail || (e as any).message || '未知错误';
      alert(`停止失败: ${errorMessage}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Tabs */}
      <div className="h-12 border-b flex bg-gray-50 shrink-0">
        <TabButton
          active={activeTab === 'config'}
          onClick={() => setActiveTab('config')}
          icon={<Settings size={16} />}
          label="配置"
        />
        <TabButton
          active={activeTab === 'description'}
          onClick={() => setActiveTab('description')}
          icon={<FileText size={16} />}
          label="任务描述"
        />
        <TabButton
          active={activeTab === 'logs'}
          onClick={() => setActiveTab('logs')}
          icon={<Terminal size={16} />}
          label="运行日志"
          badge={executionStatus === 'running' ? '运行中' : undefined}
        />
        <TabButton
          active={activeTab === 'code'}
          onClick={() => setActiveTab('code')}
          icon={<Code2 size={16} />}
          label="代码执行"
        />
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'config' && (
          <div className="h-full p-8 overflow-y-auto bg-gray-50">
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-xl shadow-sm p-8">
                <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                  <Activity size={24} className="text-blue-600" />
                  模型训练配置
                </h2>

                {/* Workflow Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    工作流
                  </label>
                  <select
                    value={selectedWorkflow}
                    onChange={e => setSelectedWorkflow(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {workflows.map(w => (
                      <option key={w} value={w}>{w}</option>
                    ))}
                  </select>
                  <p className="mt-2 text-xs text-gray-500">
                    选择用于训练的 AI 工作流
                  </p>
                </div>

                {/* Model Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    模型
                  </label>
                  <select
                    value={selectedModel}
                    onChange={e => setSelectedModel(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {models.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="mt-2 text-xs text-gray-500">
                    选择用于训练的语言模型
                  </p>
                </div>

                {/* Data Source Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-bold text-gray-700 mb-2">
                    📁 数据源
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setDataSource('raw')}
                      className={`flex-1 px-4 py-3 rounded-lg font-bold text-sm transition-all ${
                        dataSource === 'raw'
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      原始数据
                    </button>
                    <button
                      onClick={() => setDataSource('prepared')}
                      className={`flex-1 px-4 py-3 rounded-lg font-bold text-sm transition-all ${
                        dataSource === 'prepared'
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      处理后的数据
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    {dataSource === 'raw' ? '使用原始数据集进行训练' : '使用预处理后的数据集进行训练'}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t">
                  {executionStatus === 'running' ? (
                    <button
                      onClick={handleStop}
                      className="flex-1 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-colors"
                    >
                      <Square size={18} fill="currentColor" />
                      停止训练
                    </button>
                  ) : (
                    <button
                      onClick={handleRun}
                      disabled={!selectedWorkflow || !selectedModel}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Play size={18} fill="currentColor" />
                      开始训练
                    </button>
                  )}
                </div>

                {/* Status Hint */}
                {executionStatus === 'idle' && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      💡 <strong>提示:</strong> 点击"开始训练"后，工作流将自动读取数据并开始训练。
                      切换到"运行日志"标签查看实时输出。
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'description' && (
          <div className="h-full flex flex-col bg-white">
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Task Description Section */}
              <div className="flex-1 flex flex-col p-6 overflow-y-auto">
                <div className="max-w-4xl mx-auto w-full">
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <FileText size={24} className="text-blue-600" />
                        任务描述
                        {subtask && (
                          <span className="text-sm font-normal text-gray-500 ml-2">
                            ({subtask})
                          </span>
                        )}
                      </h2>
                      <div className="flex gap-2">
                        {isEditingDescription ? (
                          <>
                            <button
                              onClick={handleSaveDescription}
                              disabled={isSavingDescription}
                              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <Save size={16} />
                              {isSavingDescription ? '保存中...' : '保存'}
                            </button>
                            <button
                              onClick={() => {
                                setIsEditingDescription(false);
                                fetchTaskDescription(); // Revert changes
                              }}
                              disabled={isSavingDescription}
                              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-bold rounded-lg transition-colors disabled:opacity-50"
                            >
                              取消
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => setIsEditingDescription(true)}
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-bold rounded-lg flex items-center gap-2 transition-colors"
                          >
                            <Sparkles size={16} />
                            编辑描述
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      任务描述包含了数据集的背景、目标和评估指标。AI 助手会基于这个描述提供训练建议。
                    </p>

                    {/* Description Content */}
                    {isEditingDescription ? (
                      <textarea
                        value={taskDescription}
                        onChange={e => setTaskDescription(e.target.value)}
                        className="w-full h-64 border border-gray-300 rounded-lg p-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-mono"
                        placeholder="输入任务描述..."
                      />
                    ) : (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                        {taskDescription ? (
                          <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                            {taskDescription}
                          </div>
                        ) : (
                          <div className="text-center text-gray-400 py-12">
                            <FileText size={48} className="mx-auto mb-4 opacity-50" />
                            <p className="text-sm">暂无任务描述</p>
                            <p className="text-xs mt-2">点击"编辑描述"添加任务说明</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Rubric Section */}
                  <div className="border-t pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <Book size={24} className="text-amber-600" />
                        评估标准（Rubric）
                      </h2>
                      <div className="flex gap-2">
                        {isEditingRubric ? (
                          <>
                            <button
                              onClick={handleSaveRubric}
                              disabled={isSavingRubric}
                              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <Save size={16} />
                              {isSavingRubric ? '保存中...' : '保存'}
                            </button>
                            <button
                              onClick={() => {
                                setIsEditingRubric(false);
                                fetchRubric(); // Revert changes
                              }}
                              disabled={isSavingRubric}
                              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-bold rounded-lg transition-colors disabled:opacity-50"
                            >
                              取消
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => setIsEditingRubric(true)}
                            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-bold rounded-lg flex items-center gap-2 transition-colors"
                          >
                            <Edit3 size={16} />
                            编辑标准
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      评估标准定义了AI提交结果的评分规则。开放式任务会自动生成评分标准，您也可以手动编辑。
                    </p>

                    {/* Rubric Content */}
                    {isEditingRubric ? (
                      <textarea
                        value={rubricContent}
                        onChange={e => setRubricContent(e.target.value)}
                        className="w-full h-64 border border-gray-300 rounded-lg p-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-y font-mono"
                        placeholder="输入评估标准..."
                      />
                    ) : (
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
                        {rubricContent ? (
                          <div className="prose prose-sm max-w-none">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
                              rehypePlugins={[rehypeKatex]}
                            >
                              {rubricContent}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <div className="text-center text-gray-400 py-12">
                            <Book size={48} className="mx-auto mb-4 opacity-50" />
                            <p className="text-sm">暂无评估标准</p>
                            <p className="text-xs mt-2">开放式任务会自动生成评估标准，或点击"编辑标准"手动添加</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* AI Assistant Section */}
                  <div className="border-t pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <MessageSquare size={20} className="text-purple-600" />
                        AI 训练助手
                      </h3>
                      <select
                        value={assistantMode}
                        onChange={(e) => setAssistantMode(e.target.value as AssistantMode)}
                        className="px-3 py-1.5 text-xs font-bold border border-purple-200 rounded-lg bg-purple-50 text-purple-700 outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
                      >
                        <option value="qa">💬 问答助手</option>
                        <option value="refine_problem">📝 改进问题定义</option>
                        <option value="refine_rubric">📊 改进评分标准</option>
                        <option value="improve_code">💻 改进代码</option>
                      </select>
                    </div>

                    <p className="text-sm text-gray-600 mb-4">
                      {assistantMode === 'qa' && '回答关于模型训练、数据准备和评估的问题。'}
                      {assistantMode === 'refine_problem' && '帮助改进和完善任务描述，使其更清晰、更可执行。'}
                      {assistantMode === 'refine_rubric' && '优化评分标准，使其更客观、可衡量。'}
                      {assistantMode === 'improve_code' && '分析并改进模型训练代码，修复bug并提升性能。'}
                    </p>

                    <div className="h-96 border border-gray-200 rounded-lg overflow-hidden">
                      <ModularChatPanel
                        taskId={taskId}
                        mode="model"
                        dataSource="raw"
                        assistantMode={assistantMode}
                        onCodeGenerated={(code) => {
                          setModelCode(code);
                          setActiveTab('code');
                        }}
                        onDescriptionUpdate={(content) => {
                          setTaskDescription(content);
                          console.log('✅ Description updated in ModelTrainingModule');
                        }}
                        onRubricUpdate={(content) => {
                          setRubricContent(content);
                          console.log('✅ Rubric updated in ModelTrainingModule');
                        }}
                        onModelCodeUpdate={(code, path) => {
                          setModelCode(code);
                          console.log('✅ Model code updated in ModelTrainingModule:', path);
                          // Refresh code history to get the latest
                          fetchCodeHistory();
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="h-full flex flex-col bg-[#0f172a]">
            {/* Logs Header */}
            <div className="px-6 py-3 bg-slate-800/50 border-b border-white/10 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <Terminal size={16} className="text-slate-400" />
                <span className="text-sm font-bold text-slate-300">训练日志</span>
                {executionStatus === 'running' && (
                  <span className="px-2 py-1 bg-green-900/50 text-green-400 text-xs font-bold rounded flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    运行中
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    console.log('🔄 Manual log refresh triggered');
                    fetchLogs();
                  }}
                  disabled={isRefreshingLogs}
                  className={`px-3 py-1.5 text-slate-300 text-xs font-bold rounded flex items-center gap-1.5 transition-colors ${
                    isRefreshingLogs
                      ? 'bg-slate-800 cursor-not-allowed opacity-60'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                  title="刷新日志"
                >
                  <RefreshCw size={12} className={isRefreshingLogs ? 'animate-spin' : ''} />
                  {isRefreshingLogs ? '刷新中...' : '刷新'}
                </button>
                {executionStatus === 'running' && (
                  <button
                    onClick={handleStop}
                    className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded flex items-center gap-1.5 transition-colors"
                  >
                    <Square size={12} fill="currentColor" />
                    停止
                  </button>
                )}
              </div>
            </div>

            {/* Logs Content */}
            <div className="flex-1 overflow-y-auto p-6 font-mono text-xs">
              {logs ? (
                <pre className="text-slate-300 whitespace-pre-wrap">
                  {logs.split('\n').map((line, i) => (
                    <div key={i}>{line}</div>
                  ))}
                </pre>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-600">
                  {executionStatus === 'running'
                    ? '等待日志输出...'
                    : '点击"开始训练"查看日志'}
                </div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div className="h-full flex flex-col bg-[#0f172a]">
            {/* Code Editor Header */}
            <div className="px-6 py-3 bg-slate-800/50 border-b border-white/10 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-3">
                <Code2 size={16} className="text-slate-400" />
                <span className="text-sm font-bold text-slate-300">模型训练代码</span>
                <button
                  onClick={() => {
                    console.log('🔄 Manual refresh triggered');
                    fetchCodeHistory();
                  }}
                  className="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-xs font-bold flex items-center gap-1 transition-colors"
                  title="刷新代码历史"
                >
                  <RefreshCw size={12} />
                  刷新
                </button>

                {/* Code History Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setShowCodeHistoryDropdown(!showCodeHistoryDropdown)}
                    className={`px-2 py-1 text-xs font-bold rounded flex items-center gap-1 transition-colors ${
                      codeHistoryFiles.length > 0
                        ? 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-60'
                    }`}
                    title={codeHistoryFiles.length > 0 ? "历史代码" : "暂无历史记录"}
                    disabled={codeHistoryFiles.length === 0}
                  >
                    <History size={12} />
                    历史 {codeHistoryFiles.length > 0 && `(${codeHistoryFiles.length})`}
                    {codeHistoryFiles.length > 0 && (
                      <ChevronDown size={12} className={`transition-transform ${showCodeHistoryDropdown ? 'rotate-180' : ''}`} />
                    )}
                  </button>

                  {showCodeHistoryDropdown && codeHistoryFiles.length > 0 && (
                    <div className="absolute top-full left-0 mt-2 w-96 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                      <div className="p-2 border-b border-slate-700">
                        <div className="text-xs text-slate-400 font-bold px-2">代码历史文件</div>
                      </div>
                      <div className="p-2">
                        {codeHistoryFiles.map((file, idx) => (
                          <button
                            key={idx}
                            onClick={() => {
                              handleLoadCodeFromHistory(file.filename);
                              setShowCodeHistoryDropdown(false);
                            }}
                            className="w-full text-left px-3 py-2 rounded hover:bg-slate-700 transition-colors mb-1 last:mb-0 group"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-bold text-slate-200 truncate flex-1">
                                {file.name}
                              </span>
                            </div>
                            <div className="text-[10px] text-slate-500">
                              {new Date(file.timestamp).toLocaleString('zh-CN')}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditingCode(!isEditingCode)}
                  className={`px-3 py-1 rounded text-xs font-bold flex items-center gap-2 transition-all ${
                    isEditingCode ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Edit3 size={12} />
                  {isEditingCode ? '保存并锁定' : '编辑代码'}
                </button>
                <button
                  onClick={async () => {
                    setIsExecutingCode(true);
                    try {
                      const formData = new FormData();
                      formData.append('code', modelCode);
                      const res = await axios.post(`${API_URL}/tasks/${taskId}/model/execute`, formData);
                      setCodeExecutionResult(res.data);

                      // Add to history
                      const historyItem: CodeHistoryItem = {
                        id: Date.now().toString(),
                        code: modelCode,
                        summary: `训练执行 - ${new Date().toLocaleTimeString()}`,
                        timestamp: Date.now(),
                        result: {
                          success: res.data.success,
                          images: res.data.images?.length || 0
                        }
                      };
                      setCodeHistory(prev => [historyItem, ...prev]);
                    } catch (e) {
                      alert('代码执行失败');
                    } finally {
                      setIsExecutingCode(false);
                    }
                  }}
                  disabled={isExecutingCode || !modelCode.trim()}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1 rounded text-xs font-bold flex items-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isExecutingCode ? <RefreshCw size={12} className="animate-spin" /> : <Play size={12} fill="currentColor" />}
                  运行代码
                </button>
              </div>
            </div>

            {/* Code Editor */}
            <div className="h-1/2 flex flex-col border-b border-white/10 shrink-0">
              {/* Debug panel - temporary */}
              <div className="bg-slate-900 border-b border-white/10 px-4 py-2 text-xs font-mono">
                <div className="flex items-center gap-4 text-slate-400">
                  <span>🐛 DEBUG:</span>
                  <span>modelCode.length = {modelCode.length}</span>
                  <span>codeHistoryFiles.length = {codeHistoryFiles.length}</span>
                  <span className={modelCode.length > 0 ? 'text-green-400' : 'text-yellow-400'}>
                    {modelCode.length > 0 ? '✅ CODE LOADED' : '⚠️ NO CODE'}
                  </span>
                </div>
              </div>
              <textarea
                value={modelCode}
                onChange={e => setModelCode(e.target.value)}
                readOnly={!isEditingCode}
                className={`flex-1 w-full bg-[#1e293b] text-emerald-400 p-8 font-mono text-xs outline-none resize-none leading-relaxed ${
                  !isEditingCode ? 'opacity-70' : ''
                }`}
                placeholder="# 在此编写或从AI助手生成模型训练代码...
# 示例:
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 加载数据
train_df = pd.read_csv('prepared/public/train.csv')
test_df = pd.read_csv('prepared/public/test.csv')

# 准备特征和目标
X = train_df.drop(['target', 'id'], axis=1)
y = train_df['target']

# 划分训练集和验证集
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练模型
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 验证
val_preds = model.predict(X_val)
accuracy = accuracy_score(y_val, val_preds)
print(f'Validation Accuracy: {accuracy:.4f}')

# 预测测试集
test_features = test_df.drop(['id'], axis=1)
test_preds = model.predict(test_features)

# 保存结果
submission = pd.DataFrame({
  'id': test_df['id'],
  'target': test_preds
})
submission.to_csv('submission.csv', index=False)
print('Submission saved!')
"
              />
            </div>

            {/* Execution Output */}
            <div className="h-1/4 flex flex-col border-b border-white/10 overflow-hidden bg-[#020617] shrink-0">
              <div className="px-6 py-1.5 bg-black/40 text-[9px] text-slate-500 font-mono font-bold uppercase tracking-widest flex items-center gap-2 border-b border-white/5">
                <Terminal size={12} />
                执行输出
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-4">
                {codeExecutionResult ? (
                  <div className="animate-in fade-in slide-in-from-top-2">
                    {codeExecutionResult.stdout && (
                      <pre className="text-slate-300 font-mono text-xs whitespace-pre-wrap bg-white/5 p-5 rounded-lg border border-white/5 mb-4">
                        {codeExecutionResult.stdout}
                      </pre>
                    )}
                    {codeExecutionResult.stderr && (
                      <pre className="text-red-400 font-mono text-xs whitespace-pre-wrap bg-red-900/10 p-5 rounded-lg border border-red-900/20 mb-4">
                        {codeExecutionResult.stderr}
                      </pre>
                    )}
                    {codeExecutionResult.images?.length > 0 && (
                      <div className="grid grid-cols-2 gap-6">
                        {codeExecutionResult.images.map((img, i) => (
                          <div key={i} className="bg-white/5 p-2 rounded-xl border border-white/10">
                            <img src={`http://localhost:8003${img}`} className="w-full h-auto rounded-lg shadow-2xl" alt="plot" />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center opacity-10 text-white text-[10px] font-mono tracking-widest">
                    等待执行代码...
                  </div>
                )}
              </div>
            </div>

            {/* Code History */}
            <div className="flex-1 flex flex-col overflow-hidden bg-white rounded-t-[2.5rem] shadow-inner">
              <div className="px-10 py-4 border-b bg-gray-50/50 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                  <History size={16} className="text-blue-600" />
                  <span className="text-sm font-bold text-gray-700">代码历史</span>
                  <span className="text-xs text-gray-500">({codeHistory.length} 条记录)</span>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {codeHistory.length === 0 ? (
                  <div className="text-center text-gray-400 py-12">
                    <History size={48} className="mx-auto mb-4 opacity-50" />
                    <p className="text-sm">暂无代码历史</p>
                    <p className="text-xs mt-2">执行代码后会自动保存历史记录</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {codeHistory.map(item => (
                      <div
                        key={item.id}
                        className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                        onClick={() => setModelCode(item.code)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold text-gray-700">{item.summary}</span>
                          <div className="flex items-center gap-2">
                            {item.result?.success !== undefined && (
                              <span className={`text-[10px] px-2 py-0.5 rounded ${
                                item.result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                              }`}>
                                {item.result.success ? '成功' : '失败'}
                              </span>
                            )}
                            {item.result?.images !== undefined && item.result.images > 0 && (
                              <span className="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                {item.result.images} 图表
                              </span>
                            )}
                          </div>
                        </div>
                        <pre className="text-xs text-gray-600 font-mono truncate max-h-16 overflow-hidden">
                          {item.code.substring(0, 200)}...
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
  badge
}: {
  active: boolean;
  onClick: () => void;
  icon: any;
  label: string;
  badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        px-6 text-xs font-bold flex items-center gap-2 border-b-2 transition-colors relative
        ${active
          ? 'border-blue-600 text-blue-600 bg-white'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
      `}
    >
      {icon}
      {label}
      {badge && (
        <span className="ml-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded">
          {badge}
        </span>
      )}
    </button>
  );
}

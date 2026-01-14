"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Code2, RefreshCw, AlertCircle, Bot, CheckCircle2, History, ChevronDown } from 'lucide-react';
import { DATA_SOURCES, CHAT_SUGGESTIONS } from '@/config/modules';
import ModularChatPanel from '../ModularChatPanel';
import { API_URL } from '@/config/api';

interface DataExploreModuleProps {
  taskId: string;
  subtask?: string;
}

type TabType = 'chat' | 'code';

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

export default function DataExploreModule({ taskId, subtask }: DataExploreModuleProps) {
  // Code history state
  const [codeHistory, setCodeHistory] = useState<CodeHistoryItem[]>(() => {
    // 从 localStorage 恢复历史记录
    if (typeof window !== 'undefined') {
      try {
        const storageKey = `chat_${taskId}_explore_code_history`;
        const saved = localStorage.getItem(storageKey);
        return saved ? JSON.parse(saved) : [];
      } catch (e) {
        return [];
      }
    }
    return [];
  });
  const [showHistoryDropdown, setShowHistoryDropdown] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [dataSource, setDataSource] = useState<'raw' | 'processed'>('raw');
  const [workspaceFiles, setWorkspaceFiles] = useState<{name: string, size: string, is_dir: boolean}[]>([]);
  const [codeHistoryFiles, setCodeHistoryFiles] = useState<{name: string, size: string, is_dir: boolean}[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Content states
  const [edaCode, setEdaCodeState] = useState(() => {
    // 从 localStorage 恢复代码
    if (typeof window !== 'undefined') {
      const storageKey = `chat_${taskId}_explore_${dataSource}_generated_code`;
      const saved = localStorage.getItem(storageKey);
      return saved || '';
    }
    return '';
  });

  // 包装 setEdaCode 以同时保存到 localStorage
  const setEdaCode = (code: string | ((prev: string) => string)) => {
    setEdaCodeState(prev => {
      const newCode = typeof code === 'function' ? code(prev) : code;
      // 保存到 localStorage
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_explore_${dataSource}_generated_code`;
        localStorage.setItem(storageKey, newCode);
      }
      return newCode;
    });
  };
  const [isEditingEda, setIsEditingEda] = useState(false);
  const [edaResult, setEdaResult] = useState<{stdout: string, stderr: string, images: string[], success: boolean} | null>(() => {
    // 从 localStorage 恢复执行结果
    if (typeof window !== 'undefined') {
      try {
        const storageKey = `chat_${taskId}_explore_${dataSource}_execution_result`;
        const saved = localStorage.getItem(storageKey);
        return saved ? JSON.parse(saved) : null;
      } catch (e) {
        return null;
      }
    }
    return null;
  });
  const [isExecuting, setIsExecutingState] = useState(() => {
    // 从 localStorage 恢复执行状态
    if (typeof window !== 'undefined') {
      const storageKey = `chat_${taskId}_explore_${dataSource}_is_executing`;
      const saved = localStorage.getItem(storageKey);

      // Clear the executing state on page load to prevent stuck states
      localStorage.removeItem(storageKey);

      // Don't restore stuck executing state - always start fresh
      return false; // saved === 'true';
    }
    return false;
  });

  // 包装 setIsExecuting 以同时保存到 localStorage
  const setIsExecuting = (value: boolean | ((prev: boolean) => boolean)) => {
    setIsExecutingState(prev => {
      const newValue = typeof value === 'function' ? value(prev) : value;
      // 保存到 localStorage
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_explore_${dataSource}_is_executing`;
        localStorage.setItem(storageKey, String(newValue));
      }
      return newValue;
    });
  };

  const [pendingFixMessage, setPendingFixMessage] = useState<string>("");

  // Fetch workspace files (data files only)
  const fetchWorkspaceFiles = async () => {
    setIsRefreshing(true);
    try {
      // Map dataSource to backend view parameter
      const viewParam = dataSource === 'processed' ? 'prepared_data' : 'data';
      const res = await axios.get(`${API_URL}/tasks/${taskId}/workspace/files?view=${viewParam}`, {
        timeout: 10000 // 10 seconds timeout
      });
      setWorkspaceFiles(res.data.files || []);
    } catch (e) {
      console.error('Failed to fetch workspace files:', e);
      setWorkspaceFiles([]);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Fetch code history files
  const fetchCodeHistoryFiles = async () => {
    try {
      const res = await axios.get(`${API_URL}/tasks/${taskId}/workspace/code_history`, {
        timeout: 10000 // 10 seconds timeout
      });
      // Filter for explore code only
      const allFiles = res.data.files || [];
      const exploreFiles = allFiles.filter((f: any) => f.name.includes("explore_code"));
      setCodeHistoryFiles(exploreFiles);
    } catch (e) {
      console.error('Failed to fetch code history files:', e);
      setCodeHistoryFiles([]);
    }
  };

  // Fetch initial data
  useEffect(() => {
    if (taskId) {
      fetchWorkspaceFiles();
      fetchCodeHistoryFiles();
    }
  }, [taskId, dataSource]);

  // Cleanup: Clear executing state on unmount to prevent stuck states
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && taskId) {
        const storageKey = `chat_${taskId}_explore_${dataSource}_is_executing`;
        localStorage.removeItem(storageKey);
        console.log('🧹 Cleared executing state on unmount');
      }
    };
  }, [taskId, dataSource]);

  // 当 dataSource 切换时，恢复对应数据源的代码和结果
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const storageKey = `chat_${taskId}_explore_${dataSource}_generated_code`;
    const savedCode = localStorage.getItem(storageKey);
    if (savedCode !== null) {
      setEdaCodeState(savedCode);
    }

    const resultKey = `chat_${taskId}_explore_${dataSource}_execution_result`;
    const savedResult = localStorage.getItem(resultKey);
    if (savedResult !== null) {
      try {
        setEdaResult(JSON.parse(savedResult));
      } catch (e) {
        setEdaResult(null);
      }
    } else {
      setEdaResult(null);
    }
  }, [dataSource, taskId]);

  // 监听 localStorage 变化（当对话标签页生成代码并执行后）
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const resultKey = `chat_${taskId}_explore_${dataSource}_execution_result`;
    const codeKey = `chat_${taskId}_explore_${dataSource}_generated_code`;
    const historyKey = `chat_${taskId}_explore_code_history`;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === resultKey && e.newValue) {
        try {
          const newResult = JSON.parse(e.newValue);
          console.log('🔄 Execution result updated from chat:', newResult);
          setEdaResult(newResult);
        } catch (e) {
          console.error('Failed to parse execution result:', e);
        }
      } else if (e.key === codeKey && e.newValue) {
        console.log('🔄 Code updated from chat:', e.newValue.substring(0, 100));
        setEdaCodeState(e.newValue);
      } else if (e.key === historyKey && e.newValue) {
        try {
          const newHistory = JSON.parse(e.newValue);
          console.log('🔄 Code history updated from chat:', newHistory.length, 'items');
          setCodeHistory(newHistory);
        } catch (e) {
          console.error('Failed to parse code history:', e);
        }
      }
    };

    // Listen for storage events (cross-tab)
    window.addEventListener('storage', handleStorageChange);

    // Also poll for same-tab changes (React doesn't detect same-tab localStorage changes)
    const interval = setInterval(() => {
      const currentResult = localStorage.getItem(resultKey);
      const currentCode = localStorage.getItem(codeKey);
      const currentHistory = localStorage.getItem(historyKey);

      // Check if result changed
      if (currentResult) {
        try {
          const parsed = JSON.parse(currentResult);
          // Compare with current state to avoid unnecessary updates
          if (JSON.stringify(parsed) !== JSON.stringify(edaResult)) {
            console.log('🔄 Polling detected execution result change');
            setEdaResult(parsed);
          }
        } catch (e) {
          // Ignore parse errors
        }
      }

      // Check if code changed
      if (currentCode && currentCode !== edaCode) {
        console.log('🔄 Polling detected code change');
        setEdaCodeState(currentCode);
      }

      // Check if history changed
      if (currentHistory) {
        try {
          const parsed = JSON.parse(currentHistory);
          if (parsed.length !== codeHistory.length) {
            console.log('🔄 Polling detected code history change:', parsed.length, 'items');
            setCodeHistory(parsed);
          }
        } catch (e) {
          // Ignore parse errors
        }
      }
    }, 500); // Poll every 500ms

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [taskId, dataSource, edaResult, edaCode, codeHistory.length]);

  const handleExecuteCode = async () => {
    if (!edaCode.trim()) return;
    setIsExecuting(true);
    try {
      // Map dataSource to backend view parameter
      const viewParam = dataSource === 'processed' ? 'prepared_data' : 'data';
      const formData = new FormData();
      formData.append("code", edaCode);
      formData.append("view", viewParam);

      // Add timeout to prevent hanging if server is down
      const res = await axios.post(`${API_URL}/tasks/${taskId}/execute`, {
        code: tempCode || generatedCode
      }, {
        timeout: 1800000, // 30 minutes timeout
      });
      setEdaResult(res.data);

      // 保存执行结果到 localStorage
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_explore_${dataSource}_execution_result`;
        localStorage.setItem(storageKey, JSON.stringify(res.data));
      }

      // Save to code history with summary
      const summary = generateCodeSummary(edaCode);
      const historyItem: CodeHistoryItem = {
        id: Date.now().toString(),
        code: edaCode,
        summary,
        timestamp: Date.now(),
        result: {
          success: res.data.success || false,
          images: res.data.images?.length || 0
        }
      };

      setCodeHistory(prev => {
        const newHistory = [historyItem, ...prev].slice(0, 20); // Keep only last 20 items
        // Save to localStorage
        if (typeof window !== 'undefined') {
          const historyStorageKey = `chat_${taskId}_explore_code_history`;
          localStorage.setItem(historyStorageKey, JSON.stringify(newHistory));
        }
        return newHistory;
      });

      // Auto-refresh workspace files to show new code files
      await fetchWorkspaceFiles();
      await fetchCodeHistoryFiles();
      console.log('✅ Workspace files and code history refreshed after code execution');
    } catch (e: any) {
      console.error('❌ Code execution failed:', e);

      // Better error messages
      if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
        alert('❌ 请求超时：后端处理时间过长，请检查后端状态或稍后重试。');
      } else if (e.code === 'ECONNREFUSED' || !e.response) {
        alert('❌ 无法连接到后端服务：请确认后端服务器正在运行。');
      } else if (e.response) {
        alert(`❌ 执行失败：${e.response.data?.detail || e.response.statusText || '未知错误'}`);
      } else {
        alert(`❌ 执行失败：${e.message || '未知错误'}`);
      }
    } finally {
      setIsExecuting(false);
    }
  };

  // Generate a summary for the code
  const generateCodeSummary = (code: string): string => {
    const lowerCode = code.toLowerCase();

    if (lowerCode.includes('describe()') || lowerCode.includes('.info()') || lowerCode.includes('.head()')) {
      return '📊 数据概览';
    }
    if (lowerCode.includes('plt.') || lowerCode.includes('sns.') || lowerCode.includes('fig') || lowerCode.includes('plot')) {
      return '📈 可视化图表';
    }
    if (lowerCode.includes('corr()') || lowerCode.includes('correlation')) {
      return '🔗 相关性分析';
    }
    if (lowerCode.includes('groupby') || lowerCode.includes('pivot')) {
      return '📋 数据分组';
    }
    if (lowerCode.includes('merge') || lowerCode.includes('concat')) {
      return '🔗 数据合并';
    }
    if (lowerCode.includes('fillna') || lowerCode.includes('dropna')) {
      return '🧹 数据清洗';
    }
    if (lowerCode.includes('.fit(') || lowerCode.includes('predict')) {
      return '🤖 模型训练';
    }
    if (lowerCode.includes('import') && lowerCode.includes('pd.read')) {
      return '📁 数据加载';
    }

    return '💻 数据分析';
  };

  const handleSelectHistory = (item: CodeHistoryItem) => {
    setEdaCode(item.code);
    setShowHistoryDropdown(false);
  };

  const handleRequestAIFix = () => {
    if (!edaResult?.stderr) return;

    const fixMessage = `我的代码执行出错了，请帮我修复：

\`\`\`python
${edaCode}
\`\`\`

错误信息：
\`\`\`
${edaResult.stderr}
\`\`\`

请提供修复后的代码。`;

    setPendingFixMessage(fixMessage);
    setActiveTab('chat');
  };

  const handleRequestAIDebug = () => {
    if (!edaCode.trim()) return;

    let debugMessage: string;

    if (edaResult?.stderr) {
      // 有错误信息，请求修复
      debugMessage = `我的代码执行出错了，请帮我调试并修复：

\`\`\`python
${edaCode}
\`\`\`

错误信息：
\`\`\`
${edaResult.stderr}
\`\`\`

请分析错误原因并提供修复后的完整代码。`;
    } else {
      // 没有错误，请求代码审查和优化
      debugMessage = `请帮我审查并优化以下代码：

\`\`\`python
${edaCode}
\`\`\`

请检查：
1. 代码逻辑是否正确
2. 是否有潜在的性能问题
3. 是否有更好的实现方式
4. 是否需要添加错误处理

如果代码没有问题，请告诉我代码是正确的。如果有改进建议，请提供优化后的代码。`;
    }

    setPendingFixMessage(debugMessage);
    setActiveTab('chat');
  };

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await fetchWorkspaceFiles();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleLoadCodeFromHistory = async (filename: string) => {
    try {
      // Filename is now clean (no code_history/ prefix from backend)
      const res = await axios.get(`${API_URL}/tasks/${taskId}/workspace/code/${filename}`, {
        timeout: 10000 // 10 seconds timeout
      });
      if (res.data && res.data.code) {
        setEdaCode(res.data.code);
        // Also switch to code tab
        setActiveTab('code');
        console.log(`✅ Loaded code from history: ${filename}`);
      }
    } catch (e) {
      console.error('Failed to load code from history:', e);
      alert('加载代码失败');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Data Source Selector */}
      <div className="h-12 border-b flex items-center px-6 bg-gray-50 shrink-0">
        <span className="text-xs font-bold text-gray-500 uppercase mr-4">数据源:</span>
        <div className="flex gap-2">
          {DATA_SOURCES.map((source) => (
            <button
              key={source.id}
              onClick={() => setDataSource(source.id)}
              className={`
                px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2
                ${dataSource === source.id
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}
              `}
            >
              <span>{source.icon}</span>
              {source.label}
            </button>
          ))}
        </div>
        <button
          onClick={fetchWorkspaceFiles}
          className="ml-auto p-2 hover:bg-gray-200 rounded-lg transition-colors"
          title="刷新文件列表"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-blue-600' : 'text-gray-400'} />
        </button>
      </div>

      {/* Workspace Files Bar */}
      <div className="h-10 border-b flex items-center px-6 bg-white shrink-0 overflow-x-auto">
        <span className="text-xs font-bold text-gray-400 uppercase mr-3 whitespace-nowrap">
          文件:
        </span>
        <div className="flex gap-2">
          {workspaceFiles.length === 0 ? (
            <span className="text-xs text-gray-400">暂无文件</span>
          ) : (
            workspaceFiles.map((file, i) => (
              <button
                key={i}
                className="px-2 py-1 rounded text-xs whitespace-nowrap transition-colors bg-gray-100 text-gray-600 cursor-default"
                title={file.name}
              >
                {file.name}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="h-12 border-b flex bg-gray-50 shrink-0">
        <TabButton
          active={activeTab === 'chat'}
          onClick={() => setActiveTab('chat')}
          icon={<MessageSquare size={16} />}
          label="对话探索"
        />
        <TabButton
          active={activeTab === 'code'}
          onClick={() => setActiveTab('code')}
          icon={<Code2 size={16} />}
          label="代码执行"
        />
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {activeTab === 'chat' && (
          <>
            {/* Execution Status Banner - Compact */}
            {(isExecuting || edaResult) && (
              <div className={`border-b px-3 py-1.5 shrink-0 flex items-center justify-between gap-2 ${
                isExecuting
                  ? 'bg-blue-50 border-blue-200'
                  : edaResult?.success
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center gap-2">
                  {isExecuting ? (
                    <>
                      <RefreshCw size={12} className="text-blue-600 animate-spin" />
                      <span className="text-xs text-blue-800 font-medium">执行中...</span>
                    </>
                  ) : edaResult ? (
                    <>
                      {edaResult.success ? (
                        <CheckCircle2 size={12} className="text-green-600" />
                      ) : (
                        <AlertCircle size={12} className="text-red-600" />
                      )}
                      <span className={`text-xs font-medium ${
                        edaResult.success ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {edaResult.success
                          ? `✅ 成功 · ${edaResult.images?.length || 0} 图表`
                          : '❌ 执行失败'}
                      </span>
                    </>
                  ) : null}
                </div>
                <div className="flex items-center gap-1.5">
                  {!isExecuting && edaResult?.images && edaResult.images.length > 0 && (
                    <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                      📊 {edaResult.images.length}
                    </span>
                  )}
                  {!isExecuting && edaResult && !edaResult.success && (
                    <button
                      onClick={handleRequestAIFix}
                      className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-medium rounded transition-colors flex items-center gap-1"
                    >
                      <Bot size={10} />
                      修复
                    </button>
                  )}
                  {!isExecuting && edaResult && (
                    <button
                      onClick={() => setActiveTab('code')}
                      className="px-2 py-1 bg-white hover:bg-gray-50 text-gray-600 text-[10px] font-medium rounded border border-gray-200 transition-colors"
                    >
                      查看详情
                    </button>
                  )}
                </div>
              </div>
            )}

            <div className="flex-1 overflow-hidden">
              <ModularChatPanel
                taskId={taskId}
                mode="explore"
                dataSource={dataSource}
                suggestions={CHAT_SUGGESTIONS.explore}
                initialMessage={pendingFixMessage}
                disabled={isExecuting}
                onCodeGenerated={(code, isDebugResult = false) => {
                  setEdaCode(code);
                  // Don't auto-switch tabs - let user stay in chat to see the response
                  // User can manually switch to code tab if needed
                  // if (!isDebugResult) {
                  //   setActiveTab('code');
                  // }
                  setPendingFixMessage(""); // 清除待修复消息
                }}
              />
            </div>
          </>
        )}

        {activeTab === 'code' && (
          <div className="h-full flex flex-col bg-[#0f172a]">
            {/* Code Editor */}
            <div className="flex-1 flex flex-col border-b border-white/10">
              <div className="px-6 py-2 bg-slate-800/50 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-blue-400 font-mono font-bold">PYTHON 代码</span>

                  {/* Code History Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                      className={`px-2 py-1 text-xs font-bold rounded flex items-center gap-1 transition-colors ${
                        (codeHistory.length > 0 || codeHistoryFiles.length > 0)
                          ? 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                          : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-60'
                      }`}
                      title={(codeHistory.length > 0 || codeHistoryFiles.length > 0) ? "历史代码" : "暂无历史记录"}
                      disabled={codeHistory.length === 0 && codeHistoryFiles.length === 0}
                    >
                      <History size={12} />
                      历史 {codeHistory.length > 0 && `(${codeHistory.length})`}
                      {(codeHistory.length > 0 || codeHistoryFiles.length > 0) && (
                        <ChevronDown size={12} className={`transition-transform ${showHistoryDropdown ? 'rotate-180' : ''}`} />
                      )}
                    </button>

                    {showHistoryDropdown && (codeHistory.length > 0 || codeHistoryFiles.length > 0) && (
                      <div className="absolute top-full left-0 mt-2 w-96 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                        {/* Local Execution History */}
                        {codeHistory.length > 0 && (
                          <>
                            <div className="p-2 border-b border-slate-700">
                              <div className="text-xs text-slate-400 font-bold px-2">执行记录 (本地)</div>
                            </div>
                            <div className="p-2">
                              {codeHistory.map((item, idx) => (
                                <button
                                  key={item.id || idx}
                                  onClick={() => handleSelectHistory(item)}
                                  className="w-full text-left px-3 py-2 rounded hover:bg-slate-700 transition-colors mb-1 last:mb-0 group"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-slate-200 truncate flex-1">
                                      {item.summary || '未命名代码'}
                                    </span>
                                    <span className="text-[10px] text-slate-500 ml-2">
                                      {new Date(item.timestamp).toLocaleTimeString()}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-blue-400 flex justify-between">
                                    <span>{item.code.substring(0, 30)}...</span>
                                    {item.result && (
                                      <span className={item.result.success ? "text-green-400" : "text-red-400"}>
                                        {item.result.success ? "成功" : "失败"}
                                      </span>
                                    )}
                                  </div>
                                </button>
                              ))}
                            </div>
                          </>
                        )}

                        {/* Backend Files History */}
                        {codeHistoryFiles.length > 0 && (
                          <>
                            <div className="p-2 border-b border-slate-700 border-t">
                              <div className="text-xs text-slate-400 font-bold px-2">历史文件 (服务端)</div>
                            </div>
                            <div className="p-2">
                              {codeHistoryFiles.map((file, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => {
                                    handleLoadCodeFromHistory(file.name);
                                    setShowHistoryDropdown(false);
                                  }}
                                  className="w-full text-left px-3 py-2 rounded hover:bg-slate-700 transition-colors mb-1 last:mb-0 group"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-slate-200 truncate flex-1">
                                      {file.name}
                                    </span>
                                    <span className="text-[10px] text-slate-500 ml-2">{file.size}</span>
                                  </div>
                                  <div className="text-[10px] text-blue-400">
                                    💻 点击加载此文件
                                  </div>
                                </button>
                              ))}
                            </div>
                          </>
                        )}
                        
                        <div className="p-2 border-t border-slate-700">
                          <button
                            onClick={() => setShowHistoryDropdown(false)}
                            className="w-full px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-bold rounded transition-colors"
                          >
                            关闭
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setIsEditingEda(!isEditingEda)}
                    className={`px-3 py-1 rounded text-xs font-bold ${
                      isEditingEda ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {isEditingEda ? '保存' : '编辑'}
                  </button>
                  <button
                    onClick={handleRequestAIDebug}
                    disabled={isExecuting || !edaCode.trim()}
                    className="bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800 disabled:opacity-50 text-white px-3 py-1 rounded text-xs font-bold flex items-center gap-2"
                  >
                    <Bot size={12} />
                    AI Debug
                  </button>
                  <button
                    onClick={handleExecuteCode}
                    disabled={isExecuting}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1 rounded text-xs font-bold flex items-center gap-2"
                  >
                    {isExecuting ? '执行中...' : '▶ 运行'}
                  </button>
                </div>
              </div>
              <textarea
                value={edaCode}
                readOnly={!isEditingEda}
                onChange={e => setEdaCode(e.target.value)}
                className={`flex-1 w-full bg-[#1e293b] text-emerald-400 p-6 font-mono text-sm outline-none resize-none ${
                  !isEditingEda ? 'opacity-70' : ''
                }`}
                placeholder="# 在此输入 Python 代码进行数据探索和分析..."
              />
            </div>

            {/* Output */}
            <div className="h-1/2 flex flex-col bg-[#020617] overflow-hidden">
              <div className="px-6 py-2 bg-black/40 text-xs text-slate-500 font-mono font-bold">
                输出结果
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {edaResult ? (
                  <div className="space-y-4">
                    {edaResult.stdout && (
                      <pre className="text-slate-300 font-mono text-xs whitespace-pre-wrap bg-white/5 p-4 rounded-lg">
                        {edaResult.stdout}
                      </pre>
                    )}
                    {edaResult.stderr && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between bg-red-900/20 px-4 py-2 rounded-t-lg border border-red-900/30">
                          <span className="text-red-400 text-xs font-bold flex items-center gap-2">
                            <AlertCircle size={14} />
                            执行出错
                          </span>
                          <button
                            onClick={handleRequestAIFix}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors flex items-center gap-1"
                          >
                            <Bot size={12} />
                            请求AI修复
                          </button>
                        </div>
                        <pre className="text-red-400 font-mono text-xs whitespace-pre-wrap bg-red-900/10 p-4 rounded-b-lg border-t-0 border border-red-900/30">
                          {edaResult.stderr}
                        </pre>
                      </div>
                    )}
                    {edaResult.images?.length > 0 && (
                      <div className="space-y-4">
                        {edaResult.images.map((img: any, i) => {
                          const imgUrl = typeof img === 'string' ? img : img.url;
                          const description = typeof img === 'string' ? 'No description available' : (img.description || 'No description available');
                          return (
                            <div key={i} className="space-y-2">
                              <img
                                src={`${API_URL}${imgUrl}`}
                                className="w-full h-auto rounded-lg border border-slate-700"
                                alt={`Plot ${i + 1}`}
                              />
                              {description && description !== 'No description available' && (
                                <div className="bg-slate-800/50 px-4 py-2 rounded-lg">
                                  <p className="text-xs text-slate-400">{description}</p>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-600 text-xs">
                    等待代码执行...
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

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: any; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`
        px-6 text-xs font-bold flex items-center gap-2 border-b-2 transition-colors
        ${active
          ? 'border-blue-600 text-blue-600 bg-white'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
      `}
    >
      {icon}
      {label}
    </button>
  );
}

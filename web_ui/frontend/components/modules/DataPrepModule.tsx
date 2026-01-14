"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Code2, RefreshCw, AlertCircle, Bot, CheckCircle2, History, ChevronDown } from 'lucide-react';
import { CHAT_SUGGESTIONS } from '@/config/modules';
import ModularChatPanel from '../ModularChatPanel';
import { API_URL } from '@/config/api';

interface DataPrepModuleProps {
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

export default function DataPrepModule({ taskId, subtask }: DataPrepModuleProps) {
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [prepStatus, setPrepStatus] = useState<'idle' | 'preparing' | 'done'>('idle');

  // Code history state
  const [codeHistory, setCodeHistory] = useState<CodeHistoryItem[]>(() => {
    if (typeof window !== 'undefined') {
      try {
        const storageKey = `chat_${taskId}_prep_code_history`;
        const saved = localStorage.getItem(storageKey);
        return saved ? JSON.parse(saved) : [];
      } catch (e) {
        return [];
      }
    }
    return [];
  });
  const [showHistoryDropdown, setShowHistoryDropdown] = useState(false);

  // Content states with localStorage persistence
  const [prepCode, setPrepCodeState] = useState(() => {
    if (typeof window !== 'undefined') {
      const storageKey = `chat_${taskId}_prep_generated_code`;
      const saved = localStorage.getItem(storageKey);
      return saved || '';
    }
    return '';
  });

  // Wrapper to save to localStorage
  const setPrepCode = (code: string | ((prev: string) => string)) => {
    setPrepCodeState(prev => {
      const newCode = typeof code === 'function' ? code(prev) : code;
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_prep_generated_code`;
        localStorage.setItem(storageKey, newCode);
      }
      return newCode;
    });
  };

  const [isEditingPrep, setIsEditingPrep] = useState(false);
  const [prepResult, setPrepResult] = useState<{stdout: string, stderr: string, images: string[], success: boolean} | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const storageKey = `chat_${taskId}_prep_execution_result`;
        const saved = localStorage.getItem(storageKey);
        return saved ? JSON.parse(saved) : null;
      } catch (e) {
        return null;
      }
    }
    return null;
  });
  const [isExecuting, setIsExecutingState] = useState(() => {
    if (typeof window !== 'undefined') {
      const storageKey = `chat_${taskId}_prep_is_executing`;
      const saved = localStorage.getItem(storageKey);
      return saved === 'true';
    }
    return false;
  });

  // 包装 setIsExecuting 以同时保存到 localStorage
  const setIsExecuting = (value: boolean | ((prev: boolean) => boolean)) => {
    setIsExecutingState(prev => {
      const newValue = typeof value === 'function' ? value(prev) : value;
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_prep_is_executing`;
        localStorage.setItem(storageKey, String(newValue));
      }
      return newValue;
    });
  };

  const [pendingFixMessage, setPendingFixMessage] = useState<string>("");

  // 监听 localStorage 变化（当对话标签页生成代码并执行后）
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const resultKey = `chat_${taskId}_prep_execution_result`;
    const codeKey = `chat_${taskId}_prep_generated_code`;
    const historyKey = `chat_${taskId}_prep_code_history`;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === resultKey && e.newValue) {
        try {
          const newResult = JSON.parse(e.newValue);
          console.log('🔄 Prep execution result updated from chat:', newResult);
          setPrepResult(newResult);
        } catch (e) {
          console.error('Failed to parse prep execution result:', e);
        }
      } else if (e.key === codeKey && e.newValue) {
        console.log('🔄 Prep code updated from chat:', e.newValue.substring(0, 100));
        setPrepCode(e.newValue);
      } else if (e.key === historyKey && e.newValue) {
        try {
          const newHistory = JSON.parse(e.newValue);
          console.log('🔄 Prep code history updated from chat:', newHistory.length, 'items');
          setCodeHistory(newHistory);
        } catch (e) {
          console.error('Failed to parse prep code history:', e);
        }
      }
    };

    // Listen for storage events (cross-tab)
    window.addEventListener('storage', handleStorageChange);

    // Also poll for same-tab changes
    const interval = setInterval(() => {
      const currentResult = localStorage.getItem(resultKey);
      const currentCode = localStorage.getItem(codeKey);
      const currentHistory = localStorage.getItem(historyKey);

      // Check if result changed
      if (currentResult) {
        try {
          const parsed = JSON.parse(currentResult);
          // Compare with current state to avoid unnecessary updates
          if (JSON.stringify(parsed) !== JSON.stringify(prepResult)) {
            console.log('🔄 Polling detected prep execution result change');
            setPrepResult(parsed);
          }
        } catch (e) {
          // Ignore parse errors
        }
      }

      // Check if code changed
      if (currentCode && currentCode !== prepCode) {
        console.log('🔄 Polling detected prep code change');
        setPrepCode(currentCode);
      }

      // Check if history changed
      if (currentHistory) {
        try {
          const parsed = JSON.parse(currentHistory);
          if (parsed.length !== codeHistory.length) {
            console.log('🔄 Polling detected prep code history change:', parsed.length, 'items');
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
  }, [taskId, prepResult, prepCode, codeHistory.length]);

  const handleExecuteCode = async () => {
    if (!prepCode.trim()) return;
    setIsExecuting(true);
    try {
      const formData = new FormData();
      formData.append("code", prepCode);
      formData.append("view", "data"); // Data prep always uses raw data
      const res = await axios.post(`${API_URL}/tasks/${taskId}/eda/execute`, formData);
      setPrepResult(res.data);

      // Save to localStorage
      if (typeof window !== 'undefined') {
        const storageKey = `chat_${taskId}_prep_execution_result`;
        localStorage.setItem(storageKey, JSON.stringify(res.data));
      }

      // Save to code history with summary
      const summary = generateCodeSummary(prepCode);
      const historyItem: CodeHistoryItem = {
        id: Date.now().toString(),
        code: prepCode,
        summary,
        timestamp: Date.now(),
        result: {
          success: res.data.success || false,
          images: res.data.images?.length || 0
        }
      };

      setCodeHistory(prev => {
        const newHistory = [historyItem, ...prev].slice(0, 20); // Keep only last 20 items
        if (typeof window !== 'undefined') {
          const historyStorageKey = `chat_${taskId}_prep_code_history`;
          localStorage.setItem(historyStorageKey, JSON.stringify(newHistory));
        }
        return newHistory;
      });

      // Check if preparation was successful (has manifest.json)
      if (res.data.success && res.data.stdout.includes('manifest.json')) {
        setPrepStatus('done');
      }

      // Auto-refresh workspace files to show new code files
      // Note: DataPrepModule doesn't have workspace files, but this ensures consistency
      console.log('✅ Data prep code executed and saved');
    } catch (e) {
      alert("执行失败");
    } finally {
      setIsExecuting(false);
    }
  };

  // Generate a summary for the code
  const generateCodeSummary = (code: string): string => {
    const lowerCode = code.toLowerCase();

    if (lowerCode.includes('fillna') || lowerCode.includes('dropna') || lowerCode.includes('drop_duplicates')) {
      return '🧹 缺失值处理';
    }
    if (lowerCode.includes('merge') || lowerCode.includes('concat')) {
      return '🔗 数据合并';
    }
    if (lowerCode.includes('groupby') || lowerCode.includes('pivot')) {
      return '📋 数据聚合';
    }
    if (lowerCode.includes('to_datetime') || lowerCode.includes('astype')) {
      return '🔄 类型转换';
    }
    if (lowerCode.includes('.str.') || lowerCode.includes('replace') || lowerCode.includes('strip')) {
      return '✏️ 文本清洗';
    }
    if (lowerCode.includes('rename') || lowerCode.includes('set_index')) {
      return '🏷️ 列名调整';
    }
    if (lowerCode.includes('query') || lowerCode.includes('.loc[') || lowerCode.includes('.iloc[')) {
      return '🔍 数据筛选';
    }
    if (lowerCode.includes('sort_values') || lowerCode.includes('sort_index')) {
      return '📊 数据排序';
    }

    return '💻 数据准备';
  };

  const handleSelectHistory = (item: CodeHistoryItem) => {
    setPrepCode(item.code);
    setShowHistoryDropdown(false);
  };

  const handleRequestAIFix = () => {
    if (!prepResult?.stderr) return;

    const fixMessage = `我的数据准备代码执行出错了，请帮我修复：

\`\`\`python
${prepCode}
\`\`\`

错误信息：
\`\`\`
${prepResult.stderr}
\`\`\`

请分析错误原因并提供修复后的完整代码。`;

    setPendingFixMessage(fixMessage);
    setActiveTab('chat');
  };

  const handleRequestAIDebug = () => {
    if (!prepCode.trim()) return;

    let debugMessage: string;

    if (prepResult?.stderr) {
      // 有错误信息，请求修复
      debugMessage = `我的数据准备代码执行出错了，请帮我调试并修复：

\`\`\`python
${prepCode}
\`\`\`

错误信息：
\`\`\`
${prepResult.stderr}
\`\`\`

请分析错误原因并提供修复后的完整代码。`;
    } else {
      // 没有错误，请求代码审查和优化
      debugMessage = `请帮我审查并优化以下数据准备代码：

\`\`\`python
${prepCode}
\`\`\`

请检查：
1. 数据清洗逻辑是否正确
2. 数据转换是否符合标准格式（train.csv, test.csv, test_answer.csv）
3. 是否有潜在的性能问题
4. 是否需要添加错误处理

如果代码没有问题，请告诉我代码是正确的。如果有改进建议，请提供优化后的代码。`;
    }

    setPendingFixMessage(debugMessage);
    setActiveTab('chat');
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Header Info */}
      <div className="h-auto border-b flex items-center px-6 py-4 bg-blue-50 shrink-0">
        <div className="flex-1">
          <h3 className="text-sm font-bold text-blue-900 mb-1">
            📊 数据准备模式
          </h3>
          <p className="text-xs text-blue-700">
            使用对话方式生成数据清洗和转换方案，然后自动执行
          </p>
        </div>
        {prepStatus === 'done' && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-bold">
            <CheckCircle2 size={16} />
            准备完成
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="h-12 border-b flex bg-gray-50 shrink-0">
        <TabButton
          active={activeTab === 'chat'}
          onClick={() => setActiveTab('chat')}
          icon={<MessageSquare size={16} />}
          label="对话准备"
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
            {(isExecuting || prepResult) && (
              <div className={`border-b px-3 py-1.5 shrink-0 flex items-center justify-between gap-2 ${
                isExecuting
                  ? 'bg-blue-50 border-blue-200'
                  : prepResult?.success
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center gap-2">
                  {isExecuting ? (
                    <>
                      <RefreshCw size={12} className="text-blue-600 animate-spin" />
                      <span className="text-xs text-blue-800 font-medium">准备中...</span>
                    </>
                  ) : prepResult ? (
                    <>
                      {prepResult.success ? (
                        <CheckCircle2 size={12} className="text-green-600" />
                      ) : (
                        <AlertCircle size={12} className="text-red-600" />
                      )}
                      <span className={`text-xs font-medium ${
                        prepResult.success ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {prepResult.success
                          ? (prepStatus === 'done'
                              ? '✅ 完成'
                              : '✅ 成功')
                          : '❌ 失败'}
                      </span>
                    </>
                  ) : null}
                </div>
                <div className="flex items-center gap-1.5">
                  {!isExecuting && prepResult?.success && prepStatus === 'done' && (
                    <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                      ✨ 完成
                    </span>
                  )}
                  {!isExecuting && prepResult && !prepResult.success && (
                    <button
                      onClick={handleRequestAIFix}
                      className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-medium rounded transition-colors flex items-center gap-1"
                    >
                      <Bot size={10} />
                      修复
                    </button>
                  )}
                  {!isExecuting && prepResult && (
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
                mode="prepare"
                dataSource="raw"
                suggestions={CHAT_SUGGESTIONS.prepare}
                initialMessage={pendingFixMessage}
                disabled={isExecuting}
                onCodeGenerated={(code, isDebugResult = false) => {
                  setPrepCode(code);
                  // Don't auto-switch tabs - let user stay in chat to see the response
                  // User can manually switch to code tab if needed
                  // if (!isDebugResult) {
                  //   setActiveTab('code');
                  // }
                  setPendingFixMessage(""); // Clear pending fix message
                }}
                onPrepComplete={() => setPrepStatus('done')}
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
                  <span className="text-xs text-blue-400 font-mono font-bold">PYTHON 代码 - 数据准备</span>

                  {/* History Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                      className={`px-2 py-1 text-xs font-bold rounded flex items-center gap-1 transition-colors ${
                        codeHistory.length > 0
                          ? 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                          : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-60'
                      }`}
                      title={codeHistory.length > 0 ? "历史代码" : "暂无历史记录"}
                      disabled={codeHistory.length === 0}
                    >
                      <History size={12} />
                      历史 {codeHistory.length > 0 && `(${codeHistory.length})`}
                      {codeHistory.length > 0 && (
                        <ChevronDown size={12} className={`transition-transform ${showHistoryDropdown ? 'rotate-180' : ''}`} />
                      )}
                    </button>

                    {showHistoryDropdown && codeHistory.length > 0 && (
                      <div className="absolute top-full left-0 mt-2 w-80 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                        <div className="p-2 border-b border-slate-700">
                          <div className="text-xs text-slate-400 font-bold px-2">代码执行历史</div>
                        </div>
                        <div className="p-2">
                          {codeHistory.map((item, idx) => (
                            <button
                              key={item.id}
                              onClick={() => handleSelectHistory(item)}
                              className="w-full text-left px-3 py-2 rounded hover:bg-slate-700 transition-colors mb-1 last:mb-0 group"
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-bold text-slate-200">{item.summary}</span>
                                <div className="flex items-center gap-1">
                                  {item.result?.success ? (
                                    <CheckCircle2 size={10} className="text-green-500" />
                                  ) : (
                                    <AlertCircle size={10} className="text-red-500" />
                                  )}
                                  {item.result?.images && item.result.images > 0 && (
                                    <span className="text-[10px] bg-blue-600 text-white px-1.5 py-0.5 rounded">
                                      📊 {item.result.images}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="text-[10px] text-slate-500 font-mono truncate">
                                {new Date(item.timestamp).toLocaleString('zh-CN', {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </div>
                              <div className="text-[10px] text-slate-600 font-mono truncate mt-1 group-hover:text-slate-400">
                                {item.code.split('\n')[0].substring(0, 50)}...
                              </div>
                            </button>
                          ))}
                        </div>
                        <div className="p-2 border-t border-slate-700">
                          <button
                            onClick={() => {
                              setCodeHistory([]);
                              if (typeof window !== 'undefined') {
                                localStorage.removeItem(`chat_${taskId}_prep_code_history`);
                              }
                              setShowHistoryDropdown(false);
                            }}
                            className="w-full px-3 py-1.5 bg-red-900/30 hover:bg-red-900/50 text-red-400 text-xs font-bold rounded transition-colors"
                          >
                            清除历史
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setIsEditingPrep(!isEditingPrep)}
                    className={`px-3 py-1 rounded text-xs font-bold ${
                      isEditingPrep ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {isEditingPrep ? '保存' : '编辑'}
                  </button>
                  <button
                    onClick={handleRequestAIDebug}
                    disabled={isExecuting || !prepCode.trim()}
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
                value={prepCode}
                readOnly={!isEditingPrep}
                onChange={e => setPrepCode(e.target.value)}
                className={`flex-1 w-full bg-[#1e293b] text-emerald-400 p-6 font-mono text-sm outline-none resize-none ${
                  !isEditingPrep ? 'opacity-70' : ''
                }`}
                placeholder="# 在此输入 Python 代码进行数据准备和转换..."
              />
            </div>

            {/* Output */}
            <div className="h-1/2 flex flex-col bg-[#020617] overflow-hidden">
              <div className="px-6 py-2 bg-black/40 text-xs text-slate-500 font-mono font-bold">
                输出结果
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {prepResult ? (
                  <div className="space-y-4">
                    {prepResult.stdout && (
                      <pre className="text-slate-300 font-mono text-xs whitespace-pre-wrap bg-white/5 p-4 rounded-lg">
                        {prepResult.stdout}
                      </pre>
                    )}
                    {prepResult.stderr && (
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
                          {prepResult.stderr}
                        </pre>
                      </div>
                    )}
                    {prepResult.success && prepStatus === 'done' && (
                      <div className="bg-green-900/20 px-4 py-3 rounded-lg border border-green-900/30">
                        <p className="text-green-400 text-xs font-bold flex items-center gap-2">
                          <CheckCircle2 size={14} />
                          数据准备完成！已生成标准的 train.csv, test.csv, test_answer.csv 文件。
                        </p>
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

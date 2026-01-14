"use client";

import { useState, useEffect, useRef, useLayoutEffect } from "react";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, RefreshCw, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ChatSuggestion } from '@/types/modules';
import { API_URL } from '@/config/api';

interface ModularChatPanelProps {
  taskId: string;
  mode: 'prepare' | 'explore' | 'model' | 'report';
  dataSource: 'raw' | 'processed';
  suggestions?: ChatSuggestion[];
  onCodeGenerated?: (code: string, isDebugResult?: boolean) => void;
  onReportUpdate?: (content: string) => void;
  onPrepComplete?: () => void;
  initialMessage?: string;
  disabled?: boolean;
  assistantMode?: 'qa' | 'refine_problem' | 'refine_rubric' | 'improve_code';
  onDescriptionUpdate?: (content: string) => void;
  onRubricUpdate?: (content: string) => void;
  onModelCodeUpdate?: (code: string, path: string) => void;
  subtask?: string;
  reportScope?: 'single' | 'global';
  customPrompt?: string;
}

// 进度步骤配置
const PROGRESS_STEPS = {
  explore: [
    { key: 'thinking', label: '思考中', icon: '🤔' },
    { key: 'analyzing', label: '分析数据', icon: '📊' },
    { key: 'generating', label: '生成代码', icon: '💻' },
    { key: 'executing', label: '执行代码', icon: '⚡' }
  ],
  prepare: [
    { key: 'thinking', label: '思考中', icon: '🤔' },
    { key: 'planning', label: '制定方案', icon: '📋' },
    { key: 'generating', label: '生成代码', icon: '💻' },
    { key: 'executing', label: '执行处理', icon: '⚡' }
  ],
  report: [
    { key: 'thinking', label: '思考中', icon: '🤔' },
    { key: 'analyzing', label: '分析结果', icon: '🔬' },
    { key: 'generating', label: '生成报告', icon: '📝' }
  ],
  model: [
    { key: 'thinking', label: '思考中', icon: '🤔' },
    { key: 'configuring', label: '配置参数', icon: '⚙️' }
  ]
};

export default function ModularChatPanel({
  taskId,
  mode,
  dataSource,
  suggestions = [],
  onCodeGenerated,
  onReportUpdate,
  onPrepComplete,
  initialMessage,
  disabled = false,
  assistantMode = 'qa',
  onDescriptionUpdate,
  onRubricUpdate,
  onModelCodeUpdate,
  subtask,
  reportScope,
  customPrompt
}: ModularChatPanelProps) {
  // 每个mode使用独立的storage key，避免不同模块的状态互相覆盖
  const getStorageKey = (suffix = '') => `chat_${taskId}_${mode}${suffix}`;

  // 初始化时从localStorage恢复聊天历史
  const getInitialChatHistory = (): {role: string, content: string}[] => {
    if (typeof window !== 'undefined') {
      const historyKey = `chat_${taskId}_${mode}_history`;
      const saved = localStorage.getItem(historyKey);

      // 🔥 强制诊断：打印所有相关的localStorage keys
      const allKeys = Object.keys(localStorage).filter(k => k.startsWith('chat_'));
      console.log('🔍 [getInitialChatHistory] 强制诊断:', {
        historyKey,
        taskId,
        mode,
        saved: !!saved,
        savedContent: saved ? saved.substring(0, 200) : null,
        historyLength: saved ? JSON.parse(saved).length : 0,
        allChatKeys: allKeys,
        allKeysForTask: allKeys.filter(k => k.includes(taskId))
      });

      return saved ? JSON.parse(saved) : [];
    }
    return [];
  };

  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>(getInitialChatHistory);
  const [chatInput, setChatInput] = useState("");

  // -------------------------------------------------------------------------
  // 状态管理重构：直接从 localStorage 初始化，并使用 useEffect 自动保存
  // -------------------------------------------------------------------------

  // 1. 发送状态
  const [isChatSending, setIsChatSending] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(getStorageKey('_sending'));
      return saved === 'true';
    }
    return false;
  });

  // 2. 状态文本
  const [chatStatus, setChatStatus] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(getStorageKey('_status')) || '';
    }
    return '';
  });

  // 3. 当前步骤索引
  const [currentStep, setCurrentStep] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(getStorageKey('_step'));
      return saved ? parseInt(saved, 10) : 0;
    }
    return 0;
  });

  // 4. 已完成步骤 (Set)
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(getStorageKey('_completed'));
      return saved ? new Set(JSON.parse(saved)) : new Set();
    }
    return new Set();
  });

  // -------------------------------------------------------------------------
  // 自动持久化 Effects
  // -------------------------------------------------------------------------

  // 保存 isChatSending
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const key = getStorageKey('_sending');
      localStorage.setItem(key, String(isChatSending));
      console.log('💾 [Auto-Save] isChatSending:', isChatSending);
    }
  }, [isChatSending, mode, taskId]);

  // 保存 chatStatus
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const key = getStorageKey('_status');
      localStorage.setItem(key, chatStatus);
    }
  }, [chatStatus, mode, taskId]);

  // 保存 currentStep
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const key = getStorageKey('_step');
      localStorage.setItem(key, String(currentStep));
    }
  }, [currentStep, mode, taskId]);

  // 保存 completedSteps
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const key = getStorageKey('_completed');
      localStorage.setItem(key, JSON.stringify(Array.from(completedSteps)));
    }
  }, [completedSteps, mode, taskId]);

  // -------------------------------------------------------------------------
  // 辅助 Refs 和 Effects
  // -------------------------------------------------------------------------

  const chatEndRef = useRef<HTMLDivElement>(null);
  const isMounted = useRef(true);
  const initializedRef = useRef(false);

  // 计算实际是否应该禁用
  const isActuallyDisabled = isChatSending || disabled;

  // 组件卸载时标记
  useEffect(() => {
    isMounted.current = true;
    initializedRef.current = false;
    return () => {
      isMounted.current = false;
      console.log('🔌 [ModularChatPanel] 组件卸载');
    };
  }, []);

  // 💾 直接保存到localStorage的函数（不依赖setChatHistory）
  const saveToLocalStorage = (newHistory: {role: string, content: string}[]) => {
    if (typeof window !== 'undefined') {
      const key = getStorageKey('_history');
      localStorage.setItem(key, JSON.stringify(newHistory));
    }
  };

  // 📊 诊断：在组件挂载时打印状态
  useEffect(() => {
    console.log('🔍 [ModularChatPanel] 组件挂载状态检查:', {
      mode,
      taskId,
      isChatSending,
      chatStatus,
      currentStep,
      completedSteps: Array.from(completedSteps)
    });
  }, []);

  // 保存聊天历史到 localStorage（实时同步） - 这里的逻辑保持不变，作为双重保险
  useEffect(() => {
    if (typeof window !== 'undefined' && chatHistory.length > 0) {
      const key = getStorageKey('_history');
      const current = localStorage.getItem(key);
      const currentJson = current ? JSON.stringify(chatHistory) : null;
      if (current !== currentJson) {
        localStorage.setItem(key, JSON.stringify(chatHistory));
      }
    }
  }, [chatHistory, taskId, mode]);

  // 🔥 移除cleanup useEffect，不再在组件卸载时清除状态
  // 状态清除由后端状态检查机制负责（避免僵尸进度条）

  // 处理初始消息（从代码执行错误传过来的）
  useEffect(() => {
    if (initialMessage && initialMessage.trim()) {
      setChatInput(initialMessage);
    }
  }, [initialMessage]);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, isChatSending, chatStatus]);

  // Debug: Monitor chatHistory changes
  useEffect(() => {
    console.log('🔄 chatHistory changed:', {
      length: chatHistory.length,
      messages: chatHistory.map((msg, i) => ({
        index: i,
        role: msg.role,
        contentLength: msg.content?.length || 0,
        contentPreview: msg.content?.substring(0, 100) || '(empty)'
      }))
    });
  }, [chatHistory]);

  // 根据状态更新进度步骤
  useEffect(() => {
    if (!isChatSending) {
      setCurrentStep(0);
      setCompletedSteps(new Set());
      return;
    }

    const steps = PROGRESS_STEPS[mode] || [];
    const stepIndex = steps.findIndex(s => chatStatus.toLowerCase().includes(s.key));

    if (stepIndex !== -1) {
      // 标记之前的步骤为完成
      const newCompleted = new Set<number>();
      for (let i = 0; i < stepIndex; i++) {
        newCompleted.add(i);
      }
      setCompletedSteps(newCompleted);
      setCurrentStep(stepIndex);
    }
  }, [chatStatus, isChatSending, mode]);

  // 💾 初始化欢迎消息 - 绝对安全版本
  // 规则：只在真正首次（localStorage无历史且从未初始化）时设置
  useEffect(() => {
    // 已经初始化过，跳过
    if (initializedRef.current) {
      console.log(`⏭️ [ModularChatPanel] ${mode} 已初始化过，跳过`);
      return;
    }

    // 如果localStorage中有历史记录，说明已经初始化过，什么都不做
    const historyKey = getStorageKey('_history');
    const savedHistory = localStorage.getItem(historyKey);
    const hasHistory = savedHistory !== null;

    console.log('🔍 [初始化useEffect] 检查:', {
      mode,
      taskId,
      historyKey,
      hasHistory,
      historyLength: chatHistory.length,
      initialized: initializedRef.current
    });

    if (hasHistory) {
      console.log(`✅ [ModularChatPanel] ${mode} localStorage有历史记录，跳过初始化，保持已恢复的${chatHistory.length}条对话`);
      initializedRef.current = true;
      return;
    }

    // 没有历史记录，设置欢迎消息
    console.warn(`⚠️ [ModularChatPanel] ${mode} 没有历史记录，设置欢迎消息（这会覆盖当前${chatHistory.length}条对话）`);
    const modeMessages = {
      prepare: [{ role: "assistant" as const, content: "👋 欢迎使用数据准备模式！\n\n告诉我关于你的数据，我会帮你生成清洗和转换方案。" }],
      explore: [{ role: "assistant" as const, content: "🔍 数据探索模式已激活！\n\n你可以：\n- 询问数据统计信息\n- 请求可视化图表\n- 生成分析代码" }],
      model: [{ role: "assistant" as const, content: "🤖 模型训练助手已就绪！\n\n我可以帮你：\n- 推荐工作流\n- 配置训练参数\n- 解答训练问题" }],
      report: [{ role: "assistant" as const, content: "📝 报告生成助手已启动！\n\n告诉我你想要什么样的报告，我会基于所有分析结果生成文档。" }]
    };
    const welcomeMsg = modeMessages[mode];

    // 直接设置，不使用setTimeout
    setChatHistory(welcomeMsg);
    initializedRef.current = true;

    // 立即保存到localStorage
    localStorage.setItem(historyKey, JSON.stringify(welcomeMsg));
    console.log(`🎉 [ModularChatPanel] ${mode} 欢迎消息已设置并保存`);
  }, [mode, taskId]);  // 只依赖mode和taskId

  // 🔥 轮询检查localStorage更新（用于检测后台处理完成的消息）
  useEffect(() => {
    const historyKey = getStorageKey('_history');

    // 每500ms检查一次localStorage是否有更新
    const interval = setInterval(() => {
      const savedHistory = localStorage.getItem(historyKey);
      if (!savedHistory) return;

      try {
        const parsedHistory = JSON.parse(savedHistory);

        // 如果localStorage中的历史比当前state长，说明有新消息
        if (parsedHistory.length > chatHistory.length) {
          console.log('🔄 [轮询] 检测到localStorage有新消息，更新UI:', {
            localStorageLength: parsedHistory.length,
            stateLength: chatHistory.length,
            newMessages: parsedHistory.length - chatHistory.length
          });

          setChatHistory(parsedHistory);
        }
      } catch (e) {
        console.error('轮询检查失败:', e);
      }
    }, 500);  // 500ms检查一次

    return () => clearInterval(interval);
  }, [chatHistory.length, taskId, mode]);  // 依赖chatHistory.length来检测变化

  // 🔥 后端状态检查：避免"僵尸"进度条
  // 当从localStorage恢复执行状态后，检查后端实际状态
  useEffect(() => {
    // 只在恢复执行状态时检查一次
    if (!isChatSending) return;

    const checkBackendStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/tasks/${taskId}/chat_status`);
        const backendStatus = response.data.status;

        console.log('🔍 [后端状态检查]:', {
          frontendStatus: chatStatus,
          backendStatus,
          isChatSending
        });

        // 如果后端已经空闲，说明前端状态过期，清除执行状态
        if (backendStatus === 'idle' || backendStatus === '') {
          console.log('✅ [后端状态检查] 后端已空闲，清除前端执行状态');
          setIsChatSending(false);
          setChatStatus('');
          setCurrentStep(0);
          setCompletedSteps(new Set());
        }
      } catch (e) {
        console.error('❌ [后端状态检查] 失败:', e);
      }
    };

    // 立即检查一次
    checkBackendStatus();

    // 然后每2秒检查一次，直到状态清除
    const interval = setInterval(checkBackendStatus, 2000);

    return () => clearInterval(interval);
  }, [isChatSending]);  // 只在isChatSending变化时执行

  const handleClearHistory = async () => {
    // 清除前端 localStorage
    const historyKey = getStorageKey('_history');
    localStorage.removeItem(historyKey);
    localStorage.removeItem(getStorageKey('_summary'));
    localStorage.removeItem(getStorageKey('_sending'));
    localStorage.removeItem(getStorageKey('_status'));
    localStorage.removeItem(getStorageKey('_step'));
    localStorage.removeItem(getStorageKey('_completed'));

    // 重置状态为欢迎消息
    const modeMessages = {
      prepare: [{ role: "assistant" as const, content: "👋 欢迎使用数据准备模式！\n\n告诉我关于你的数据，我会帮你生成清洗和转换方案。" }],
      explore: [{ role: "assistant" as const, content: "🔍 数据探索模式已激活！\n\n你可以：\n- 询问数据统计信息\n- 请求可视化图表\n- 生成分析代码" }],
      model: [{ role: "assistant" as const, content: "🤖 模型训练助手已就绪！\n\n我可以帮你：\n- 推荐工作流\n- 配置训练参数\n- 解答训练问题" }],
      report: [{ role: "assistant" as const, content: "📝 报告生成助手已启动！\n\n告诉我你想要什么样的报告，我会基于所有分析结果生成文档。" }]
    };
    const welcomeMsg = modeMessages[mode];
    setChatHistory(welcomeMsg);

    // 立即保存欢迎消息到localStorage
    localStorage.setItem(historyKey, JSON.stringify(welcomeMsg));
    console.log('🧹 [ModularChatPanel] 对话历史已清除，重置为欢迎消息');

    setIsChatSending(false);

    // 清除后端的对话总结
    try {
      await axios.post(`${API_URL}/tasks/${taskId}/clear_history`);
    } catch (e) {
      console.error('Failed to clear backend history:', e);
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !taskId || isActuallyDisabled) return;

    const prefix = {
      prepare: "[DATA_PREP_MODE] ",
      explore: "[EDA_MODE] ",
      model: "[CHAT_MODE] ",
      report: "[REPORT_MODE] "
    }[mode];

    const userMsg = { role: "user", content: chatInput };

    // 🔥 关键修复：用户消息也要直接保存到localStorage
    if (typeof window !== 'undefined') {
      const historyKey = getStorageKey('_history');
      const currentHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
      const newHistory = [...currentHistory, userMsg];

      // 🔥 保存前先验证
      console.log('💾 [保存前] localStorage状态:', {
        historyKey,
        getStorageKey: getStorageKey('_history'),
        手动构造key: `chat_${taskId}_${mode}_history`,
        两个key是否一致: getStorageKey('_history') === `chat_${taskId}_${mode}_history`,
        当前localStorage内容: localStorage.getItem(historyKey)?.substring(0, 100)
      });

      localStorage.setItem(historyKey, JSON.stringify(newHistory));

      // 🔥 保存后立即验证
      const saved = localStorage.getItem(historyKey);
      console.log('💾 [保存后] 验证:', {
        historyKey,
        保存成功: saved === JSON.stringify(newHistory),
        保存后长度: saved ? JSON.parse(saved).length : 0,
        prevLength: currentHistory.length,
        newLength: newHistory.length,
        content: chatInput.substring(0, 50)
      });

      // 更新UI
      setChatHistory(newHistory);
    } else {
      setChatHistory(prev => [...prev, userMsg]);
    }

    setChatInput("");
    setIsChatSending(true);

    // Set initial status based on mode and assistant mode
    let initialStatus = "思考中...";
    if (mode === 'model') {
      if (assistantMode === 'qa') initialStatus = "分析问题...";
      else if (assistantMode === 'refine_problem') initialStatus = "改进问题描述...";
      else if (assistantMode === 'refine_rubric') initialStatus = "改进评分标准...";
      else if (assistantMode === 'improve_code') initialStatus = "分析并改进代码...";
    } else if (mode === 'report') {
      initialStatus = "分析数据并生成报告...";
    }
    setChatStatus(initialStatus);

    // Clear loading state if anything goes wrong
    const clearLoadingState = () => {
      console.log('🧹 Clearing loading state...');
      setIsChatSending(false);
      setChatStatus("");
    };

    // Poll status more frequently for better UX
    const statusInterval = setInterval(async () => {
      try {
        const sRes = await axios.get(`${API_URL}/tasks/${taskId}/chat_status`);
        if (sRes.data.status !== "idle") {
          setChatStatus(sRes.data.status);
          console.log('📊 Status updated:', sRes.data.status);
        }
      } catch (e) {
        console.error('Status check failed:', e);
      }
    }, 1000); // Poll every 1 second instead of 2

    try {
      // Map dataSource to backend selected_data_view parameter
      const dataViewParam = dataSource === 'processed' ? 'prepared_data' : 'data';

      // For model mode, include assistant_mode in the message
      let messageContent = userMsg.content;
      if (mode === 'model' && assistantMode) {
        messageContent = `[ASSISTANT_MODE:${assistantMode}] ${userMsg.content}`;
      }

      const payload: any = {
        role: "user",
        content: prefix + messageContent,
        selected_data_view: dataViewParam,
        subtask: subtask,
        report_scope: reportScope,
        custom_prompt: customPrompt
      };

      console.log('📤 Sending chat request...', { taskId, mode, assistantMode, dataSource, dataViewParam });

      const res = await axios.post(`${API_URL}/tasks/${taskId}/chat`, payload, {
        timeout: 1800000, // 30 minutes timeout for long-running EDA/Report tasks
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('✅ Chat request successful, processing response...');

      // Clear loading and interval immediately after receiving response
      setIsChatSending(false);
      clearInterval(statusInterval);
      setChatStatus("");
      console.log('✅ Loading state cleared, processing response data...');

      // Debug: Log the FULL response
      console.log('═══════════════════════════════════════════════════════════');
      console.log('🔍 Backend FULL Response:', JSON.stringify(res.data, null, 2));
      console.log('═══════════════════════════════════════════════════════════');
      console.log('🔍 Content type:', typeof res.data.content);
      console.log('🔍 Content exists?', !!res.data.content);
      console.log('🔍 Content length:', res.data.content?.length || 0);
      console.log('🔍 Content preview:', res.data.content?.substring(0, 500));
      console.log('🔍 updated_content keys:', Object.keys(res.data.updated_content || {}));
      console.log('═══════════════════════════════════════════════════════════');

      // Handle response updates before adding to history
      let assistantMessage = res.data;

      // Try to parse JSON content from backend
      let parsedContent = null;
      if (assistantMessage.content && typeof assistantMessage.content === 'string') {
        try {
          // Remove markdown code blocks if present
          let contentToParse = assistantMessage.content;
          if (contentToParse.startsWith('```json')) {
            contentToParse = contentToParse.replace(/```json\n?/, '').replace(/\n?```$/, '');
          } else if (contentToParse.startsWith('```')) {
            contentToParse = contentToParse.replace(/```\n?/, '').replace(/\n?```$/, '');
          }

          parsedContent = JSON.parse(contentToParse);
        } catch (e) {
          // Content is not JSON, keep as-is
          parsedContent = null;
        }
      }

      // Format parsed JSON content into readable markdown
      if (parsedContent) {
        let formattedContent = '';

        if (parsedContent.analysis_summary) {
          formattedContent += `## 📊 分析摘要\n\n${parsedContent.analysis_summary}\n\n`;
        }

        if (parsedContent.key_insights && parsedContent.key_insights.length > 0) {
          formattedContent += `## 🔍 核心发现\n\n`;
          parsedContent.key_insights.forEach((insight: string, idx: number) => {
            formattedContent += `${idx + 1}. ${insight}\n`;
          });
          formattedContent += `\n`;
        }

        if (parsedContent.visualization_insights) {
          const viz = parsedContent.visualization_insights;
          if (viz.available_visualizations && viz.available_visualizations.length > 0) {
            formattedContent += `## 📈 可视化建议\n\n`;
            viz.available_visualizations.forEach((v: string) => {
              formattedContent += `- ${v}\n`;
            });
            formattedContent += `\n`;
          }
        }

        if (parsedContent.recommendations && parsedContent.recommendations.length > 0) {
          formattedContent += `## 💡 下一步建议\n\n`;
          parsedContent.recommendations.forEach((rec: string, idx: number) => {
            formattedContent += `${idx + 1}. ${rec}\n`;
          });
          formattedContent += `\n`;
        }

        if (parsedContent.next_steps && parsedContent.next_steps.length > 0) {
          formattedContent += `## 🎯 推荐操作\n\n`;
          parsedContent.next_steps.forEach((step: string, idx: number) => {
            formattedContent += `${idx + 1}. ${step}\n`;
          });
        }

        // Update the content with formatted version
        if (formattedContent) {
          assistantMessage.content = formattedContent;
        }
      }

      if (res.data.updated_content?.eda_execution_result) {
        const execResult = res.data.updated_content.eda_execution_result;

        // Debug: Log execution result
        console.log('🔍 Execution result:', {
          success: execResult.success,
          hasStderr: !!execResult.stderr,
          stderrLength: execResult.stderr?.length || 0,
          hasStdout: !!execResult.stdout,
          imagesCount: execResult.images?.length || 0
        });

        // If there are images, add them to the message content with descriptions
        if (execResult.images && execResult.images.length > 0) {
          const imageList = execResult.images.map((img: any, i: number) => {
            const filename = (img.url || img).split('/').pop() || `plot_${i+1}.png`;
            const description = img.description || "No description available";
            const imgUrl = img.url || img;

            return `### 📊 图表 ${i+1}\n\n**${filename}**\n\n${description}\n\n![${filename}](${API_URL}${imgUrl})`;
          }).join('\n\n---\n\n');

          // Append images to existing content instead of replacing
          const visualizationSection = '\n\n---\n\n## 生成的可视化\n\n' + imageList;
          assistantMessage.content = (assistantMessage.content || '') + visualizationSection;
        }

        // Only show error if execution failed AND there's stderr
        if (execResult.stderr && execResult.success === false) {
          if (assistantMessage.content) {
            assistantMessage.content += `\n\n---\n\n### ❌ 执行错误\n\`\`\`\n${execResult.stderr}\n\`\`\``;
          } else {
            assistantMessage.content = `### ❌ 执行错误\n\`\`\`\n${execResult.stderr}\n\`\`\``;
          }
        }
      }

      // Debug: Log before adding to chat history
      console.log('✅ Adding message to chat history:');
      console.log('  - Role:', assistantMessage.role);
      console.log('  - Content length:', assistantMessage.content?.length || 0);
      console.log('  - Content preview:', assistantMessage.content?.substring(0, 300));

      // Safety check: Ensure content exists
      if (!assistantMessage.content || assistantMessage.content.trim() === '') {
        console.warn('⚠️ Empty content detected, using fallback message');
        assistantMessage.content = '✅ 分析已完成，请查看「代码执行」标签查看结果。';
      }

      // Force display content for debugging
      console.log('📢 ABOUT TO ADD MESSAGE TO CHAT:');
      console.log('  Message role:', assistantMessage.role);
      console.log('  Message content length:', assistantMessage.content?.length);
      console.log('  First 200 chars:', assistantMessage.content?.substring(0, 200));

      // 🔥 关键修复：不依赖setChatHistory，直接操作localStorage
      // 这样即使组件已卸载，响应也能保存
      if (typeof window !== 'undefined') {
        const historyKey = getStorageKey('_history');
        const currentHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
        const newHistory = [...currentHistory, assistantMessage];
        localStorage.setItem(historyKey, JSON.stringify(newHistory));

        console.log('💾 [handleSendMessage-AI] 直接保存AI响应到localStorage（不依赖setChatHistory）:', {
          historyKey,
          prevLength: currentHistory.length,
          newLength: newHistory.length,
          isMounted: isMounted.current
        });

        // 只有组件还挂载时才更新state
        if (isMounted.current) {
          setChatHistory(newHistory);
        } else {
          console.warn('⚠️ 组件已卸载，AI响应已保存到localStorage但UI未更新');
        }
      } else if (isMounted.current) {
        // 降级方案：如果window不存在且组件挂载，使用setChatHistory
        setChatHistory(prev => [...prev, assistantMessage]);
      }

      console.log('✅ MESSAGE ADDED TO CHAT HISTORY!');

      // Handle response updates
      if (res.data.updated_content) {
        // 💾 NEW: 保存 chat_summary（如果存在）到 localStorage
        if (res.data.updated_content.chat_summary && typeof window !== 'undefined') {
          localStorage.setItem(getStorageKey('_summary'), res.data.updated_content.chat_summary);
          console.log('✅ Chat summary saved to localStorage');
        }

        // Debug result - auto-update code and notify user
        if (res.data.updated_content.is_debug_result && res.data.updated_content.eda_code && onCodeGenerated) {
          console.log('🔧 Debug result detected - auto-updating code', res.data.updated_content.eda_code.substring(0, 100) + '...');
          // 保存修复后的代码到 localStorage
          if (typeof window !== 'undefined') {
            const storageKey = `chat_${taskId}_${mode}_${dataSource}_generated_code`;
            localStorage.setItem(storageKey, res.data.updated_content.eda_code);
            console.log('✅ Code saved to localStorage:', storageKey);
          }
          // 通知父组件更新代码，传递 isDebugResult=true 防止自动切换tab
          onCodeGenerated(res.data.updated_content.eda_code, true);
          console.log('✅ onCodeGenerated called with isDebugResult=true');
        }
        // Normal code generation (not debug)
        else if (res.data.updated_content.eda_code && onCodeGenerated && !res.data.updated_content.is_debug_result) {
          // 保存生成的代码到 localStorage
          if (typeof window !== 'undefined') {
            const storageKey = `chat_${taskId}_${mode}_${dataSource}_generated_code`;
            localStorage.setItem(storageKey, res.data.updated_content.eda_code);
          }
          // Normal code generation - pass isDebugResult=false to allow auto-tab switch
          onCodeGenerated(res.data.updated_content.eda_code, false);
        }

        // Handle other updates
        if (res.data.updated_content.description && onDescriptionUpdate) {
          onDescriptionUpdate(res.data.updated_content.description);
          console.log('✅ Description updated via callback');
        }
        if (res.data.updated_content.rubric && onRubricUpdate) {
          onRubricUpdate(res.data.updated_content.rubric);
          console.log('✅ Rubric updated via callback');
        }
        if (res.data.updated_content.model_code && onModelCodeUpdate) {
          const codePath = res.data.updated_content.model_code_path || '';
          onModelCodeUpdate(res.data.updated_content.model_code, codePath);
          console.log('✅ Model code updated via callback:', codePath);
        }
        if (res.data.updated_content.report && onReportUpdate) {
          onReportUpdate(res.data.updated_content.report);
        }
        if (res.data.updated_content.eda_report && onReportUpdate) {
          onReportUpdate(res.data.updated_content.eda_report);
        }
        if (res.data.updated_content.eda_execution_result) {
          // 保存执行结果到 localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem(getStorageKey('_execution_result'), JSON.stringify(res.data.updated_content.eda_execution_result));

            // Also add to code history
            if (res.data.updated_content.eda_code) {
              const historyKey = mode === 'prepare'
                ? `chat_${taskId}_prep_code_history`
                : `chat_${taskId}_explore_code_history`;

              try {
                const existingHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
                const execResult = res.data.updated_content.eda_execution_result;

                // Generate a summary based on the code
                const summary = mode === 'prepare'
                  ? '💻 对话生成 - 数据准备'
                  : '📊 对话生成 - 数据分析';

                const historyItem = {
                  id: Date.now().toString(),
                  code: res.data.updated_content.eda_code,
                  summary,
                  timestamp: Date.now(),
                  result: {
                    success: execResult.success || false,
                    images: execResult.images?.length || 0
                  }
                };

                const newHistory = [historyItem, ...existingHistory].slice(0, 20);
                localStorage.setItem(historyKey, JSON.stringify(newHistory));
                console.log('✅ Code history updated:', historyKey);
              } catch (e) {
                console.error('Failed to update code history:', e);
              }
            }
          }
        }
      }
    } catch (e: any) {
      console.error('❌ Chat request error:', e);

      // Determine error type
      let errorMessage = "❌ 错误：无法连接到后端服务";

      if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
        errorMessage = "❌ 请求超时：后端处理时间过长，请稍后查看「代码执行」标签或刷新页面";
      } else if (e.response) {
        // Server responded with error status
        errorMessage = `❌ 服务器错误：${e.response.status} - ${e.response.statusText}`;
      } else if (e.request) {
        // Request was made but no response received
        errorMessage = "❌ 网络错误：未收到服务器响应，请检查网络连接";
      }

      console.error('Error details:', {
        code: e.code,
        message: e.message,
        hasResponse: !!e.response,
        hasRequest: !!e.request
      });

      // 🔥 关键修复：错误消息也要直接保存到localStorage
      if (typeof window !== 'undefined') {
        const historyKey = getStorageKey('_history');
        const currentHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
        const errorMsg = { role: "assistant", content: errorMessage };
        const newHistory = [...currentHistory, errorMsg];
        localStorage.setItem(historyKey, JSON.stringify(newHistory));

        console.log('💾 [handleSendMessage-error] 直接保存错误消息到localStorage（不依赖setChatHistory）:', {
          historyKey,
          prevLength: currentHistory.length,
          newLength: newHistory.length,
          isMounted: isMounted.current,
          error: errorMessage
        });

        // 只有组件还挂载时才更新state
        if (isMounted.current) {
          setChatHistory(newHistory);
        } else {
          console.warn('⚠️ 组件已卸载，错误消息已保存到localStorage但UI未更新');
        }
      } else if (isMounted.current) {
        setChatHistory(prev => [...prev, { role: "assistant", content: errorMessage }]);
      }
    } finally {
      console.log('🧹 Finally block: clearing loading state...');
      setIsChatSending(false);
      clearInterval(statusInterval);
      setChatStatus("");

      // 🔥 不再清除localStorage中的执行状态，保留给切换标签后的组件
      // 清除状态由后端状态检查机制负责（避免僵尸进度条）
      console.log('✅ 执行状态保留在localStorage，供切换标签后恢复');
    }
  };

  const handleSuggestionClick = (suggestion: ChatSuggestion) => {
    setChatInput(suggestion.prompt);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Suggestions - Compact, always show */}
      {suggestions.length > 0 && (
        <div className="px-3 py-2 border-b bg-gray-100/50">
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-2 py-1 bg-white hover:bg-blue-50 text-gray-600 hover:text-blue-700 rounded text-[10px] font-medium transition-colors border border-gray-200"
              >
                {suggestion.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* History Toolbar - Compact */}
        {chatHistory.length > 1 && (
          <div className="flex items-center justify-between mb-2 pb-2">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {chatHistory.length - 1} 条消息
              </span>
              {chatHistory.length > 2 && (
                <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                  历史
                </span>
              )}
            </div>
            <button
              onClick={handleClearHistory}
              disabled={isActuallyDisabled}
              className="text-sm px-2 py-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="清除对话历史"
            >
              清除
            </button>
          </div>
        )}

        {chatHistory.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm shadow-md ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-200'
            }`}>
              {msg.role === 'assistant' && (
                <div className="text-[10px] font-black text-blue-500/50 uppercase tracking-widest mb-2 flex items-center gap-2">
                  <Bot size={12} /> DS Copilot
                  {mode === 'model' && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded font-normal">
                      {assistantMode === 'qa' && '💬 问答'}
                      {assistantMode === 'refine_problem' && '📝 改进定义'}
                      {assistantMode === 'refine_rubric' && '📊 改进标准'}
                      {assistantMode === 'improve_code' && '💻 改进代码'}
                    </span>
                  )}
                </div>
              )}
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {(msg.content || "").replace(/<EDA_CODE>([\s\S]*?)<\/EDA_CODE>/g, "\n```python\n$1\n```\n")}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {isActuallyDisabled && (
          <div className="flex justify-start">
            <div className="bg-white border border-blue-200 px-5 py-4 rounded-xl shadow-md w-full max-w-md">
              {/* 进度条 */}
              <div className="mb-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-blue-600">处理进度</span>
                  <span className="text-[10px] text-gray-400">
                    {completedSteps.size}/{PROGRESS_STEPS[mode]?.length || 0} 步骤完成
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${((completedSteps.size) / (PROGRESS_STEPS[mode]?.length || 1)) * 100}%`
                    }}
                  />
                </div>
              </div>

              {/* 步骤列表 */}
              <div className="space-y-2 mb-3">
                {(PROGRESS_STEPS[mode] || []).map((step, index) => (
                  <div
                    key={step.key}
                    className={`flex items-center gap-2 text-xs transition-all ${
                      index === currentStep
                        ? 'text-blue-600 font-bold'
                        : completedSteps.has(index)
                        ? 'text-green-600'
                        : 'text-gray-400'
                    }`}
                  >
                    {index === currentStep ? (
                      <RefreshCw size={12} className="animate-spin" />
                    ) : completedSteps.has(index) ? (
                      <CheckCircle2 size={12} />
                    ) : (
                      <div className="w-3 h-3 rounded-full border-2 border-gray-300" />
                    )}
                    <span className={completedSteps.has(index) ? 'line-through opacity-60' : ''}>
                      {step.icon} {step.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* 当前状态 */}
              <div className="flex items-center gap-2 text-xs text-gray-600 bg-blue-50 px-3 py-2 rounded-lg">
                <Loader2 size={14} className="animate-spin text-blue-600" />
                <span>{chatStatus || "正在处理..."}</span>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Chat Input */}
      <div className="p-4 bg-white border-t relative">
        {/* 禁用提示 */}
        {isChatSending && (
          <div className="absolute -top-12 left-4 right-4 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-xs text-amber-700 flex items-center gap-2">
            <AlertCircle size={14} />
            <span>正在处理中，请等待完成后再发送新消息...</span>
          </div>
        )}

        <textarea
          value={chatInput}
          disabled={isActuallyDisabled}
          onChange={e => setChatInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          className={`w-full rounded-xl p-3 text-sm outline-none resize-none pr-12 transition-all ${
            isActuallyDisabled
              ? 'bg-gray-100 opacity-50 cursor-not-allowed'
              : 'bg-white border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100'
          }`}
          rows={3}
          placeholder={isActuallyDisabled ? "处理中，请稍候..." : "输入你的问题... (Shift+Enter 换行)"}
        />
        <button
          onClick={handleSendMessage}
          disabled={isActuallyDisabled || !chatInput.trim()}
          className={`absolute right-6 bottom-6 p-2 rounded-lg transition-all ${
            isActuallyDisabled || !chatInput.trim()
              ? 'bg-gray-300 cursor-not-allowed opacity-50'
              : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
          }`}
          title={isActuallyDisabled ? "请等待当前任务完成" : "发送消息"}
        >
          {isActuallyDisabled ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
}

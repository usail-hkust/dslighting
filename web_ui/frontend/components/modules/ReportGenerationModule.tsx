"use client";

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { FileText, Download, Printer, RefreshCw, Globe, FolderOpen, FileEdit, MessageSquare, Save } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkBreaks from 'remark-breaks';
import ModularChatPanel from '../ModularChatPanel';
import { CHAT_SUGGESTIONS } from '@/config/modules';
import { API_URL } from '@/config/api';

interface ReportGenerationModuleProps {
  taskId: string;
  subtask?: string;
}

type ReportScope = 'single' | 'global';
type ReportTemplate = 'general' | 'academic' | 'data_report' | 'math_modeling';

const TEMPLATE_OPTIONS = [
  { value: 'general', label: '通用报告', icon: '📄', description: '通用数据分析报告' },
  { value: 'academic', label: '学术论文', icon: '🎓', description: '学术论文格式报告' },
  { value: 'data_report', label: '数据报告', icon: '📊', description: '专业数据分析报告' },
  { value: 'math_modeling', label: '数学建模', icon: '🧮', description: '数学建模竞赛报告' },
];

export default function ReportGenerationModule({ taskId, subtask }: ReportGenerationModuleProps) {
  const [reportScope, setReportScope] = useState<ReportScope>(subtask ? 'single' : 'global');
  const [reportTemplate, setReportTemplate] = useState<ReportTemplate>('general');
  const [reportContent, setReportContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [tempReport, setTempReport] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Force global scope if no subtask
  useEffect(() => {
    if (!subtask && reportScope === 'single') {
      console.log('⚠️ No subtask found, forcing GLOBAL scope');
      setReportScope('global');
    }
  }, [subtask, reportScope]);

  // Debug: Log when subtask changes
  console.log('📝 ReportGenerationModule render:', { taskId, subtask, reportScope });

  const fetchReport = useCallback(async () => {
    console.log('🔄 Fetching report:', { taskId, subtask, reportScope });
    setIsRefreshing(true);

    try {
      let url = "";

      // Determine which API endpoint to call
      // Force global URL if no subtask is present, regardless of scope state
      if (reportScope === 'global' || !subtask) {
        url = `${API_URL}/tasks/${taskId}/report`;
      } else {
        url = `${API_URL}/tasks/${taskId}/subtasks/${subtask}/report`;
      }

      // Add timestamp to bypass cache
      const timestamp = new Date().getTime();
      const separator = url.includes('?') ? '&' : '?';
      const finalUrl = `${url}${separator}_t=${timestamp}`;

      console.log('📍 Making request to:', finalUrl);
      const res = await axios.get(finalUrl, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'Expires': '0',
        }
      });

      setReportContent(res.data.report || "");
      console.log('✅ Report loaded successfully, length:', res.data.report?.length || 0);
    } catch (e: any) {
      console.error('❌ Failed to fetch report:', e);
      setReportContent("");
    } finally {
      setIsRefreshing(false);
    }
  }, [taskId, subtask, reportScope]);

  useEffect(() => {
    console.log('🎯 useEffect triggered:', { taskId, subtask, reportScope });
    if (taskId) {
      fetchReport();
    }
  }, [fetchReport]);

  const handleSaveReport = async () => {
    try {
      const url = reportScope === 'global' || !subtask
        ? `${API_URL}/tasks/${taskId}/report/update`
        : `${API_URL}/tasks/${taskId}/subtasks/${subtask}/report`;

      await axios.post(url, {
        content: tempReport,
        is_eda: false
      });
      setReportContent(tempReport);
      setIsEditing(false);
      alert("保存成功");
    } catch (e: any) {
      alert("保存失败: " + e.message);
    }
  };


  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await fetchReport();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handlePrint = () => {
    window.print();
  };

  const getTemplatePrompt = () => {
    const template = TEMPLATE_OPTIONS.find(t => t.value === reportTemplate);
    const basePrompt = `Please generate a comprehensive ${template?.label || 'report'} for ${taskId}${subtask && reportScope === 'single' ? ` (subtask: ${subtask})` : ''}.`;

    switch (reportTemplate) {
      case 'academic':
        return `${basePrompt}

Follow academic paper structure:
1. Abstract (200-250 words)
2. Introduction (background, motivation, objectives)
3. Literature Review
4. Methodology (data, methods, techniques)
5. Results and Analysis
6. Discussion
7. Conclusion

Use formal academic language. **NOTE: Do not include a References section as AI-generated citations may be inaccurate.**`;

      case 'data_report':
        return `${basePrompt}

Structure as a professional data report:
1. Executive Summary
2. Business Context
3. Data Overview
4. Key Findings
5. Detailed Analysis
6. Recommendations

Focus on actionable insights and business impact.`;

      case 'math_modeling':
        return `${basePrompt}

Follow mathematical modeling competition format:
1. Problem Analysis
2. Model Assumptions
3. Notation and Variable Definitions
4. Model Formulation
5. Solution Methods
6. Model Results
7. Sensitivity Analysis
8. Strengths and Weaknesses
9. Model Improvements

Include mathematical formulations and clear explanations. **NOTE: Do not include a References section.**`;

      default:
        return `${basePrompt}

Provide a comprehensive analysis including:
1. Overview
2. Data Analysis
3. Key Findings
4. Conclusions
5. Recommendations`;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white">
      {/* Report Configuration Bar - Compact */}
      <div className="border-b bg-blue-50 px-3 py-1.5 shrink-0">
        <div className="flex gap-3 items-center">
          {/* Report Scope */}
          <div className="flex-1">
            <div className="flex gap-2">
              <button
                disabled={!subtask}
                onClick={() => {
                  console.log('🔘 Clicking SINGLE button, current scope:', reportScope, 'new scope will be: single');
                  if (subtask) setReportScope('single');
                }}
                className={`flex-1 px-2 py-1 text-xs font-bold rounded border transition-all flex items-center justify-center gap-1 ${
                  reportScope === 'single'
                    ? 'border-blue-500 bg-blue-500 text-white'
                    : !subtask 
                      ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
                }`}
                title={subtask ? `当前子任务: ${subtask}` : "需要先创建子任务"}
              >
                <FolderOpen size={12} />
                单个
                {subtask && <span className="text-[10px] opacity-90">({subtask})</span>}
              </button>
              <button
                onClick={() => {
                  console.log('🔘 Clicking GLOBAL button, current scope:', reportScope, 'new scope will be: global');
                  setReportScope('global');
                }}
                className={`flex-1 px-2 py-1 text-xs font-bold rounded border transition-all flex items-center justify-center gap-1 ${
                  reportScope === 'global'
                    ? 'border-purple-500 bg-purple-500 text-white'
                    : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Globe size={12} />
                全局
              </button>
            </div>
            {!subtask && reportScope === 'single' && (
              <div className="text-[10px] text-orange-600 mt-1">
                ⚠️ 正在切换至全局模式...
              </div>
            )}
          </div>

          {/* Report Template */}
          <div className="flex-1">
            <div className="relative">
              <select
                value={reportTemplate}
                onChange={(e) => setReportTemplate(e.target.value as ReportTemplate)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-xs font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 appearance-none bg-white cursor-pointer"
              >
                {TEMPLATE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.icon} {option.label}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <svg className="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area - Split View (Absolute Positioning) */}
      <div className="flex-1 relative w-full h-full overflow-hidden">
        {/* Top: Report Display/Editor (50%) */}
        <div className="absolute top-0 left-0 right-0 h-[50%] overflow-y-auto bg-gray-50 border-b border-gray-200 z-0">
          {/* Report Actions Toolbar */}
          <div className="sticky top-0 z-10 bg-white border-b px-4 py-2 flex justify-between items-center shadow-sm">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-500 uppercase">
                {reportScope === 'global' ? '全局' : subtask || '任务'} 报告
              </span>
              {isEditing && (
                <span className="text-xs text-blue-600">编辑模式</span>
              )}
              {/* Temporary debug info */}
              <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                scope: {reportScope} | subtask: {subtask || 'none'} | content: {reportContent.length > 0 ? `${reportContent.length} chars` : 'empty'}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  console.log('🔄 Manual refresh triggered, current scope:', reportScope);
                  fetchReport();
                }}
                className={`p-1 hover:bg-gray-100 rounded ${isRefreshing ? 'animate-spin' : ''}`}
                title="刷新"
              >
                <RefreshCw size={12} />
              </button>
              <button
                onClick={handlePrint}
                className="px-2 py-1 text-xs font-bold rounded border bg-white hover:bg-gray-50 flex items-center gap-1"
                title="打印"
              >
                <Printer size={12} />
                打印
              </button>
              <button
                onClick={() => {
                  if (isEditing) {
                    handleSaveReport();
                  } else {
                    setTempReport(reportContent);
                    setIsEditing(true);
                  }
                }}
                className="px-2 py-1 text-xs font-bold rounded bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-1"
              >
                {isEditing ? (
                  <>
                    <Save size={12} />
                    保存
                  </>
                ) : (
                  <>
                    <FileEdit size={12} />
                    编辑
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Report Content */}
          <div className="px-4 pb-4">
            {isEditing ? (
              <textarea
                value={tempReport}
                onChange={(e) => setTempReport(e.target.value)}
                className="w-full min-h-[300px] p-4 text-sm font-mono border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white shadow-sm"
                placeholder="输入报告内容..."
              />
            ) : (
              <div className="max-w-4xl mx-auto">
                {reportContent ? (
                  <div className="prose prose-sm max-w-none bg-white rounded-lg shadow-sm p-6">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {reportContent}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="text-center text-gray-400 py-8 bg-white rounded-lg shadow-sm">
                    <FileText size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="text-sm font-medium text-gray-500 mb-1">暂无报告</p>
                    <p className="text-xs">在下方与 AI 对话生成报告</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Bottom: AI Chat Panel (50%) - Absolute Positioning */}
        <div className="absolute bottom-0 left-0 right-0 h-[50%] bg-white flex flex-col overflow-hidden z-0">
          {/* Chat Header */}
          <div className="px-4 py-2 border-b bg-gray-50 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <MessageSquare size={16} className="text-blue-600" />
              <span className="text-sm font-bold text-gray-700">
                AI 报告助手
              </span>
              <span className="text-xs text-gray-500">
                模板: {TEMPLATE_OPTIONS.find(t => t.value === reportTemplate)?.icon} {TEMPLATE_OPTIONS.find(t => t.value === reportTemplate)?.label}
              </span>
            </div>
          </div>

          {/* Chat Content */}
          <div className="flex-1 overflow-hidden min-h-0 relative">
            <ModularChatPanel
              taskId={taskId}
              mode="report"
              dataSource="raw"
              subtask={subtask}
              reportScope={reportScope}
              suggestions={CHAT_SUGGESTIONS.report}
              customPrompt={getTemplatePrompt()}
              onReportUpdate={(content) => {
                setReportContent(content);
                setIsEditing(false); // Exit edit mode when AI generates new content
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

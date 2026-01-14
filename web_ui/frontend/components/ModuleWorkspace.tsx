"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { MODULES } from '@/config/modules';
import { ModuleKey } from '@/types/modules';
import { ArrowLeft, RotateCcw, Plus } from 'lucide-react';
import DataExploreModule from './modules/DataExploreModule';
import ModelTrainingModule from './modules/ModelTrainingModule';
import DataPrepModule from './modules/DataPrepModule';
import ReportGenerationModule from './modules/ReportGenerationModule';
import TaskSelector from './TaskSelector';
import NewTaskDialog from './NewTaskDialog';
import { API_URL } from '@/config/api';

interface ModuleWorkspaceProps {
  module: ModuleKey;
  taskId: string;
  subtask?: string;
  onSubtaskChange?: (subtask: string) => void;
  onBack: () => void;
  onResetTask?: () => void;
}

interface Subtask {
  name: string;
  description: string;
  has_description: boolean;
  has_rubric: boolean;
}

export default function ModuleWorkspace({ module, taskId, subtask, onSubtaskChange, onBack, onResetTask }: ModuleWorkspaceProps) {
  const moduleConfig = MODULES[module];

  // Multi-task state
  const [taskMode, setTaskMode] = useState<'single' | 'multi'>('single');
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [isNewTaskDialogOpen, setIsNewTaskDialogOpen] = useState(false);

  // Fetch task mode on mount and when taskId changes
  useEffect(() => {
    fetchTaskMode();
  }, [taskId]);

  const fetchTaskMode = async () => {
    try {
      const modeRes = await axios.get(`${API_URL}/tasks/${taskId}/mode`);
      const mode = modeRes.data.mode;
      console.log('📊 Task mode:', mode, 'for task:', taskId);
      setTaskMode(mode);

      if (mode === 'multi') {
        // Fetch detailed subtask information
        const subtasksRes = await axios.get(`${API_URL}/tasks/${taskId}/subtasks`);
        const tasks = subtasksRes.data.subtasks || [];

        console.log('📋 Found subtasks:', tasks.map((t: any) => t.name));

        // Transform to match frontend interface
        const formattedTasks = tasks.map((task: any) => ({
          name: task.name,
          description: task.description || '',
          has_description: task.has_description,
          has_rubric: task.has_rubric
        }));

        setSubtasks(formattedTasks);

        // Set first task as current if none selected
        if (formattedTasks.length > 0 && !subtask && onSubtaskChange) {
          console.log('✅ Setting default subtask to:', formattedTasks[0].name);
          onSubtaskChange(formattedTasks[0].name);
        }
      }
    } catch (err) {
      console.error('Failed to fetch task mode:', err);
      setTaskMode('single');
    }
  };

  const handleTaskChange = (taskName: string) => {
    if (onSubtaskChange) {
      onSubtaskChange(taskName);
    }
  };

  const handleCreateTask = async (taskName: string, copyDescription: boolean, copyRubric: boolean) => {
    try {
      await axios.post(`${API_URL}/tasks/${taskId}/subtasks`, {
        name: taskName,
        copy_description: copyDescription,
        copy_rubric: copyRubric,
        from_task: subtask || null
      });

      // Refresh task list
      await fetchTaskMode();

      // Switch to the new task
      if (onSubtaskChange) {
        onSubtaskChange(taskName);
      }

      alert('任务创建成功');
    } catch (err: any) {
      console.error('Failed to create task:', err);
      throw new Error(err.response?.data?.detail || '创建任务失败');
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-sm overflow-hidden">
      {/* Module Header */}
      <div className="border-b bg-white shrink-0">
        {/* Task Selector (only show in multi-task mode) */}
        {taskMode === 'multi' ? (
          <div className="h-14 border-b bg-blue-50 flex items-center justify-between px-6">
            <div className="flex items-center gap-4 flex-1">
              <span className="text-sm font-bold text-gray-700 whitespace-nowrap">
                当前工作空间:
              </span>
              <div className="flex-1 max-w-md">
                <TaskSelector
                  tasks={subtasks}
                  currentTask={subtask || ''}
                  onTaskChange={handleTaskChange}
                  onCreateTask={() => setIsNewTaskDialogOpen(true)}
                />
              </div>
            </div>
            <div className="text-xs text-gray-500">
              切换工作空间以管理不同任务的数据和模型
            </div>
          </div>
        ) : (
          <div className="h-12 border-b bg-gray-50 flex items-center justify-between px-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">
                <strong>当前模式：</strong>单任务模式
              </span>
              <button
                onClick={() => setIsNewTaskDialogOpen(true)}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded flex items-center gap-1 transition-colors"
              >
                <Plus size={12} />
                新建工作空间
              </button>
            </div>
            <span className="text-xs text-gray-500">
              创建多个工作空间以管理不同的任务
            </span>
          </div>
        )}

        {/* Module Title Bar */}
        <div className="h-16 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="返回模块选择"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{moduleConfig.icon}</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{moduleConfig.title}</h2>
                <p className="text-xs text-gray-500">{moduleConfig.description}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              数据集: <span className="font-semibold text-gray-700">{taskId}</span>
              {taskMode === 'multi' && subtask && (
                <>
                  <span className="text-gray-300 mx-1">/</span>
                  <span className="font-semibold text-blue-600">{subtask}</span>
                </>
              )}
            </span>
            {onResetTask && (
              <button
                onClick={() => {
                  if (confirm('确定要重置任务到原始数据吗？这将清除所有处理结果。')) {
                    onResetTask();
                  }
                }}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-lg border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
                title="重置到原始数据"
              >
                <RotateCcw size={14} />
                重置数据
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Module Content */}
      <div className="flex-1 overflow-hidden">
        {module === 'prepare' && <DataPrepModule taskId={taskId} subtask={subtask} />}
        {module === 'explore' && <DataExploreModule taskId={taskId} subtask={subtask} />}
        {module === 'model' && <ModelTrainingModule taskId={taskId} subtask={subtask} />}
        {module === 'report' && <ReportGenerationModule taskId={taskId} subtask={subtask} />}
      </div>

      {/* New Task Dialog */}
      <NewTaskDialog
        isOpen={isNewTaskDialogOpen}
        onClose={() => setIsNewTaskDialogOpen(false)}
        onCreate={handleCreateTask}
        currentTaskName={subtask}
      />
    </div>
  );
}

"use client";

import React, { useState } from 'react';
import { X } from 'lucide-react';

interface NewTaskDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (taskName: string, copyDescription: boolean, copyRubric: boolean) => Promise<void>;
  currentTaskName?: string;
}

export default function NewTaskDialog({
  isOpen,
  onClose,
  onCreate,
  currentTaskName
}: NewTaskDialogProps) {
  const [taskName, setTaskName] = useState('');
  const [copyDescription, setCopyDescription] = useState(false);
  const [copyRubric, setCopyRubric] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!taskName.trim()) {
      setError('请输入任务名称');
      return;
    }

    // Only allow alphanumeric, underscore, hyphen, and Chinese characters
    const nameRegex = /^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$/;
    if (!nameRegex.test(taskName)) {
      setError('任务名称只能包含字母、数字、下划线、连字符和中文');
      return;
    }

    setIsCreating(true);
    setError('');

    try {
      await onCreate(taskName.trim(), copyDescription, copyRubric);
      // Reset form
      setTaskName('');
      setCopyDescription(false);
      setCopyRubric(false);
      onClose();
    } catch (err: any) {
      setError(err.message || '创建任务失败');
    } finally {
      setIsCreating(false);
    }
  };

  const handleCancel = () => {
    setTaskName('');
    setCopyDescription(false);
    setCopyRubric(false);
    setError('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={handleCancel}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Close button */}
        <button
          onClick={handleCancel}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={20} />
        </button>

        {/* Header */}
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          新建工作空间
        </h2>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Task name input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              任务名称
            </label>
            <input
              type="text"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              placeholder="例如: task_1 或 预测任务"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isCreating}
              autoFocus
            />
            <p className="mt-1 text-xs text-gray-500">
              支持字母、数字、下划线、连字符和中文
            </p>
          </div>

          {/* Copy options */}
          {currentTaskName && (
            <div className="mb-4 space-y-2">
              <p className="text-sm font-medium text-gray-700">
                从当前任务复制 ({currentTaskName}):
              </p>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={copyDescription}
                  onChange={(e) => setCopyDescription(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={isCreating}
                />
                <span className="text-sm text-gray-700">复制任务描述</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={copyRubric}
                  onChange={(e) => setCopyRubric(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={isCreating}
                />
                <span className="text-sm text-gray-700">复制评估标准</span>
              </label>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={handleCancel}
              disabled={isCreating}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isCreating}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isCreating ? '创建中...' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

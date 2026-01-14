"use client";

import React, { useState } from 'react';
import { ChevronDown, Plus } from 'lucide-react';

interface Task {
  name: string;
  description: string;
  has_description: boolean;
  has_rubric: boolean;
}

interface TaskSelectorProps {
  tasks: Task[];
  currentTask: string;
  onTaskChange: (taskName: string) => void;
  onCreateTask: () => void;
}

export default function TaskSelector({ tasks, currentTask, onTaskChange, onCreateTask }: TaskSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedTask = tasks.find(t => t.name === currentTask);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors min-w-[200px]"
      >
        <span className="flex-1 text-left truncate">
          {selectedTask ? selectedTask.name : '选择任务...'}
        </span>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 mt-2 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-hidden">
            <div className="p-2 border-b border-gray-100">
              <div className="text-xs font-semibold text-gray-500 px-2 py-1">
                当前工作空间 ({tasks.length})
              </div>
            </div>

            <div className="max-h-60 overflow-y-auto p-1">
              {tasks.map((task) => (
                <button
                  key={task.name}
                  onClick={() => {
                    onTaskChange(task.name);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 rounded text-sm hover:bg-gray-50 transition-colors mb-1 last:mb-0 ${
                    currentTask === task.name ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{task.name}</span>
                    <div className="flex gap-1">
                      {task.has_description && (
                        <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                          描述
                        </span>
                      )}
                      {task.has_rubric && (
                        <span className="text-[10px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
                          标准
                        </span>
                      )}
                    </div>
                  </div>
                  {task.description && (
                    <div className="text-xs text-gray-500 truncate mt-1">
                      {task.description}
                    </div>
                  )}
                </button>
              ))}
            </div>

            <div className="p-2 border-t border-gray-100">
              <button
                onClick={() => {
                  setIsOpen(false);
                  onCreateTask();
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-blue-600 hover:bg-blue-50 transition-colors flex items-center gap-2"
              >
                <Plus size={14} />
                新建工作空间
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

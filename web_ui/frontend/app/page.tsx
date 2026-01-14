"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Layout, Upload, Folder, RefreshCw } from "lucide-react";
import ModuleSelector from "@/components/ModuleSelector";
import ModuleWorkspace from "@/components/ModuleWorkspace";
import Sidebar from "@/components/Sidebar";
import { ModuleKey } from "@/types/modules";
import { API_URL } from "@/config/api";

export default function Home() {
  const [tasks, setTasks] = useState<string[]>([]);
  const [activeTaskId, setActiveTaskId] = useState("");
  const [activeModule, setActiveModule] = useState<ModuleKey | null>(null);
  const [currentSubtask, setCurrentSubtask] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Initial Fetch
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = () => {
    console.log("Fetching tasks from:", `${API_URL}/tasks`);
    axios.get(`${API_URL}/tasks`)
      .then(res => {
        console.log("Tasks fetched:", res.data);
        setTasks(res.data.tasks || []);
      })
      .catch(err => console.error("Failed to fetch tasks:", err));
  };

  const handleResetTask = async () => {
    if (!activeTaskId) return;
    try {
      await axios.post(`${API_URL}/tasks/${activeTaskId}/reset`);
      alert("任务已重置到原始数据");
    } catch (e: any) {
      alert("重置失败: " + (e.response?.data?.detail || e.message));
    }
  };

  const handleModuleSelect = (module: ModuleKey) => {
    setActiveModule(module);
  };

  const handleQuickPath = (modules: ModuleKey[]) => {
    // Execute modules in sequence
    if (modules.length > 0) {
      setActiveModule(modules[0]);
    }
  };

  const handleBackToSelector = () => {
    setActiveModule(null);
  };

  return (
    <main className="flex h-screen bg-gray-100/50 p-4 gap-4 text-gray-900 font-sans overflow-hidden">
      {/* Left Sidebar - Task List */}
      <Sidebar
        tasks={tasks}
        activeTaskId={activeTaskId}
        setActiveTaskId={(id) => {
          setActiveTaskId(id);
          setActiveModule(null); // Reset to module selector when switching tasks
          setCurrentSubtask(""); // Reset subtask when switching tasks
        }}
        fetchTasks={fetchTasks}
        setIsAnalyzing={setIsAnalyzing}
        API_URL={API_URL}
      />

      {/* Main Content Area */}
      <section className="flex-1 flex flex-col min-w-0 relative bg-white border rounded-2xl shadow-sm overflow-hidden">
        {!activeTaskId ? (
          // No task selected
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50/30">
            <Folder size={64} className="mb-4 opacity-20" />
            <p className="text-lg font-medium text-gray-500 mb-2">选择或创建一个任务</p>
            <p className="text-sm text-gray-400">从左侧列表选择任务，或上传新数据</p>
          </div>
        ) : !activeModule ? (
          // Module Selector
          <ModuleSelector
            taskId={activeTaskId}
            onModuleSelect={handleModuleSelect}
            onQuickPathSelect={handleQuickPath}
          />
        ) : (
          // Active Module Workspace
          <ModuleWorkspace
            module={activeModule}
            taskId={activeTaskId}
            subtask={currentSubtask}
            onSubtaskChange={setCurrentSubtask}
            onBack={handleBackToSelector}
            onResetTask={handleResetTask}
          />
        )}
      </section>

      {/* Right Panel - Logs (Optional, can be removed if not needed) */}
      {/* Uncomment if you want to keep a logs panel on the right
      <aside className="w-[450px] bg-white border rounded-2xl shadow-sm flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b">
          <h3 className="text-sm font-bold text-gray-700">系统日志</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-gray-600">
          {logs || '暂无日志'}
        </div>
      </aside>
      */}
    </main>
  );
}

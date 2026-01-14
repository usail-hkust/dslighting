"use client";

import { useState } from "react";
import axios from "axios";
import { Folder, Upload, Layout, PlusCircle, FileText } from "lucide-react";

interface SidebarProps {
  tasks: string[];
  activeTaskId: string;
  setActiveTaskId: (id: string) => void;
  fetchTasks: () => void;
  setIsAnalyzing: (val: boolean) => void;
  API_URL: string;
}

export default function Sidebar({
  tasks,
  activeTaskId,
  setActiveTaskId,
  fetchTasks,
  setIsAnalyzing,
  API_URL
}: SidebarProps) {
  const [taskName, setTaskName] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [taskMode, setTaskMode] = useState("standard_ml");

  const handleUpload = async () => {
    const fileEl = document.getElementById('new-task-file') as HTMLInputElement;
    const pdfEl = document.getElementById('new-task-pdf') as HTMLInputElement;
    const file = fileEl.files?.[0];
    const pdfFile = pdfEl.files?.[0];

    if(!taskName) {
        alert("请提供任务名称");
        return;
    }
    if(!file && !pdfFile && !taskDescription) {
        alert("请至少上传数据文件、PDF或填写任务描述");
        return;
    }

    const fd = new FormData();
    if (file) fd.append("file", file);
    if (pdfFile) fd.append("pdf_file", pdfFile);
    fd.append("task_name", taskName);
    fd.append("task_mode", taskMode);
    fd.append("task_comment", taskDescription);

    try {
      await axios.post(`${API_URL}/upload`, fd);
      alert("上传成功！系统正在分析任务...");
      fetchTasks();
      setActiveTaskId(taskName);
      setIsAnalyzing(true);
      setTaskName("");
      setTaskDescription("");
      setTaskMode("standard_ml");
      fileEl.value = "";
      pdfEl.value = "";
    } catch (err: any) {
      alert("上传失败: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <aside className="w-72 bg-gray-50 border-r flex flex-col shrink-0 h-full overflow-hidden">
      {/* 顶部 Logo - 禁止收缩 */}
      <div className="p-4 border-b bg-white font-bold text-lg text-blue-600 flex items-center gap-2 shrink-0">
        <Layout size={20}/> DSLighting
      </div>

      {/* 任务列表 - 允许滚动并占据剩余空间 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-xs font-bold text-gray-400 mb-2 uppercase px-2 tracking-wider">任务列表</div>
        {tasks.map(t => (
          <button
            key={t}
            onClick={() => setActiveTaskId(t)}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm flex items-center gap-2 transition-all ${
              activeTaskId === t
                ? 'bg-blue-600 text-white font-medium shadow-md shadow-blue-200'
                : 'text-gray-600 hover:bg-gray-200 hover:text-gray-900'
            }`}
          >
            <Folder size={16} /> <span className="truncate">{t}</span>
          </button>
        ))}
      </div>

      {/* 底部操作区 - 关键点：使用 shrink-0 防止被压扁 */}
      <div className="p-4 border-t bg-white shrink-0 space-y-3 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
          <PlusCircle size={14} />
          <span className="text-xs font-bold uppercase">新建任务</span>
        </div>

        {/* Task Name */}
        <input
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 ring-blue-500/20 focus:border-blue-500 transition-all"
          placeholder="任务名称..."
          value={taskName}
          onChange={e => setTaskName(e.target.value)}
        />

        {/* Task Description - Text Input */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block">任务描述（可选）</label>
          <textarea
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
            placeholder="描述任务要求、目标等..."
            rows={2}
            value={taskDescription}
            onChange={e => setTaskDescription(e.target.value)}
          />
        </div>

        {/* Task Description - PDF Upload */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block flex items-center gap-1">
            <FileText size={12} />
            上传任务描述PDF（可选）
          </label>
          <input
            type="file"
            accept=".pdf,application/pdf"
            className="w-full text-xs text-gray-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
            id="new-task-pdf"
          />
        </div>

        {/* Task Mode Selection */}
        <div className="flex gap-2">
          <button
            onClick={() => setTaskMode("standard_ml")}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-all ${
              taskMode === "standard_ml"
                ? "bg-blue-50 border-blue-200 text-blue-700"
                : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50"
            }`}
          >
            标准机器学习
          </button>
          <button
            onClick={() => setTaskMode("open_ended")}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-all ${
              taskMode === "open_ended"
                ? "bg-purple-50 border-purple-200 text-purple-700"
                : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50"
            }`}
          >
            开放式任务
          </button>
        </div>

        {/* Data File Input */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block">上传数据文件（可选）</label>
          <input
            type="file"
            className="w-full text-xs text-gray-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            id="new-task-file"
          />
        </div>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-bold flex justify-center items-center gap-2 transition-colors shadow-sm"
        >
          <Upload size={16} /> 创建任务
        </button>
      </div>
    </aside>
  );
}
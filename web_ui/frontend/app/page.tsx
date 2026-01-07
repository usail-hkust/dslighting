"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Upload, Play, FileText, Terminal, Folder, Save, Bot } from "lucide-react";

export default function Home() {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [tasks, setTasks] = useState<string[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState("aide");
  const [selectedModel, setSelectedModel] = useState("");
  const [activeTaskId, setActiveTaskId] = useState("");
  const [newTaskName, setNewTaskName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  
  // Task Details
  const [taskDesc, setTaskDesc] = useState("");
  const [taskFiles, setTaskFiles] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);

  // Status
  const [status, setStatus] = useState("idle");
  const [logs, setLogs] = useState("");
  const [runningTaskId, setRunningTaskId] = useState("");

  const API_URL = "http://localhost:8001";

  useEffect(() => {
    fetchWorkflows();
    fetchModels();
    fetchTasks();
  }, []);

  const fetchWorkflows = () => axios.get(`${API_URL}/workflows`).then(res => setWorkflows(res.data.workflows));
  const fetchModels = () => axios.get(`${API_URL}/models`).then(res => {
    setModels(res.data.models);
    if (res.data.models.length > 0) {
      setSelectedModel(res.data.models[0]);
    }
  });
  const fetchTasks = () => axios.get(`${API_URL}/tasks`).then(res => setTasks(res.data.tasks));

  useEffect(() => {
    if (activeTaskId) {
      loadTaskDetails(activeTaskId);
    }
  }, [activeTaskId]);

  const loadTaskDetails = async (id: string) => {
    try {
      const res = await axios.get(`${API_URL}/tasks/${id}`);
      setTaskDesc(res.data.description);
      setTaskFiles(res.data.files);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (runningTaskId) {
      interval = setInterval(() => {
        axios.get(`${API_URL}/logs/${runningTaskId}`).then((res) => {
          setLogs(res.data.logs);
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [runningTaskId]);

  const handleUpload = async () => {
    if (!file || !newTaskName) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("task_name", newTaskName);

    try {
      await axios.post(`${API_URL}/upload`, formData);
      alert("Upload successful!");
      fetchTasks();
      setActiveTaskId(newTaskName);
      setNewTaskName("");
      setFile(null);
    } catch (e) {
      alert("Upload failed");
      console.error(e);
    }
  };

  const handleSaveDescription = async () => {
    if (!activeTaskId) return;
    const formData = new FormData();
    formData.append("description", taskDesc);
    await axios.post(`${API_URL}/tasks/${activeTaskId}/update`, formData);
    setIsEditing(false);
    alert("Task description updated!");
  };

  const handleRun = async () => {
    if (!activeTaskId) return;
    setStatus("running");
    setRunningTaskId(activeTaskId);
    try {
      const formData = new FormData();
      formData.append("workflow", selectedWorkflow);
      formData.append("task_id", activeTaskId);
      formData.append("model", selectedModel);
      
      await axios.post(`${API_URL}/run`, formData);
      setStatus("started");
    } catch (e) {
      console.error(e);
      setStatus("error");
    }
  };

  return (
    <main className="flex h-screen bg-gray-50 text-gray-900">
      {/* Sidebar: Task List */}
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            DSLighting
          </h1>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs font-semibold text-gray-500 mb-2 uppercase px-2">Tasks</div>
          {tasks.map(t => (
            <button
              key={t}
              onClick={() => setActiveTaskId(t)}
              className={`w-full text-left px-3 py-2 rounded text-sm mb-1 flex items-center gap-2 ${activeTaskId === t ? 'bg-blue-50 text-blue-700 font-medium' : 'hover:bg-gray-50'}`}
            >
              <Folder size={14} /> {t}
            </button>
          ))}
        </div>

        <div className="p-4 border-t bg-gray-50">
          <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">New Task</div>
          <input 
            className="w-full border rounded px-2 py-1 text-sm mb-2" 
            placeholder="Task Name (e.g. my-task)" 
            value={newTaskName}
            onChange={e => setNewTaskName(e.target.value)}
          />
          <input 
            type="file" 
            className="w-full text-xs mb-2"
            onChange={e => setFile(e.target.files?.[0] || null)}
          />
          <button 
            onClick={handleUpload}
            disabled={!file || !newTaskName}
            className="w-full bg-black text-white rounded py-1 text-sm disabled:opacity-50 flex justify-center items-center gap-2"
          >
            <Upload size={12} /> Upload
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <section className="flex-1 flex flex-col overflow-hidden">
        {activeTaskId ? (
          <>
            <header className="bg-white border-b px-6 py-4 flex flex-col gap-4 shadow-sm">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    {activeTaskId}
                  </h2>
                  <div className="text-xs text-gray-500 flex gap-2 mt-1">
                    {taskFiles.map(f => <span key={f} className="bg-gray-100 px-2 py-0.5 rounded">{f}</span>)}
                  </div>
                </div>
                
                <button 
                  onClick={handleRun}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded text-sm font-bold flex items-center gap-2 transition-colors shadow-md"
                >
                  <Play size={16} /> Run Agent
                </button>
              </div>

              <div className="flex items-center gap-6 bg-gray-50 p-2 rounded-md border border-gray-100">
                <div className="flex items-center gap-2">
                  <label className="text-xs font-bold text-gray-500 uppercase">Workflow:</label>
                  <select 
                    value={selectedWorkflow} 
                    onChange={(e) => setSelectedWorkflow(e.target.value)}
                    className="border rounded px-2 py-1 text-sm bg-white"
                  >
                    {workflows.map(w => <option key={w} value={w}>{w}</option>)}
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-xs font-bold text-gray-500 uppercase flex items-center gap-1">
                    <Bot size={12}/> Model:
                  </label>
                  <select 
                    value={selectedModel} 
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="border rounded px-2 py-1 text-sm bg-white"
                  >
                    {models.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              {/* Editor / Description Panel */}
              <div className="w-1/2 p-6 overflow-y-auto border-r bg-white">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <FileText size={18} /> Task Description / Prompt
                  </h3>
                  <button 
                    onClick={() => isEditing ? handleSaveDescription() : setIsEditing(true)}
                    className={`text-xs px-3 py-1 rounded border flex items-center gap-1 ${isEditing ? 'bg-green-50 text-green-700 border-green-200' : 'hover:bg-gray-50'}`}
                  >
                    {isEditing ? <><Save size={12}/> Save</> : "Edit"}
                  </button>
                </div>
                
                {isEditing ? (
                  <textarea 
                    className="w-full h-[calc(100vh-280px)] border rounded p-4 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-blue-100 outline-none"
                    value={taskDesc}
                    onChange={(e) => setTaskDesc(e.target.value)}
                  />
                ) : (
                  <div className="prose prose-sm max-w-none text-gray-600 whitespace-pre-wrap">
                    {taskDesc || "No description provided."}
                  </div>
                )}
              </div>

              {/* Logs / Terminal Panel */}
              <div className="w-1/2 bg-gray-900 text-gray-300 flex flex-col font-mono text-sm">
                <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
                  <span className="flex items-center gap-2 font-semibold text-gray-100">
                    <Terminal size={14} /> Agent Output
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${status === 'running' ? 'bg-yellow-400 animate-pulse' : 'bg-gray-500'}`}></span>
                    <span className="text-xs uppercase">{status}</span>
                  </div>
                </div>
                <div className="flex-1 p-4 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {logs || <span className="text-gray-600 italic">Waiting for agent execution...</span>}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <Folder size={48} className="mb-4 opacity-20" />
            <p>Select a task from the sidebar or upload a new one.</p>
          </div>
        )}
      </section>
    </main>
  );
}

"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Upload, Play, FileText, Terminal } from "lucide-react";

export default function Home() {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState("aide");
  const [taskId, setTaskId] = useState("custom-task-01");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("idle");
  const [logs, setLogs] = useState("");
  const [activeRunId, setActiveRunId] = useState("");

  const API_URL = "http://localhost:8000";

  useEffect(() => {
    // Fetch workflows
    axios.get(`${API_URL}/workflows`).then((res) => {
      setWorkflows(res.data.workflows);
    }).catch(err => console.error("Backend offline?", err));
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (activeRunId) {
      interval = setInterval(() => {
        axios.get(`${API_URL}/logs/${activeRunId}`).then((res) => {
          setLogs(res.data.logs);
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [activeRunId]);

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("task_name", taskId);

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      alert("Upload successful!");
    } catch (e) {
      alert("Upload failed");
      console.error(e);
    }
  };

  const handleRun = async () => {
    if (!taskId) return;
    setStatus("running");
    try {
      const formData = new FormData();
      formData.append("workflow", selectedWorkflow);
      formData.append("task_id", taskId);
      
      const res = await axios.post(`${API_URL}/run`, formData);
      setActiveRunId(taskId); // Using task_id as run_id for simplicity in this demo backend
      setStatus("started");
    } catch (e) {
      console.error(e);
      setStatus("error");
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-6xl mx-auto">
      <header className="mb-10 border-b pb-4">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          DSLighting Interactive
        </h1>
        <p className="text-gray-500">Autonomous Data Science Agent Runner</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Configuration */}
        <div className="space-y-6 bg-white p-6 rounded-lg shadow-sm border border-gray-100 h-fit">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FileText size={20} /> Configuration
          </h2>

          <div>
            <label className="block text-sm font-medium mb-1">Task ID / Name</label>
            <input 
              type="text" 
              value={taskId} 
              onChange={(e) => setTaskId(e.target.value)}
              className="w-full border p-2 rounded text-black"
              placeholder="e.g. bike-sharing-v1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Workflow</label>
            <select 
              value={selectedWorkflow} 
              onChange={(e) => setSelectedWorkflow(e.target.value)}
              className="w-full border p-2 rounded text-black"
            >
              {workflows.map(w => <option key={w} value={w}>{w}</option>)}
            </select>
          </div>

          <div className="border-t pt-4">
            <label className="block text-sm font-medium mb-2">Upload Dataset (.csv / .zip)</label>
            <div className="flex gap-2">
              <input 
                type="file" 
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-sm"
              />
            </div>
            <button 
              onClick={handleUpload}
              disabled={!file}
              className="mt-2 w-full bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded flex items-center justify-center gap-2 text-sm transition-colors"
            >
              <Upload size={14} /> Upload Data
            </button>
          </div>

          <button 
            onClick={handleRun}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded font-bold flex items-center justify-center gap-2 transition-colors"
          >
            <Play size={18} /> Run Agent
          </button>
        </div>

        {/* Right Column: Status & Logs */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-gray-900 text-gray-100 p-6 rounded-lg shadow-lg min-h-[500px] flex flex-col font-mono">
            <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-2">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Terminal size={18} /> Live Terminal
              </h2>
              <span className={`px-2 py-0.5 rounded text-xs ${status === 'running' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-green-500/20 text-green-300'}`}>
                {status.toUpperCase()}
              </span>
            </div>
            <div className="flex-1 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed p-2 bg-black/30 rounded">
              {logs || "Ready to start..."}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

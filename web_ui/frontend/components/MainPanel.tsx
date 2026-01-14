"use client";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkBreaks from 'remark-breaks';
import { 
  Play, X, Target, Activity, Printer, RefreshCw, 
  Code2, ImageIcon, Terminal, 
  Folder, FileText, Edit3, FileSearch, Book, PenTool, RotateCcw
} from "lucide-react";
import { useState, useEffect } from 'react';
import axios from 'axios';

import { API_URL } from '@/config/api';

interface MainPanelProps {
  activeTaskId: string;
  selectedWorkflow: string;
  setSelectedWorkflow: (w: string) => void;
  workflows: string[];
  executionStatus: string;
  handleRun: () => void;
  handleStop: () => void;
  descContent: string;
  isEditingDesc: boolean;
  setIsEditingDesc: (v: boolean) => void;
  tempDesc: string;
  setTempDesc: (v: string) => void;
  saveDescription: () => void;
  reportContent: string;
  edaReportContent?: string;
  isEditingReport: boolean;
  setIsEditingReport: (v: boolean) => void;
  tempReport: string;
  setTempReport: (v: string) => void;
  saveReport: () => void;
  manualRefresh: () => void;
  handleRequestReport: () => void;
  handleRequestEdaReport: () => void;
  handleResetTask: () => void; // New
  isRefreshing: boolean;
  copilotMode: "goal" | "chat" | "report" | "improve" | "eda" | "synthetic";
  edaCodeFromAssistant?: string;
  edaExecutionResult?: {stdout: string, stderr: string, images: string[], distributed?: string[]};
}

export default function MainPanel({
  activeTaskId,
  selectedWorkflow,
  setSelectedWorkflow,
  workflows,
  executionStatus,
  handleRun,
  handleStop,
  descContent,
  isEditingDesc,
  setIsEditingDesc,
  tempDesc,
  setTempDesc,
  saveDescription,
  reportContent,
  edaReportContent,
  isEditingReport,
  setIsEditingReport,
  tempReport,
  setTempReport,
  saveReport,
  manualRefresh,
  handleRequestReport,
  handleRequestEdaReport,
  handleResetTask,
  isRefreshing,
  copilotMode,
  edaCodeFromAssistant,
  edaExecutionResult,
  selectedDataView, // NEW
  setSelectedDataView // NEW
}: MainPanelProps & {
  selectedDataView: "data" | "prepared_data";
  setSelectedDataView: (v: "data" | "prepared_data") => void;
}) {
  
  const [edaCode, setEdaCode] = useState("");
  const [isEditingEda, setIsEditingEda] = useState(false);
  const [edaResult, setEdaResult] = useState<{stdout: string, stderr: string, images: string[], distributed?: string[]} | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [workspaceFiles, setWorkspaceFiles] = useState<{name: string, size: string, is_dir: boolean}[]>([]);
  
  // Rubric State
  const [rubricContent, setRubricContent] = useState("");
  const [isEditingRubric, setIsEditingRubric] = useState(false);
  const [tempRubric, setTempRubric] = useState("");

  const fetchWorkspaceFiles = async () => {
    try {
      const res = await axios.get(`${API_URL}/tasks/${activeTaskId}/workspace/files?view=${selectedDataView}`);
      setWorkspaceFiles(res.data.files);
    } catch (e) { console.error(e); }
  };

  const fetchRubric = async () => {
    try {
      const res = await axios.get(`${API_URL}/tasks/${activeTaskId}/rubric`);
      setRubricContent(res.data.content);
    } catch (e) { 
      setRubricContent(""); 
    }
  };

  const saveRubric = async () => {
    try {
      await axios.post(`${API_URL}/tasks/${activeTaskId}/rubric`, { content: tempRubric });
      setRubricContent(tempRubric);
      setIsEditingRubric(false);
    } catch (e) { alert("Failed to save rubric"); }
  };

  useEffect(() => {
    if (activeTaskId) {
      fetchWorkspaceFiles();
      fetchRubric(); // Fetch rubric when task changes
      setEdaResult(null);
    }
  }, [activeTaskId, selectedDataView]); // Trigger fetch when view changes

  // SYNC Code and Result from Assistant
  useEffect(() => {
    if (copilotMode === 'eda') {
      if (edaCodeFromAssistant) {
        setEdaCode(edaCodeFromAssistant);
        setIsEditingEda(false);
      }
      if (edaExecutionResult) {
        setEdaResult(edaExecutionResult);
        fetchWorkspaceFiles();
      }
    }
  }, [edaCodeFromAssistant, edaExecutionResult, copilotMode]);

  const handleExecuteCode = async () => {
    if (!edaCode.trim()) return;
    setIsExecuting(true);
    try {
      const formData = new FormData();
      formData.append("code", edaCode);
      const res = await axios.post(`${API_URL}/tasks/${activeTaskId}/eda/execute`, formData);
      setEdaResult(res.data);
      fetchWorkspaceFiles();
    } catch (e) { alert("Execution failed"); }
    finally { setIsExecuting(false); }
  };

  const handlePrint = () => { window.print(); };

  if (!activeTaskId) return (
    <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50/30">
      <Target size={48} className="mb-4 opacity-20" />
      <p className="text-sm font-medium">Select a Task</p>
    </div>
  );

  const isEdaMode = copilotMode === 'eda';

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      <header className="h-14 border-b flex items-center justify-between px-10 bg-white shrink-0">
        <div className="flex items-center gap-4 min-w-0">
          <h2 className="text-lg font-bold text-gray-800 truncate">{activeTaskId}</h2>
          <button 
            onClick={() => { if(confirm("Are you sure? This will restore data from the original backup and wipe current EDA logs.")) handleResetTask(); }}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 text-[10px] font-bold transition-all shadow-sm shrink-0"
            title="Reset to Original Raw Data"
          >
            <RotateCcw size={12} /> Reset Data
          </button>
        </div>
        <div className="flex items-center gap-3">
          <select value={selectedWorkflow} onChange={e => setSelectedWorkflow(e.target.value)} className="bg-gray-50 border rounded px-2 py-1 text-xs font-bold">
            {workflows.map(w => <option key={w} value={w}>{w}</option>)}
          </select>
          <button onClick={executionStatus === 'running' ? handleStop : handleRun} className={`${executionStatus === 'running' ? 'bg-red-600 animate-pulse' : 'bg-blue-600'} text-white px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2`}>
            {executionStatus === 'running' ? <><X size={14} /> Stop</> : <><Play size={14} fill="currentColor" /> Run</>}
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col overflow-hidden">
        {!isEdaMode && (
          <div className="h-1/2 border-b flex flex-col bg-white overflow-hidden">
            <div className="px-10 py-2 border-b bg-gray-50 flex justify-between items-center shrink-0">
              <span className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2"><Target size={14} className="text-blue-500"/> Task Goal</span>
              <button onClick={() => { if(isEditingDesc) saveDescription(); else { setTempDesc(descContent); setIsEditingDesc(true); }}} className="text-[10px] font-bold px-2 py-1 rounded border bg-white">{isEditingDesc ? "Save" : "Edit"}</button>
            </div>
            <div className="flex-1 overflow-y-auto p-10 prose prose-sm max-w-none">
              {isEditingDesc ? <textarea className="w-full h-full p-4 border rounded font-mono text-xs outline-none" value={tempDesc} onChange={e => setTempDesc(e.target.value)}/> : <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]} rehypePlugins={[rehypeKatex]}>{descContent}</ReactMarkdown>}
            </div>
            
            {/* Rubric Section - Only show if content exists (Open-Ended Tasks) */}
            {rubricContent && (
              <div className="border-t border-gray-100 flex flex-col h-1/3 bg-gray-50/30">
                <div className="px-10 py-2 border-b bg-gray-50 flex justify-between items-center shrink-0">
                  <span className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2"><Book size={14} className="text-amber-500"/> Evaluation Criteria (Rubric)</span>
                  <button onClick={() => { if(isEditingRubric) saveRubric(); else { setTempRubric(rubricContent); setIsEditingRubric(true); }}} className="text-[10px] font-bold px-2 py-1 rounded border bg-white">{isEditingRubric ? "Save" : "Edit"}</button>
                </div>
                <div className="flex-1 overflow-y-auto p-10 prose prose-sm max-w-none">
                  {isEditingRubric ? (
                    <textarea 
                      className="w-full h-full p-4 border rounded font-mono text-xs outline-none bg-white" 
                      value={tempRubric} 
                      onChange={e => setTempRubric(e.target.value)}
                    />
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]} rehypePlugins={[rehypeKatex]}>{rubricContent}</ReactMarkdown>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex-1 flex flex-col bg-white min-h-0 overflow-hidden">
          {isEdaMode ? (
            <div className="flex-1 flex flex-col overflow-hidden bg-[#0f172a]">
              {/* TIER 1: EDITOR */}
              <div className="h-[35%] flex flex-col border-b border-white/10 shrink-0">
                <div className="px-6 py-2 bg-slate-800/50 flex justify-between items-center shrink-0 border-b border-white/5">
                  <span className="text-[10px] text-blue-400 font-mono font-black flex items-center gap-2 tracking-widest"><Code2 size={14}/> PYTHON WORKBENCH</span>
                  <div className="flex gap-2">
                    <button onClick={() => setIsEditingEda(!isEditingEda)} className={`px-3 py-1 rounded text-[10px] font-bold flex items-center gap-2 transition-all ${isEditingEda ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}><Edit3 size={12}/> {isEditingEda ? "Save & Lock" : "Edit Script"}</button>
                    <button onClick={handleExecuteCode} disabled={isExecuting} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1 rounded text-[10px] font-bold flex items-center gap-2 shadow-lg">{isExecuting ? <RefreshCw size={12} className="animate-spin"/> : <Play size={12} fill="currentColor"/>} Run Cell</button>
                  </div>
                </div>
                <textarea value={edaCode} readOnly={!isEditingEda} onChange={e => setEdaCode(e.target.value)} className={`flex-1 w-full bg-[#1e293b] text-emerald-400 p-8 font-mono text-xs outline-none resize-none leading-relaxed ${!isEditingEda ? 'opacity-70' : ''}`}/>
              </div>

              {/* TIER 2: OUTPUT */}
              <div className="h-[25%] flex flex-col border-b border-white/10 overflow-hidden bg-[#020617] shrink-0">
                <div className="px-6 py-1.5 bg-black/40 text-[9px] text-slate-500 font-mono font-bold uppercase tracking-widest flex items-center gap-2 border-b border-white/5"><Terminal size={12}/> Output</div>
                <div className="flex-1 overflow-y-auto p-8 space-y-4">
                  {edaResult ? (
                    <div className="animate-in fade-in slide-in-from-top-2">
                      {edaResult.stdout && <pre className="text-slate-300 font-mono text-xs whitespace-pre-wrap bg-white/5 p-5 rounded-lg border border-white/5 mb-4">{edaResult.stdout}</pre>}
                      {edaResult.stderr && <pre className="text-red-400 font-mono text-xs whitespace-pre-wrap bg-red-900/10 p-5 rounded-lg border border-red-900/20 mb-4">{edaResult.stderr}</pre>}
                      {edaResult.images?.length > 0 && <div className="grid grid-cols-2 gap-6">{edaResult.images.map((img, i) => <div key={i} className="bg-white/5 p-2 rounded-xl border border-white/10"><img src={`http://localhost:8003${img}`} className="w-full h-auto rounded-lg shadow-2xl" alt="plot"/></div>)}</div>}
                    </div>
                  ) : <div className="h-full flex items-center justify-center opacity-10 text-white text-[10px] font-mono tracking-widest">AWAITING EXECUTION</div>}
                </div>
              </div>

              {/* TIER 3: EDA REPORT */}
              <div className="flex-1 flex flex-col overflow-hidden bg-white rounded-t-[2.5rem] shadow-inner">
                <div className="px-10 py-4 border-b bg-gray-50/50 flex items-center justify-between shrink-0">
                  <div className="flex items-center gap-6 overflow-x-auto no-scrollbar">
                    <div className="flex items-center gap-2 mr-4">
                      <span className="text-[10px] text-amber-600 font-black uppercase flex items-center gap-2 whitespace-nowrap">
                        <FileSearch size={14}/> Workspace Snapshot
                      </span>
                      <select 
                        value={selectedDataView} 
                        onChange={e => setSelectedDataView(e.target.value as any)}
                        className="bg-amber-50 border border-amber-200 text-amber-700 text-[10px] font-bold rounded px-1 py-0.5 outline-none cursor-pointer hover:bg-amber-100 transition-colors"
                      >
                        <option value="data">Raw Data</option>
                        <option value="prepared_data">Processed Data</option>
                      </select>
                      <button 
                        onClick={fetchWorkspaceFiles} 
                        className="p-1 hover:bg-amber-100 rounded text-amber-600 transition-colors"
                        title="Refresh file list"
                      >
                        <RefreshCw size={12} />
                      </button>
                    </div>
                    <div className="flex gap-2">
                      {workspaceFiles.map((file, i) => (
                        <div key={i} className="flex items-center gap-1.5 px-3 py-1 bg-white border border-gray-200 rounded-full text-[10px] text-gray-600 whitespace-nowrap shadow-sm hover:border-amber-300 transition-colors">
                          {file.is_dir ? <Folder size={10} className="text-blue-500"/> : <FileText size={10} className="text-gray-400"/>}
                          <span>{file.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={handleRequestEdaReport} title="Regenerate via AI" className="text-[10px] font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 flex items-center gap-1.5 transition-all shadow-sm">
                      <PenTool size={12}/> Update Log
                    </button>
                    <button onClick={() => { if(isEditingReport) saveReport(); else { setTempReport(edaReportContent || ""); setIsEditingReport(true); }}} className="text-[10px] font-bold px-3 py-1 rounded-full border bg-white hover:bg-gray-50 flex items-center gap-1.5 shadow-sm">
                      <Edit3 size={12}/> {isEditingReport ? "Save Log" : "Edit Log"}
                    </button>
                    <button onClick={manualRefresh} className={`p-1.5 hover:bg-gray-200 rounded-full ${isRefreshing ? 'animate-spin text-blue-600' : 'text-gray-400'}`}><RefreshCw size={14}/></button>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-12 prose prose-slate max-w-none prose-headings:font-black prose-h1:text-2xl">
                  {isEditingReport ? (
                    <textarea 
                      className="w-full h-full p-4 border rounded font-mono text-xs outline-none" 
                      value={tempReport} 
                      onChange={e => setTempReport(e.target.value)}
                    />
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]} rehypePlugins={[rehypeKatex]}>
                      {edaReportContent}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="px-10 py-2 border-b bg-gray-50 flex justify-between items-center shrink-0">
                <span className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2"><Activity size={14} className="text-purple-500"/> Report</span>
                <div className="flex gap-2 items-center">
                  <button onClick={manualRefresh} className={`p-1 hover:bg-gray-200 rounded-md border bg-white ${isRefreshing ? 'animate-spin text-blue-600' : 'text-gray-400'}`}><RefreshCw size={14}/></button>
                  <button onClick={handleRequestReport} className="text-[10px] font-bold px-3 py-1.5 rounded border bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 flex items-center gap-1.5 shadow-sm"><PenTool size={12}/> Generate Report</button>
                  <button onClick={handlePrint} className="text-[10px] font-bold px-2 py-1 rounded border bg-white hover:bg-gray-50 flex items-center gap-1"><Printer size={12}/> PDF</button>
                  <button onClick={() => { if(isEditingReport) saveReport(); else { setTempReport(reportContent); setIsEditingReport(true); }}} className="text-[10px] font-bold px-2 py-1 rounded border bg-white">{isEditingReport ? "Save" : "Edit"}</button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-12 bg-gray-50/20">
                <div className="bg-white border rounded-xl shadow-sm p-16 mx-auto max-w-4xl min-h-full prose prose-slate max-w-none">
                  {isEditingReport ? <textarea className="w-full h-full min-h-[500px] p-4 border rounded font-mono text-xs outline-none" value={tempReport} onChange={e => setTempReport(e.target.value)}/> : <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]} rehypePlugins={[rehypeKatex]}>{reportContent}</ReactMarkdown>}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
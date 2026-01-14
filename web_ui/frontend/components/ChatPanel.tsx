import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Send, Check, AlertTriangle } from "lucide-react";

interface ChatPanelProps {
  chatHistory: { role: string; content: string; updated_content?: any }[];
  isChatSending: boolean;
  copilotMode: string;
  setCopilotMode: (m: "goal" | "chat" | "report") => void;
  chatInput: string;
  setChatInput: (v: string) => void;
  handleSendMessage: (blueprintJson?: string) => void;
  chatEndRef: any;
}

export default function ChatPanel({
  chatHistory,
  isChatSending,
  copilotMode,
  setCopilotMode,
  chatInput,
  setChatInput,
  handleSendMessage,
  chatEndRef
}: ChatPanelProps) {
  
  const [activeBlueprint, setActiveBlueprint] = useState<string | null>(null);
  const [blueprintError, setBlueprintError] = useState<string | null>(null);

  // Detect latest blueprint from assistant history
  useEffect(() => {
    const lastMsg = chatHistory[chatHistory.length - 1];
    if (lastMsg?.role === 'assistant' && lastMsg.updated_content?.blueprint) {
      // Pretty print JSON
      setActiveBlueprint(JSON.stringify(lastMsg.updated_content.blueprint, null, 2));
      setChatInput("Confirmed"); // Default confirm message
    } else {
      setActiveBlueprint(null);
    }
  }, [chatHistory, setChatInput]);

  const onSend = () => {
    if (activeBlueprint) {
      try {
        JSON.parse(activeBlueprint); // Validate
        handleSendMessage(activeBlueprint);
      } catch (e) {
        setBlueprintError("Invalid JSON syntax");
      }
    } else {
      handleSendMessage();
    }
  };

  return (
    <div className="flex-1 overflow-hidden relative flex flex-col">
      <div className="flex p-2 gap-1 border-b">
        {["goal", "chat", "report"].map(m => (
          <button key={m} onClick={() => setCopilotMode(m as any)} className={`flex-1 py-1 text-[10px] font-bold rounded capitalize ${copilotMode === m ? 'bg-blue-100 text-blue-700' : 'text-gray-500'}`}>{m}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gray-50/50">
        {chatHistory.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[90%] rounded-2xl px-5 py-4 text-sm shadow-md transition-all ${ 
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-br-none' 
                : 'bg-white border border-gray-100 text-gray-800 rounded-bl-none'
            }`}>
              {msg.role === 'assistant' && (
                <div className="text-[10px] font-black text-blue-500/50 uppercase tracking-widest mb-2 flex items-center gap-1">
                  <Bot size={12}/> DS Copilot
                </div>
              )}
              <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : 'prose-slate'}`}>
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // ... (existing components) ...
                    code({node, inline, className, children, ...props}: any) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline ? (
                        <div className="relative group my-4">
                          <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl overflow-x-auto font-mono text-xs border border-slate-800 shadow-inner">
                            <code className={className} {...props}>{children}</code>
                          </pre>
                        </div>
                      ) : (
                        <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded font-mono text-xs border border-gray-200" {...props}>{children}</code>
                      );
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
            </div>
            
            {/* IN-CHAT BLUEPRINT EDITOR (Only for the latest assistant message) */}
            {msg.role === 'assistant' && msg.updated_content?.blueprint && idx === chatHistory.length - 1 && activeBlueprint && (
              <div className="w-[90%] mt-3 bg-white border border-amber-200 rounded-xl shadow-lg overflow-hidden animate-in fade-in slide-in-from-top-2">
                <div className="bg-amber-50 px-4 py-2 border-b border-amber-100 flex justify-between items-center">
                  <span className="text-[10px] font-bold text-amber-700 uppercase flex items-center gap-2">
                    <Edit3 size={12}/> Editable Blueprint Plan
                  </span>
                  {blueprintError && <span className="text-[10px] text-red-600 font-bold flex items-center gap-1"><AlertTriangle size={10}/> {blueprintError}</span>}
                </div>
                <textarea 
                  value={activeBlueprint}
                  onChange={e => { setActiveBlueprint(e.target.value); setBlueprintError(null); }}
                  className="w-full h-64 p-4 font-mono text-xs text-slate-700 bg-slate-50 outline-none resize-none"
                />
                <div className="p-2 bg-gray-50 border-t flex justify-end gap-2">
                   <button onClick={() => setActiveBlueprint(JSON.stringify(msg.updated_content.blueprint, null, 2))} className="text-[10px] text-gray-500 hover:text-gray-800 px-3 py-1">Reset</button>
                   <button onClick={onSend} className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-1 rounded text-xs font-bold flex items-center gap-2">
                     <Check size={12}/> Confirm & Proceed
                   </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {isChatSending && <div className="flex justify-start"><div className="bg-white border px-4 py-2 rounded-xl animate-pulse text-xs text-gray-400">Thinking...</div></div>}
        <div ref={chatEndRef} />
      </div>
      <div className="p-4 bg-white border-t relative">
        <textarea 
          value={chatInput} 
          disabled={isChatSending}
          onChange={e => setChatInput(e.target.value)} 
          onKeyDown={e => e.key==='Enter' && !e.shiftKey && onSend()} 
          className="w-full bg-gray-100 rounded-xl p-3 pr-12 text-sm outline-none resize-none disabled:opacity-50" 
          rows={2} 
          placeholder={activeBlueprint ? "Type 'Confirmed' or edit the blueprint above..." : `Mode: ${copilotMode}...`}
        />
        <button 
          onClick={onSend} 
          disabled={isChatSending || !chatInput.trim()} 
          className="absolute right-6 bottom-6 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}

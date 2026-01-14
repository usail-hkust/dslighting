"use client";

import { MODULES, QUICK_PATHS } from '@/config/modules';
import { ModuleKey } from '@/types/modules';
import { ChevronRight, Zap } from 'lucide-react';

interface ModuleSelectorProps {
  taskId: string;
  onModuleSelect: (module: ModuleKey) => void;
  onQuickPathSelect?: (modules: ModuleKey[]) => void;
}

export default function ModuleSelector({ taskId, onModuleSelect, onQuickPathSelect }: ModuleSelectorProps) {
  const modules = Object.values(MODULES);

  const handleQuickPathClick = (pathModules: ModuleKey[]) => {
    if (onQuickPathSelect && pathModules.length > 0) {
      onQuickPathSelect(pathModules);
    } else {
      onModuleSelect(pathModules[0]);
    }
  };

  // 检查是否是 bike-sharing-demand 任务
  const isBikeSharingTask = taskId === 'bike-sharing-demand';
  const hasBikeSharingData = taskId && (taskId.includes('bike') || taskId.includes('sharing'));

  return (
    <div className="flex-1 flex flex-col items-center overflow-y-auto p-12 bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="w-full max-w-6xl py-4">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            DSLighting 你的个人数据科学助理
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            选择工作模式，每个模块完全独立，可以跳过任何步骤
          </p>

          {/* Feature Introduction */}
          <div className="max-w-3xl mx-auto mb-6 p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
              <div className="flex items-start gap-3">
                <div className="text-2xl">🔍</div>
                <div>
                  <div className="text-sm font-bold text-gray-900">智能数据探索</div>
                  <div className="text-xs text-gray-600">自动分析数据结构，生成可视化图表</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl">🤖</div>
                <div>
                  <div className="text-sm font-bold text-gray-900">AI 驱动分析</div>
                  <div className="text-xs text-gray-600">自然语言交互，自动生成分析代码</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="text-2xl">📊</div>
                <div>
                  <div className="text-sm font-bold text-gray-900">端到端工作流</div>
                  <div className="text-xs text-gray-600">从清洗到建模，一站式完成</div>
                </div>
              </div>
            </div>
          </div>

          {isBikeSharingTask && (
            <div className="inline-block px-4 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-bold animate-pulse">
              🎯 检测到经典案例数据集！推荐使用"体验示例"路径
            </div>
          )}
        </div>

        {/* Quick Paths */}
        <div className="mb-12">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Zap size={20} className="text-amber-500" />
            推荐路径
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_PATHS.map((path, index) => (
              <QuickPathCard
                key={index}
                path={path}
                onClick={() => handleQuickPathClick(path.modules)}
                isRecommended={isBikeSharingTask && index === 0}
              />
            ))}
          </div>
        </div>

        {/* All Modules */}
        <div>
          <h2 className="text-xl font-bold text-gray-800 mb-4">所有模块</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {modules.map((module) => (
              <ModuleCard
                key={module.key}
                module={module}
                onClick={() => onModuleSelect(module.key)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ModuleCard({ module, onClick }: { module: any; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`
        group relative p-6 rounded-2xl border-2 transition-all duration-200
        ${module.optional
          ? 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-lg'
          : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-xl'
        }
        text-left
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{module.icon}</span>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{module.title}</h3>
            {module.badge && (
              <span className={`
                inline-block mt-1 px-2 py-0.5 text-xs font-bold rounded
                ${module.badge === '热门' ? 'bg-purple-100 text-purple-700' :
                  module.badge === '核心' ? 'bg-green-100 text-green-700' :
                  module.badge === '独立' ? 'bg-amber-100 text-amber-700' :
                  'bg-gray-100 text-gray-600'}
              `}>
                {module.badge}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-gray-600 mb-4 leading-relaxed">
        {module.description}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        {module.optional ? (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            💡 可以跳过
          </span>
        ) : (
          <span className="text-xs text-gray-500">
            {module.whenToUse}
          </span>
        )}
        <span className="text-blue-600 text-sm font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          进入 <ChevronRight size={16} />
        </span>
      </div>
    </button>
  );
}

function QuickPathCard({ path, onClick, isRecommended }: { path: any; onClick: () => void; isRecommended?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`p-5 rounded-xl border-2 hover:shadow-lg transition-all duration-200 text-left ${
        isRecommended
          ? 'border-green-300 bg-green-50 hover:border-green-500 shadow-md'
          : 'border-amber-200 bg-amber-50 hover:border-amber-400'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{path.icon}</span>
        <h3 className="text-lg font-bold text-gray-900">{path.label}</h3>
        {isRecommended && (
          <span className="ml-auto px-2 py-1 bg-green-600 text-white text-xs font-bold rounded-full">
            推荐
          </span>
        )}
      </div>

      {/* Module Path */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {path.modules.map((moduleKey: string, idx: number) => {
          const module = Object.values(MODULES).find(m => m.key === moduleKey);
          return (
            <span
              key={moduleKey}
              className="px-2 py-1 text-xs font-medium rounded bg-white border border-gray-200"
            >
              {module?.icon} {module?.title}
              {idx < path.modules.length - 1 && ' →'}
            </span>
          );
        })}
      </div>

      <p className="text-sm text-gray-600">{path.description}</p>
    </button>
  );
}

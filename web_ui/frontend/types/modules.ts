/**
 * 模块化架构类型定义
 */

export type ModuleKey = 'prepare' | 'explore' | 'model' | 'report';

export interface ModuleConfig {
  key: ModuleKey;
  icon: string;
  title: string;
  description: string;
  optional: boolean;
  badge?: string;
  whenToUse: string;
  canSkip?: string;
  color: string;
}

export interface QuickPath {
  label: string;
  modules: ModuleKey[];
  description: string;
  icon: string;
}

export interface DataSourceConfig {
  id: 'raw' | 'processed';
  label: string;
  description: string;
  hint: string;
  icon: string;
}

export interface ChatSuggestion {
  label: string;
  prompt: string;
  icon?: string;
}

export interface ModuleWorkspaceProps {
  module: ModuleKey;
  taskId: string;
  onBack: () => void;
  onModuleChange?: (module: ModuleKey) => void;
}

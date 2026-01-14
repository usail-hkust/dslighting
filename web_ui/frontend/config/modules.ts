/**
 * 模块配置
 */

import { ModuleConfig, QuickPath, DataSourceConfig, ChatSuggestion } from '@/types/modules';

/**
 * 所有可用模块的配置
 */
export const MODULES: Record<string, ModuleConfig> = {
  prepare: {
    key: 'prepare',
    icon: '📊',
    title: '数据准备',
    description: '清洗、转换、标准化数据格式，生成 train/test/answer 文件',
    optional: true,
    badge: '可选',
    whenToUse: '当数据格式不规范，需要清洗或转换时',
    canSkip: '如果数据已经是标准的 CSV 格式（train/test/answer）',
    color: 'blue'
  },
  explore: {
    key: 'explore',
    icon: '🔬',
    title: '分析探索',
    description: '对话式数据探索、Python 代码执行、可视化生成',
    optional: false,
    badge: '热门',
    whenToUse: '任何情况下都可以使用，完全独立',
    color: 'purple'
  },
  model: {
    key: 'model',
    icon: '🤖',
    title: '模型训练',
    description: '选择工作流和模型，自动训练和评估',
    optional: false,
    badge: '核心',
    whenToUse: '准备好标准格式的数据后',
    color: 'green'
  },
  report: {
    key: 'report',
    icon: '📝',
    title: '报告生成',
    description: '生成技术报告，汇总分析结果和模型性能',
    optional: false,
    badge: '独立',
    whenToUse: '任何时候都可以生成报告',
    color: 'amber'
  }
};

/**
 * 推荐的工作路径
 */
export const QUICK_PATHS: QuickPath[] = [
  {
    label: '🎯 体验示例',
    modules: ['explore', 'model', 'report'],
    description: '使用 bike-sharing-demand 数据集体验完整的机器学习流程',
    icon: '🎯'
  },
  {
    label: '快速开始',
    modules: ['model', 'report'],
    description: '数据已经准备好了，直接开始训练模型',
    icon: '🚀'
  },
  {
    label: '深入分析',
    modules: ['explore', 'model', 'report'],
    description: '先进行数据探索和可视化，再训练模型',
    icon: '🔬'
  },
  {
    label: '完整流程',
    modules: ['prepare', 'explore', 'model', 'report'],
    description: '从原始数据开始，完整处理整个流程',
    icon: '🛠️'
  }
];

/**
 * 数据源配置
 */
export const DATA_SOURCES: DataSourceConfig[] = [
  {
    id: 'raw',
    label: '原始数据',
    description: 'Raw Data',
    hint: '使用上传的原始文件',
    icon: '📁'
  },
  {
    id: 'processed',
    label: '处理后数据',
    description: 'Processed Data',
    hint: '使用 EDA 清洗后的数据',
    icon: '✨'
  }
];

/**
 * 各模块的聊天建议
 */
export const CHAT_SUGGESTIONS: Record<string, ChatSuggestion[]> = {
  explore: [
    { label: '📊 查看数据统计', prompt: '请显示数据的基本统计信息，包括列名、数据类型、缺失值等' },
    { label: '🔍 检查数据质量', prompt: '请检查数据质量问题，包括缺失值、异常值、重复值等' },
    { label: '📈 生成可视化', prompt: '请生成数据可视化图表，展示数据分布和相关性' },
    { label: '🔗 相关性分析', prompt: '请进行相关性分析，展示特征之间的关系' },
    { label: '🔢 缺失值分析', prompt: '请分析缺失值的分布情况，并给出处理建议' },
    { label: '📉 特征分布', prompt: '请展示各特征的分布情况，包括数值型和类别型特征' },
    { label: '⚠️ 异常值检测', prompt: '请检测数据中的异常值，并用可视化展示' },
    { label: '📅 时间序列', prompt: '如果有时间列，请分析时间序列的趋势和周期性' },
    { label: '📋 分组统计', prompt: '请按类别特征进行分组统计，展示组间差异' },
    { label: '🔄 数据对比', prompt: '请对比不同特征或子集之间的统计差异' },
    { label: '💡 特征工程', prompt: '请基于数据分析，给出特征工程建议' },
    { label: '📊 目标变量', prompt: '请分析目标变量的分布，以及与特征的关系' }
  ],
  prepare: [
    { label: '📋 分析数据结构', prompt: '请分析当前数据的结构，告诉我要如何准备成标准格式' },
    { label: '🔧 生成清洗方案', prompt: '请生成数据清洗和转换的方案' },
    { label: '✨ 数据转换', prompt: '请帮我处理缺失值、异常值，并将数据转换为标准格式' },
    { label: '📂 文件分割', prompt: '请将数据分割成 train.csv, test.csv, test_answer.csv 三个文件' }
  ],
  model: [
    { label: '💡 推荐工作流', prompt: '根据这个数据集，推荐最适合的工作流和模型' },
    { label: '⚙️ 配置建议', prompt: '给出训练参数的配置建议' },
    { label: '🎯 模型对比', prompt: '请对比不同模型的性能，给出最优选择' },
    { label: '📈 性能优化', prompt: '请分析模型性能，给出优化建议' }
  ],
  report: [
    { label: '📄 生成技术报告', prompt: '请基于当前的所有分析结果，生成一份完整的技术报告' },
    { label: '📊 汇总关键发现', prompt: '请汇总所有关键发现和洞察' },
    { label: '📋 EDA 报告', prompt: '请生成一份探索性数据分析报告，包含所有可视化和统计结果' },
    { label: '🏆 模型总结', prompt: '请总结模型训练过程和最终结果' }
  ]
};

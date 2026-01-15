# 常见问题

这里是使用 DSLighting 时的常见问题和解决方案。

## 安装问题

### Q: Python 版本不兼容怎么办？

**A:** DSLighting 需要 Python 3.10 或更高版本。请检查你的 Python 版本：

\`\`\`bash
python --version
# 或
python3 --version
\`\`\`

如果版本不对，可以使用 [pyenv](https://github.com/pyenv/pyenv) 安装正确的版本：

\`\`\`bash
pyenv install 3.10.0
pyenv local 3.10.0
\`\`\`

### Q: pip 安装依赖失败？

**A:** 尝试以下方案：

1. 升级 pip：
\`\`\`bash
pip install --upgrade pip
\`\`\`

2. 使用 \`requirements_local.txt\`（不锁定版本）：
\`\`\`bash
pip install -r requirements_local.txt
\`\`\`

3. 使用国内镜像源：
\`\`\`bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
\`\`\`

## API 配置问题

### Q: 如何配置多个 LLM API？

**A:** 在 \`.env\` 文件中使用 \`LLM_MODEL_CONFIGS\`：

\`\`\`bash
LLM_MODEL_CONFIGS='[
  {"model": "gpt-4", "api_key": "key1", "api_base": "base1"},
  {"model": "claude-3", "api_key": "key2", "api_base": "base2"}
]'
\`\`\`

### Q: API 调用失败怎么办？

**A:** 检查以下几点：

1. API 密钥是否正确
2. API Base 地址是否正确
3. 网络连接是否正常
4. API 额度是否充足

## 数据准备问题

### Q: MLE-Bench 数据下载失败？

**A:** MLE-Bench 数据下载可能需要较长时间，请：

1. 确保网络连接稳定
2. 尝试使用代理
3. 分批下载数据集

### Q: 如何使用自己的数据集？

**A:** 参考[数据准备指南](/guide/data-preparation)，按照以下步骤：

1. 创建任务目录
2. 添加 \`config.yaml\`
3. 组织训练和测试数据
4. 运行任务

## 运行问题

### Q: 任务运行失败怎么办？

**A:** 检查日志文件：

\`\`\`bash
ls runs/benchmark_results/
\`\`\`

查看错误日志和输出信息，根据错误信息进行调整。

### Q: 如何提高任务执行速度？

**A:** 可以尝试：

1. 使用更快的 LLM 模型
2. 减少 max_iterations 或 max_steps
3. 增加 max_workers 参数
4. 使用 GPU 加速（如果支持）

## Web UI 问题

### Q: Web UI 无法连接后端？

**A:** 确保：

1. 后端服务正在运行
2. CORS 配置正确
3. 端口号没有被占用
4. 防火墙没有阻止连接

### Q: 如何部署 Web UI 到生产环境？

**A:** 参考 Web UI 的 README 文档，可以部署到：

- Vercel (前端)
- Railway/Render (后端)
- 自己的服务器

## 其他问题

### Q: 如何贡献代码？

**A:** 欢迎贡献！请查看：

1. [贡献指南](https://github.com/usail-hkust/dslighting/blob/main/docs/CONTRIBUTING.md)
2. 提交 Issue 讨论你的想法
3. 创建 Pull Request

### Q: 如何获取帮助？

**A:** 可以通过以下方式：

1. 查看[文档](/)
2. 提交 [GitHub Issue](https://github.com/usail-hkust/dslighting/issues)
3. 加入微信交流群

还有其他问题？欢迎在 [GitHub Discussions](https://github.com/usail-hkust/dslighting/discussions) 中提问！

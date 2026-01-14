# 快速启动指南

## 🚀 一键启动

### 启动后端（终端1）

```bash
# 1. 进入项目根目录
cd /path/to/dslighting

# 2. 激活虚拟环境
source dslighting/bin/activate

# 3. 进入后端目录
cd web_ui/backend

# 4. 启动后端
python main.py
```

✅ 看到 `Uvicorn running on http://0.0.0.0:8003` 表示成功

### 启动前端（终端2）

```bash
# 1. 进入项目根目录
cd /path/to/dslighting

# 2. 进入前端目录
cd web_ui/frontend

# 3. 启动前端
npm run dev
```

✅ 看到 `Ready in XXXms` 和 `Local: http://localhost:3000` 表示成功

### 访问应用

打开浏览器访问：http://localhost:3000

---

## 📋 前置要求

1. ✅ **Python 3.10 或更高版本**
   ```bash
   # 检查Python版本
   python3.10 --version
   # 或
   python --version
   ```
2. ✅ Python虚拟环境（dslighting）已激活
3. ✅ 后端依赖已安装：`pip install -r web_ui/backend/requirements.txt`
4. ✅ 前端依赖已安装：`npm install`（首次）

---

## 🔧 故障排除

### Python版本不满足要求

如果遇到Python版本相关的错误：

```bash
# 检查Python版本
python3.10 --version

# 如果版本低于3.10，需要安装Python 3.10+
# macOS: brew install python@3.10
# Ubuntu: sudo apt-get install python3.10
# Windows: 从 https://www.python.org/downloads/ 下载安装

# 使用特定Python版本创建虚拟环境
python3.10 -m venv dslighting
source dslighting/bin/activate
```

### 后端启动失败

```bash
# 检查虚拟环境
which python
# 应该指向: .../dslighting/bin/python

# 重新安装依赖
cd /path/to/dslighting
source dslighting/bin/activate
pip install -r web_ui/backend/requirements.txt
```

### 前端启动失败

```bash
# 清理并重装
cd /path/to/dslighting/web_ui/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 端口被占用

```bash
# 查找占用8003端口的进程
lsof -i :8003

# 杀死进程
kill -9 <PID>
```

---

## 📚 完整文档

- [主README](../README.md)
- [详细配置指南](../SETUP_GUIDE.md)
- [后端文档](backend/README.md)
- [前端文档](frontend/README.md)

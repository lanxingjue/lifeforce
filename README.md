# Lifeforce

Lifeforce 是一个多 Agent 协同的数字生命体项目，当前重点能力是对话、跨轮记忆和文件系统观察。

## 当前功能

- Orchestrator：对话与任务编排
- Observer：文件监控、变化记录、最近变更查询
- Executor：技能调度（Shell 执行、LLM 调用、记忆写入）
- 记忆系统 2.0：SQLite 本地记忆 + mem0 混合检索（主路径）+ 自动降级（兜底）
- 预算系统：按小时/天/月限制 token 消耗

## 环境要求

- Python 3.11+
- Windows / macOS / Linux（当前命令示例以 PowerShell 为主）

## 安装

```powershell
py -m pip install -e .
```

如果你使用 Poetry，也可以：

```powershell
poetry install
```

## 配置

### 1) 初始化配置文件

```powershell
py -m lifeforce.cli.main init
```

### 2) 配置 API Key

推荐在项目根目录放 `.env`：

```env
APIYI_API_KEY=sk-your-apiyi-key
```

项目会自动加载 `.env`，因此通常不需要每次手动设置环境变量。

也可以临时设置（PowerShell）：

```powershell
$env:APIYI_API_KEY="sk-your-apiyi-key"
```

### 3) 调整预算（可选）

编辑 `config.yaml` 中的：

```yaml
budget:
  hourly_limit: 50000
  daily_limit: 50000000
  monthly_limit: 50000000000
```

## 常用命令

### 对话与状态

```powershell
py -m lifeforce.cli.main chat "你好，Lifeforce"
py -m lifeforce.cli.main status
```

### 文件监控

启动监控（前台运行，`Ctrl+C` 停止）：

```powershell
py -m lifeforce.cli.main observe "C:\Users\wang\Documents\trae_projects\lifeForce"
```

查看最近文件变化：

```powershell
py -m lifeforce.cli.main observe-recent 20
```

## 记忆系统说明

- 主路径：mem0 + chroma + kuzu（日志会显示 `mode=primary`）
- 降级路径：当 mem0 初始化失败时，自动切换到本地 SQLite 检索（不中断功能）
- 你可以在日志中看到：
  - `mem0 initialized with provider=chroma+kuzu (mode=primary)`
  - 或 `初始化 mem0 失败，降级到本地模式: ...`

## 已知事项

- 当前 `typer/click` 在部分环境下执行 `--help` 可能报兼容错误，但不影响常用命令执行。
- 若出现 kuzu 文件锁冲突（`Could not set lock on file`），通常是多进程同时占用同一个 `data/kuzu_db`，关闭重复进程后重试即可。

## 开发与测试

运行测试：

```powershell
py -m pytest tests -q
```

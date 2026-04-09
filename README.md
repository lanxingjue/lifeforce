# Lifeforce

A digital life form MVP with multi-agent collaboration.

## Features

- Multi-agent roles (Orchestrator, Observer, Executor)
- Persistent memory system (SQLite)
- Budget guard for token usage
- CLI built with typer + rich

## Quick Start

### 1. Install

```bash
poetry install
```

### 2. Configure

```powershell
lifeforce init
$env:APIYI_API_KEY="sk-your-apiyi-key"
```

### 3. Run

```bash
lifeforce chat "hello"
lifeforce status
```

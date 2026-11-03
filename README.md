# Payal AI — Unified Autonomous AI Operating Environment

**Author & Creator:** Rishabh Raj ([@rishu7491](https://github.com/rishu7491))  
**License:** Private / Proprietary  
**Version:** 1.0.0-alpha  

---

## 🌟 Overview

**Payal** is an independent, sovereign personal AI operating environment engineered to combine high-performance local inference, multi-cloud model routing, autonomous planning, and safe sandboxed execution across Windows 11 and Kali/WSL environments.

---

## 🏗️ Core Architecture

```
payal/
├── core/
│   ├── identity/          # Agent soul, identity engine, and persona definitions
│   └── model_router/      # Cloud & local LLM router with fallback & health checking
├── execution/
│   ├── tools/             # Unified Tool Registry and schema validators
│   ├── windows/           # Windows PowerShell native execution adapter
│   └── linux/             # Kali Linux / WSL isolated execution adapter
├── services/
│   └── api/               # FastAPI async REST microservice & WebSocket channels
├── agents/                # Specialist agent personas & task definitions
├── commands/              # Automated slash command pipelines
├── skills/                # Extensive agent capability packages
├── rules/                 # Style, safety, and operational guardrails
├── schemas/               # JSON Schemas for validation and state contracts
├── tests/                 # Comprehensive Pytest unit and integration test suite
└── docs/                  # Architectural blueprints and engineering specs
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.11+
- Windows 11 / WSL2
- Node.js 18+ (for bridges)

### 2. Installation
```powershell
pip install -r requirements.txt # or install fastapi uvicorn pydantic pytest httpx
```

### 3. Run Payal Core API Service
```powershell
python -m uvicorn services.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Run Test Suite
```powershell
pytest -q
```

---

## 🔒 Security & Privacy
- Zero credential leakage.
- Policy-governed execution boundaries.
- Local-first inference optimization.

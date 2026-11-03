# PAYAL AI — MASTER TECHNICAL BLUEPRINT v2

**Project:** Payal AI  
**Product type:** Independent AI Agent + Unified IDE  
**Architecture:** Hybrid, modular, model-agnostic  
**Primary platform:** Windows 11  
**Secondary platform:** Kali Linux  
**Owner:** Rishu  
**Design:** Premium black, dark charcoal and crimson red

---

# 1. Product Vision

Payal will be an independent AI platform combining the strongest practical capabilities of:

- Antigravity — agent-driven development workflows.
- OpenClaw — tool integrations and agent infrastructure.
- Hermes — reusable skills and agent workflows.
- Codex — coding, debugging and verification.
- Cursor — contextual codebase understanding and AI-assisted editing.

Payal will not simply wrap these products.

It will have its own core engine, identity, memory, orchestration, permissions, execution system and unified interface.

External frameworks will be optional internal components.

**Fundamental principle:** Payal owns the intelligence orchestration and execution architecture. Frameworks and models are replaceable dependencies.

# 2. Core Architecture

```text
                    PAYAL AI
                       |
             UNIFIED IDE + AGENT UI
                       |
                 PAYAL CORE
                       |
     +-----------------+------------------+
     |                 |                  |
 Intelligence      Execution           Memory
     |                 |                  |
 Planner          Tool Router        Memory Engine
 Orchestrator     Permission Engine  Retrieval
 Agent Manager    Task Executor      Knowledge Store
 Model Router     Verification       Context Manager
     |                 |
     +-----------------+
                       |
               INTEGRATION LAYER
                       |
       +---------------+----------------+
       |               |                |
   Frameworks       Native Tools      Providers
   OpenClaw         File Engine       Ollama
   Hermes           Code Engine       llama.cpp
   Others           Browser Engine    Cloud APIs
```

## 2.1 Payal Core Engine

The independent core will own:

1. Identity and personality.
2. Conversation management.
3. Task planning and decomposition.
4. Agent orchestration.
5. Model selection and routing.
6. Memory and context management.
7. Tool selection.
8. Permission checking.
9. Execution coordination.
10. Result verification.
11. Error recovery.
12. Audit and event management.

No external framework should be allowed to bypass the core permission system.

# 3. Main System Modules

## A. Intelligence Engine

Responsibilities:

- Understand user requests.
- Maintain task context.
- Break complex tasks into subtasks.
- Select appropriate agents.
- Select local or cloud models.
- Evaluate results.
- Decide whether additional verification is needed.

## B. Model Router

Provider-independent interface.

Supported provider adapters:

- Ollama
- llama.cpp
- OpenAI-compatible APIs
- Groq-compatible APIs
- Other cloud providers

Capabilities:

- Local-first execution.
- Cloud fallback.
- Model capability selection.
- Context-window management.
- Token and latency tracking.
- Provider health checks.
- User-controlled privacy policies.

Changing an LLM must not require rebuilding Payal's core.

## C. Agent Manager

Initial logical agent roles:

| Agent | Responsibility |
|---|---|
| Master Agent | Overall coordination |
| Research Agent | Research and source analysis |
| Coding Agent | Code generation and editing |
| Review Agent | Code review and testing |
| Database Agent | SQL and database tasks |
| Browser Agent | Browser workflows |
| File Agent | File operations |
| System Agent | Approved system operations |
| Security Agent | Defensive security analysis |
| Memory Agent | Memory organization |

These are logical specialists. They can share model infrastructure rather than requiring ten simultaneously running LLMs.

## D. Memory Engine

Memory layers:

1. Working memory — current task.
2. Episodic memory — previous interactions and events.
3. Semantic memory — stable knowledge.
4. Personal memory — user-approved preferences.
5. Procedural memory — workflows and skills.
6. Project memory — project-specific context.

Every stored fact should support:

- Source and timestamp.
- Confidence level.
- Verified/unverified status.
- Project association.
- Sensitivity classification.
- Expiry or review policy.

Memory should be independent of the LLM provider and framework.

## E. Tool Execution Engine

Tool categories:

- Windows PowerShell adapter.
- Kali Linux adapter.
- Browser automation.
- Filesystem operations.
- Git and GitHub.
- Database connectors.
- Local application integrations.
- API integrations.

Every tool must have a defined schema, permissions, execution limits and result format.

Potentially destructive or security-sensitive operations must use controlled environments and explicit approval.

## F. Verification Engine

Payal must not report success just because an LLM says a task is complete.

Verification should include:

- Test execution.
- Output validation.
- File-change inspection.
- Error detection.
- Expected-versus-actual comparison.
- Completion status.
- Recovery or rollback where possible.

# 4. Unified IDE + AI Agent Workspace

The product will have one cohesive desktop workspace.

Main navigation:

1. Dashboard
2. AI Agent
3. Code Editor
4. Terminal
5. Browser
6. Files
7. Git & GitHub
8. Agents
9. Memory
10. Models
11. Database
12. Skills
13. Security & Approvals
14. Logs and Monitoring
15. Settings

### Main interface layout

```text
+------------------------------------------------------+
| PAYAL AI             Project       Model       Status |
+------------+----------------------+-----------------+
|            |                      |                 |
| Dashboard  |    CODE EDITOR       |   PAYAL AGENT   |
| Projects   |                      |                 |
| Files      |    Source Code       |   Conversation  |
| Agents     |                      |   Task Plan     |
| Browser    |                      |   Agent Status  |
| Database   |                      |   Approvals     |
| Memory     |                      |                 |
| Skills     |                      |                 |
| Settings   |                      |                 |
|            |                      |                 |
+------------+----------------------+-----------------+
|                    TERMINAL                         |
+------------------------------------------------------+
```

The layout should be resizable, customizable and responsive to laptop screen sizes.

# 5. Framework Integration Strategy

| Framework | Integration strategy |
|---|---|
| OpenClaw | Integrate useful agent and tool capabilities through controlled adapters |
| Hermes | Integrate reusable skill and workflow concepts |
| Antigravity | Independently develop equivalent agent-driven development workflows where feasible |
| Codex | Develop coding, testing and review capabilities |
| Cursor | Develop codebase indexing, contextual editing and code navigation |

Rules:

- Never make Payal dependent on one framework.
- Do not duplicate functionality unnecessarily.
- Prefer maintained open-source components when appropriate.
- Develop native alternatives where integration is unsuitable.
- Preserve a common internal interface for every integration.
- Verify licensing before adopting external code.

# 6. Recommended Technology Stack

| Layer | Recommended technology |
|---|---|
| Desktop application | Tauri |
| Frontend | React + TypeScript |
| UI styling | Tailwind CSS |
| Backend | Python + FastAPI |
| Real-time communication | WebSockets |
| Local database | SQLite |
| Future database | PostgreSQL |
| Vector retrieval | Qdrant or equivalent |
| Local inference | Ollama / llama.cpp |
| Browser automation | Playwright |
| Windows execution | PowerShell adapters |
| Linux execution | Controlled shell adapters |
| Container isolation | Docker |
| Testing | Pytest + frontend tests |
| Version control | Git + GitHub |

# 7. API and Internal Contracts

Core services communicate through stable internal interfaces:

```text
/api/v1/chat
/api/v1/tasks
/api/v1/agents
/api/v1/models
/api/v1/memory
/api/v1/tools
/api/v1/approvals
/api/v1/projects
/api/v1/files
/api/v1/git
/api/v1/skills
/api/v1/system
/api/v1/audit
```

Example task lifecycle:

```text
USER REQUEST -> REQUEST UNDERSTANDING -> TASK PLANNING -> PERMISSION CHECK -> AGENT DELEGATION -> TOOL EXECUTION -> RESULT VERIFICATION -> MEMORY UPDATE -> FINAL RESPONSE
```

# 8. Database Design

Initial SQLite entities: `users`, `projects`, `conversations`, `messages`, `tasks`, `subtasks`, `agents`, `models`, `memories`, `tools`, `permissions`, `approvals`, `skills`, `executions`, `audit_logs`.

# 9. Security and Autonomy

Permission levels:
- **Level 1 — Read-only:** Search files, read documents, analyze code, research web.
- **Level 2 — Reversible actions:** Create/edit project files, run approved tests, create branches.
- **Level 3 — Approval required:** Install software, change settings, execute privileged commands, external messaging.
- **Level 4 — Restricted operations:** Destructive system operations, policy modification. Denied by default.

# 10. Hardware and Model Strategy

Current development target:
- Ryzen 7 7445HS.
- RTX 3050 6GB VRAM.
- 16GB system RAM.
- Windows 11.
- Kali Linux VM.

Use intelligent model routing rather than running multiple heavy models simultaneously.

# 11. Repository Structure

Full modular tree rooted at `payal/`.

# 12. Development Roadmap

- Phase 0: Existing Environment Audit
- Phase 1: Payal Core
- Phase 2: Intelligence and Orchestration
- Phase 3: Memory
- Phase 4: Execution and Security
- Phase 5: Development Engine
- Phase 6: System Integrations
- Phase 7: Advanced Agents
- Phase 8: Unified Desktop Workspace
- Phase 9: Advanced Capabilities

# 13. Non-Negotiable Design Principles

1. Payal's core must remain independent.
2. Frameworks are tools, not the platform.
3. Models must be replaceable.
4. Memory must survive model changes.
5. All important actions must be auditable.
6. Security must be enforced outside the LLM.
7. Verification must precede success claims.
8. Integrations must be modular.
9. The interface must remain unified.
10. Development must be incremental and test-driven.


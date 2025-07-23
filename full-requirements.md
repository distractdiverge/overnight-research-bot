Overnight Research Bot – Requirements Document

1  Purpose & Goal

Design and implement an autonomous, overnight research utility that runs on a single Apple Silicon MacBook Pro (M3 Pro · 36 GB RAM).  The bot should:
	•	Harvest web information on a specified topic each night
	•	Summarise findings, propose next‑step questions, and persist state
	•	Wake the user each morning with a digest the next agent can extend

2  Scope
	•	Local execution on the user’s laptop (no cloud dependency required, but remote GPU fallback optional)
	•	Target models ≤ 7 B parameters (quantised or FP16)
	•	Single‑user, single‑topic run per night; multi‑topic batching considered future work

3  System Context & Actors
	•	Primary user – user (developer/owner) – schedules and reviews output.
	•	Research Bot – Python service orchestrated by launchd.
	•	LLM Backend – LM Studio (MLX engine) REST API or in‑process mlx‑lm; remote Ollama server optional.
	•	Vector DB – Chroma (local SQLite backend).
	•	External Web – DuckDuckGo / SerpAPI or equivalent search endpoint.

graph TD
  subgraph Laptop (macOS 14)
    SCHED(launchd + caffeinate)
    ORCH[Orchestrator.py]
    VDB[(Chroma / SQLite)]
    LMSTUDIO[LM Studio server → MLX]
  end
  USER[Morning Reviewer]
  WEB[Search API]

  SCHED → ORCH
  ORCH  → LMSTUDIO
  ORCH  → WEB
  ORCH  → VDB
  ORCH  → USER

4  Functional Requirements

 ID 	Requirement
 F‑1 	The system runs unattended for ≥ 6 h via launchd nightly at 23:00 local time.
 F‑2 	Accept command‑line topic or use environment variable RESEARCH_TOPIC.
 F‑3 	For each iteration: search → summarise → propose sub‑questions → store.
 F‑4 	Persist summaries & metadata to Chroma for incremental, resumable runs.
 F‑5 	On completion write markdown/plain‑text digest to ~/logs/research.log.
 F‑6 	Support two LLM back‑ends selectable via USE_LMSTUDIO env flag.
 F‑7 	Gracefully fallback to remote Ollama by honouring OPENAI_BASE_URL.
 F‑8 	Provide Mermaid system & sequence diagrams and sample code scaffolding.

5  Technical Requirements

5.1  Hardware & OS
	•	macOS 14.x on MacBook Pro (Apple M3 Pro, 36 GB RAM)

5.2  Programming & Runtime
	•	Python ≥ 3.11 (asyncio standard library)
	•	Packages: openai>=1.30, mlx‑lm, duckduckgo_search, chromadb, tqdm
	•	Code style: Black‑formatted, type‑annotated (PEP 484).

5.3  LLM Models & Inference

Model ID	Params	Quant	RAM‑footprint	Expected tok/s (M3 Pro)
 phi‑3‑mini‑4k‑instr 	 3.8 B 	 Q4_K_M 	 ≈ 4 GB 	 ≈ 25 t/s 
 gemma‑7b‑it‑q4 	 7 B 	 Q4 	 ≈ 6 GB 	 ≈ 16–18 t/s 
 mistral‑7b‑instr‑q4 	 7 B 	 Q4 	 ≈ 6 GB 	 ≈ 15 t/s 

	•	Default back‑end: LM Studio (MLX engine) on‑device GPU via Metal.
	•	Enable Speculative Decoding & cap max context = 4096 tokens.

5.4  Scheduling & Runtime Control
	•	launchd plist (stored in ~/Library/LaunchAgents/com.researchbot.overnight.plist).
	•	Wrap command with caffeinate ‑i to prevent sleep.

5.5  Environment Variables

Name	Purpose	Example
 USE_LMSTUDIO 	 1 to call LM Studio REST; unset → local mlx‑lm.	 1
 MODEL 	Model alias to request.	 phi‑3‑mini
 OPENAI_BASE_URL 	Override to remote Ollama server.	 http://192.168.1.42:11434/v1
 RESEARCH_TOPIC 	Default nightly topic.	 LLM privacy techniques

5.6  Data Storage & Format
	•	Chroma persistent store at ~/ai/chromadb_store (SQLite default).
	•	Document schema: {id, t: ISO datetime, topic: str, summary: str}.
	•	Logs: plain‑text in ~/logs/research.log and error in research.err.

5.7  Sequence Diagram

sequenceDiagram
    participant Cron as launchd
    participant Bot as Orchestrator
    participant LM as LM Studio/MLX
    participant Web as Search API
    participant DB as Chroma

    Cron->>Bot: start(topic)
    Bot->>Web: search(k=10)
    Web-->>Bot: snippets[]
    Bot->>LM: summarise + plan
    LM-->>Bot: summary, tasks
    Bot->>DB: upsert()
    Bot-->>Cron: exit

6  Non‑Functional Requirements

 ID 	Requirement
 NF‑1 	Performance – Process 10 web snippets and summarise within 5 min/iteration on phi‑3‑mini.
 NF‑2 	Thermals/Energy – Draw ≤ 30 W average; utilise GPU not CPU cores > 50 %.
 NF‑3 	Reliability – Resume on unexpected shutdown using saved Chroma state.
 NF‑4 	Maintainability – 100 % typed code; CI lint+black; README with setup steps.
 NF‑5 	Licensing – Use only Apache‑2 or MIT licensed libraries/models.
 NF‑6 	Security – No PII sent off‑device; API keys stored in Keychain or .env.
 NF‑7 	Extensibility – Modular back‑end (easily swap to CUDA server); plug‑in multi‑agent planners.

7  Constraints & Assumptions
	•	Laptop remains on AC power overnight with 80 % charge‑limit enabled.
	•	Internet connectivity available for search API.
	•	Topics fit in ≤ 4096 tokens context after concatenation.

8  Acceptance Criteria & Test Plan
	•	Smoke test – python orchestrator.py "test" summarises example snippets in < 3 min.
	•	Overnight test – launchd job writes ≥ 1 KB digest and persists ≥ 1 entry in Chroma.
	•	Back‑end swap – Setting USE_LMSTUDIO=0 runs identical job via in‑process mlx‑lm.
	•	Remote swap – Setting OPENAI_BASE_URL to a remote Ollama returns coherent output.

9  Deliverables
	1.	orchestrator.py (main service)
	2.	requirements.txt / pyproject.toml
	3.	com.user.researchbot.plist
	4.	README.md with setup, model download, and troubleshooting
	5.	Mermaid diagrams (embedded in README)

10  Future Enhancements (Backlog)
	•	Multi‑topic queue and dynamic priority.
	•	Morning email or iMessage digest via AppleScript.
	•	Fine‑tune pipeline (LoRA) triggered on weekends.
	•	Web UI dashboard (Flask + HTMX) for browsing Chroma memory.
	•	Integration with windsurf status‑check endpoint to publish latest build/hash.

⸻

Document prepared 2025‑07‑23 for hand‑off to next AI agent.
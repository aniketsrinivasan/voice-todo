### High-level goals
- Build a backend that supports manual and voice-driven to-do CRUD, plus agentic workflows for query/edit/delete via natural language.
- Use `Supabase` for persistence; expose a `FastAPI` service; wrap LLM and Whisper; encapsulate DB access and business logic via clear abstractions.

### Architectural overview
- **API layer (FastAPI)**: REST endpoints for `todos`, `categories`, `voice`, and `agent`.
- **Service layer**: Orchestrates business logic (validation, permissions, transactions).
- **Repository layer (Supabase DAL)**: Typed data access; hides Supabase queries and RPCs.
- **Agentic layer (`agent.py`)**: LLM-driven tool-execution using tools under `mcp_tools/`.
- **LLM wrapper (`llm.py`)**: Abstract LLM client behind an interface.
- **Voice wrapper (`voice.py`)**: Abstraction over Whisper for transcription.
- **Schemas (`schemas.py`)**: Pydantic models for API I/O contracts.

---

### Data model (Supabase)
- **users**
  - id (uuid, PK)
  - email (text, unique)
  - created_at (timestamptz, default now)

- **todos**
  - id (uuid, PK)
  - user_id (uuid, FK -> users.id, indexed)
  - description (text, indexed with FTS)
  - priority (text enum: low|med|high, indexed)
  - due_at (timestamptz, nullable, indexed)
  - created_at (timestamptz, default now)
  - updated_at (timestamptz, default now)
  - metadata (jsonb)
  - transcription_id (uuid, FK -> voice_transcripts.id, nullable)

- **categories**
  - id (uuid, PK)
  - user_id (uuid, FK -> users.id, indexed)
  - name (text, unique per user, indexed)
  - created_at (timestamptz, default now)

- **todo_categories** (many-to-many)
  - todo_id (uuid, FK -> todos.id, indexed)
  - category_id (uuid, FK -> categories.id, indexed)
  - PK (todo_id, category_id)

- **voice_transcripts**
  - id (uuid, PK)
  - user_id (uuid, FK -> users.id, indexed)
  - audio_uri (text)  // Supabase storage path
  - text (text)
  - language (text, nullable)
  - created_at (timestamptz, default now)
  - status (text enum: pending|done|failed)
  - error (text, nullable)
  - metadata (jsonb)

- **audit_logs** (optional, useful for agentic ops)
  - id (uuid, PK)
  - user_id (uuid, FK -> users.id, indexed)
  - action (text) // create_todo, edit_todo, delete_todo, query_todos
  - payload (jsonb) // input/output snapshot
  - created_at (timestamptz, default now)

- **Indexes/FTS**
  - GIN index on `todos.metadata`
  - FTS index on `todos.description` (e.g., tsvector column + GIN)
  - B-tree indexes on `todos.user_id`, `todos.due_at`, `todos.priority`, `categories.name`

---

### Pydantic schemas plan (`schemas.py`)
- **TodoBase**
  - description: str
  - priority: Literal["low","med","high"]
  - due_at: Optional[datetime]
  - categories: Optional[list[str]]  // names for create/update
  - metadata: Optional[dict[str, Any]]

- **TodoCreate(TodoBase)**
  - required: description

- **TodoUpdate**
  - description: Optional[str]
  - priority: Optional[Literal["low","med","high"]]
  - due_at: Optional[datetime | None]
  - categories: Optional[list[str]]
  - metadata: Optional[dict[str, Any]]

- **TodoOut**
  - id: UUID
  - user_id: UUID
  - transcription_id: Optional[UUID]
  - created_at: datetime
  - updated_at: datetime
  - inherits fields from `TodoBase`

- **CategoryCreate**
  - name: str

- **CategoryOut**
  - id: UUID
  - name: str
  - created_at: datetime

- **TranscriptCreate**
  - audio_uri: str
  - language: Optional[str]

- **TranscriptOut**
  - id: UUID
  - status: Literal["pending","done","failed"]
  - text: Optional[str]
  - error: Optional[str]
  - created_at: datetime

- **AgentQuery**
  - prompt: str
  - mode: Literal["query","create","edit","delete"]  // hints; agent can still decide
  - context: Optional[dict[str, Any]]

- **AgentResult**
  - message: str
  - changes: Optional[list[dict[str, Any]]]  // normalized summary of DB ops
  - data: Optional[dict[str, Any]]  // e.g., query results

---

### Abstractions and interfaces
- **LLM client (`llm.py`)**
  - `LLMClient` protocol:
    - `generate(messages: list[dict], tools: Optional[list]=None, tool_choice: Optional[str]=None) -> dict`
  - Concrete: `OpenAILLMClient`

- **Speech-to-text (`voice.py`)**
  - `SpeechToTextClient` protocol:
    - `transcribe(audio_uri: str, language: Optional[str]) -> TranscriptOut`
  - Concrete: `WhisperClient`

- **Repositories (Supabase DAL)**
  - `TodosRepository`
    - `create(user_id, TodoCreate) -> TodoOut`
    - `get(user_id, todo_id) -> TodoOut`
    - `list(user_id, filters) -> list[TodoOut]`
    - `update(user_id, todo_id, TodoUpdate) -> TodoOut`
    - `delete(user_id, todo_id) -> None`
    - `attach_categories(user_id, todo_id, category_names: list[str])`
  - `CategoriesRepository`
    - `ensure_many(user_id, names: list[str]) -> list[CategoryOut]`
    - `list(user_id) -> list[CategoryOut]`
  - `TranscriptsRepository`
    - `create_pending(user_id, audio_uri, language) -> TranscriptOut`
    - `mark_done(id, text, metadata) -> TranscriptOut`
    - `mark_failed(id, error) -> TranscriptOut`
    - `get(id) -> TranscriptOut`
  - `AuditRepository`
    - `record(user_id, action, payload)`

- **Services**
  - `TodosService`
    - validates input, orchestrates repo calls and category joins
    - search utilities (FTS queries, date windows like “due this week”)
  - `VoiceService`
    - handles transcript job lifecycle; calls `SpeechToTextClient`; updates `voice_transcripts`
  - `AgentService`
    - configures `agent.py`, registers tools, runs agent loop, records audit logs

- **Agent tools (`microservices/agentic/mcp_tools`)**
  - `QueryTodosTool`: input filters (date window, priority, category, FTS string), returns list of todos
  - `CreateTodoTool`: input `TodoCreate`, returns created todo
  - `EditTodoTool`: input identifiers (by id or fuzzy match via FTS) + `TodoUpdate`, returns updated todo(s)
  - `DeleteTodoTool`: input identifier(s), returns count
  - `ExplainTool` (optional): turns raw results into user-facing summaries

---

### API design (FastAPI)
- **Auth**: placeholder dependency that yields `user_id` (JWT later via Supabase Auth or custom). Keep interfaces accepting `user_id`.
- **Routes**
  - `POST /todos` -> create
  - `GET /todos` -> list with filters: `q`, `priority`, `category`, `due_before`, `due_after`, `limit`, `offset`
  - `GET /todos/{id}` -> get
  - `PATCH /todos/{id}` -> update
  - `DELETE /todos/{id}` -> delete
  - `GET /categories` -> list
  - `POST /categories` -> create
  - `POST /voice/transcripts` -> submit audio URI; returns transcript id (status pending)
  - `GET /voice/transcripts/{id}` -> poll transcript status/result
  - `POST /agent/execute` -> natural language input; returns `AgentResult`
- **Error model**
  - Standard problem+json shape: `code`, `message`, `details`

---

### Core flows
- **Create to-do via voice**
  - Client uploads audio to storage → obtains `audio_uri`
  - `POST /voice/transcripts` creates pending record → background task calls Whisper → `mark_done` with text
  - Client polls transcript → `POST /agent/execute` with text and mode `create`
  - Agent uses `CreateTodoTool`; response returned to client; `audit_logs` recorded

- **Query via voice (“what’s due this week?”)**
  - Transcribe → `POST /agent/execute` with mode `query`
  - Agent chooses `QueryTodosTool` → service builds filters → returns structured list + summary

- **Edit via voice (“move laundry to tomorrow”)**
  - Transcribe → `POST /agent/execute` with mode `edit`
  - Agent finds candidate todos (FTS + category heuristics) → disambiguates if multiple → applies `EditTodoTool`

- **Manual CRUD**
  - Direct `todos` and `categories` endpoints

---

### Implementation plan (step-by-step)
1. **Project scaffolding**
   - Set up `FastAPI` app structure: `backend/src` with `api`, `services`, `repositories`, `models`, `config`, `microservices`.
   - Load env (Supabase URL/key, OpenAI keys) via `pydantic-settings`.

2. **Database schema in Supabase**
   - Create tables and indexes listed above.
   - Create policies for row-level security (scoped by `user_id`).
   - Enable FTS on `todos.description`.

3. **Schemas (`schemas.py`)**
   - Add Pydantic models for I/O as listed.

4. **Supabase client and repositories**
   - Initialize Supabase client once (singleton/factory).
   - Implement `TodosRepository`, `CategoriesRepository`, `TranscriptsRepository`, `AuditRepository`.
   - Include typed mapping from Supabase records to Pydantic models.

5. **Service layer**
   - `TodosService`: implement create, list (with filters), get, update, delete, attach categories, FTS helpers, “due this week” helper.
   - `VoiceService`: implement transcript lifecycle; run transcription in background task; handle errors/timeouts.
   - `AgentService`: orchestrate agent, tools, and audit logging.

6. **LLM and Voice wrappers**
   - `OpenAILLMClient` in `llm.py` with a minimal `generate` interface supporting tool-calls.
   - `WhisperClient` in `voice.py` to transcribe given `audio_uri`.

7. **Agent and tools**
   - In `agent.py`, bootstrap the agent, register tools from `mcp_tools/`.
   - Implement tools thinly; each calls into services, never repos directly.
   - Add tool input/output schemas for validation.

8. **API endpoints (FastAPI)**
   - Wire routes to services.
   - Add auth dependency that resolves a `user_id` (stub for now).
   - Integrate background tasks for transcription.

9. **Validation, errors, and logging**
   - Consistent exceptions in services; translate to HTTP errors.
   - Structured logging; include `user_id` and request id.
   - Record `audit_logs` for agent operations.

10. **Testing**
    - Unit tests for repositories (can mock Supabase), services, and tools.
    - E2E tests for CRUD and agent flows with a fake LLM and fake STT.
    - Contract tests for API schemas.

11. **Observability and performance**
    - Add metrics (request latency, transcription time).
    - Index review; paginate lists; cap result sizes.

12. **Security hardening (phase 2)**
    - Integrate Supabase Auth or JWT verification dependency.
    - Enforce RLS policies end-to-end.
    - Rate limiting on `agent/execute` and `voice/transcripts`.

---

### Component interactions
- **API ↔ Services**: Endpoints perform input validation, call the service, translate service exceptions to HTTP.
- **Services ↔ Repos**: Services compose multiple repo calls; repos perform single-table concerns.
- **Agent ↔ Tools ↔ Services**: Agent chooses tools; tools call services with validated inputs; services update DB; results return upward.
- **Voice**: API kicks off background transcription; on completion, services update transcript and link to todos when applicable.

---

### Conventions and practices
- **Docstrings**: Google style for non-trivial functions/classes.
- **Comments**: Only where loops/logic are non-trivial; brief and ready-to-ship.
- **Reuse**: Centralize Supabase client and mappers; services reuse repo helpers; tools reuse services.

---

### Acceptance criteria
- Manual CRUD flows work with validation and pagination.
- Voice upload → transcription → agent create/query/edit flows work end-to-end.
- Agent tools can query, create, edit, delete todos scoped to a `user_id`.
- Categories can be created and associated; many-to-many enforced.
- FTS works for description search; “due this week” queries return correct results.
- API documented via OpenAPI; unit and E2E tests passing.

- Implement next: initialize the DAL and services skeletons, then wire the simplest endpoint (`POST /todos`) before adding voice/agent layers.
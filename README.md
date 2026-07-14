# AI-First HCP CRM — Log Interaction Screen

A "Log Interaction" screen for pharma field reps that supports **two logging modes**:
a traditional structured form, and a **conversational chat interface** backed by a
**LangGraph** agent running on **Groq** (`gemma2-9b-it`, with `llama-3.3-70b-versatile`
as a fallback/deeper-reasoning model).

Built with: React + Redux (frontend), FastAPI (backend), LangGraph + Groq (AI agent),
SQLAlchemy over Postgres/MySQL/SQLite (database), Google Inter (font).

---

## 1. What this project is

Field reps currently log HCP interactions by filling out forms after every visit —
slow, and details get lost. This project lets a rep either:

1. **Fill the structured form** (interaction type, products, sentiment, samples, etc.), or
2. **Just talk to "Nova"**, the in-app AI assistant — e.g. *"Just met Dr. Rao, discussed
   CardioFlex 10mg dosing, she was positive and I dropped 5 samples. Follow up in 2 weeks."*
   — and have the agent extract the structured record, save it, run a compliance check,
   and confirm back in plain language.

Both paths write to the same `interactions` table, so the history list below works
identically regardless of which mode was used to log an entry.

---

## 2. Role of the LangGraph agent

The agent ("Nova") is the reasoning layer that sits between a rep's unstructured,
conversational language and the CRM's structured data model. Concretely, it:

- **Interprets intent** — decides whether the rep is logging a new interaction, editing
  an old one, asking for history/context, asking what to do next, or just chatting.
- **Extracts structure from free text** — turns a rushed, informal note into the same
  fields the structured form would have collected (interaction type, products, topics,
  sentiment, samples, key takeaways, next steps), using the LLM as an extraction engine.
- **Calls tools, not just text** — rather than only generating a reply, the agent decides
  *which backend action* to take (log, edit, fetch history, schedule a follow-up, check
  compliance, recommend next steps) and with what arguments, then uses the tool's result
  to compose its next message. This is the core LangGraph pattern used here: an
  `agent` node (LLM bound to tools) and a `tools` node (executes them), looping until the
  model responds without requesting another tool call.
- **Keeps a human in the loop** — it always confirms back what it logged/changed in plain
  language, and every automated edit is captured in an `edit_history` audit trail rather
  than silently overwriting data.
- **Stays compliance-aware** — after logging, it proactively runs a compliance check and
  surfaces anything that looks like an off-label or unsubstantiated claim, or an
  oversized sample drop, for MLR review — rather than letting risky language slip into
  the CRM silently.

See `backend/app/agent/graph.py` for the graph definition and
`backend/app/agent/tools.py` for the tool implementations.

### The 5 (+1) tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | **`log_interaction`** *(required)* | Takes the rep's raw free-text note + `hcp_id`. Sends it to the Groq LLM with a structured-extraction prompt that returns JSON: interaction type, products discussed, topics, sentiment, samples dropped, key takeaways, next steps, and a short professional summary. Persists this as a new `Interaction` row and returns its id so later turns (e.g. an edit) can reference it. |
| 2 | **`edit_interaction`** *(required)* | Takes an `interaction_id` and a natural-language description of the change (e.g. *"change sentiment to Positive and add that 5 samples of Drug A were dropped"*). The LLM is given the current record as JSON and asked to return the full updated record. Before overwriting, the previous version is appended to `edit_history` (a JSON audit trail) so nothing is lost. |
| 3 | **`get_hcp_history`** | Pulls the N most recent past interactions for an HCP, so the agent has context (e.g. rep says *"same as last time"*) before logging or recommending. |
| 4 | **`schedule_follow_up`** | Sets/updates the `follow_up_date` (and an optional note) on a logged interaction — powers the rep's task list. |
| 5 | **`check_compliance`** | Runs an LLM-based check over the interaction content for off-label promotion, unsubstantiated claims, or excessive sample quantities; sets `compliance_flag` + `compliance_notes` for MLR review. Called automatically after every `log_interaction`, and also available from the structured-form path. |
| 6 | **`suggest_next_best_action`** *(bonus, 6th tool)* | Given an HCP's interaction history, asks the LLM for 2–3 concrete talking points / product focus for the *next* visit — a lightweight "next best action" recommendation. |

All 6 tools are plain `@tool`-decorated Python functions (LangChain tool spec) bound to
the Groq model inside the LangGraph `agent` node, and executed by a `ToolNode` in the
`tools` node. The structured-form submission path also calls `check_compliance` directly
(same tool, no chat required), so both logging modes share the exact same compliance logic.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18 + Redux Toolkit |
| Backend | Python 3.11 + FastAPI |
| AI agent framework | LangGraph |
| LLM | Groq `gemma2-9b-it` (primary), `llama-3.3-70b-versatile` (fallback) |
| Database | SQLAlchemy ORM — Postgres or MySQL in production, SQLite by default for zero-setup local runs |
| Font | Google Inter |

---

## 4. Project structure

```
hcp-crm-ai/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   ├── config.py          # env-based settings (Groq key/model, DB url)
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # HCP, Interaction, ChatSession tables
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── agent/
│   │   │   ├── llm.py         # Groq client wrapper (primary + fallback model)
│   │   │   ├── tools.py       # the 6 LangGraph tools
│   │   │   └── graph.py       # LangGraph StateGraph (agent + tools nodes)
│   │   └── routers/
│   │       ├── hcp.py         # HCP CRUD
│   │       ├── interactions.py# structured-form logging + edit + delete
│   │       └── chat.py        # conversational logging (invokes the agent graph)
│   ├── seed.py                 # creates 3 demo HCPs
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── LogInteractionScreen.jsx  # HCP sidebar + form/chat tab switch
    │   │   ├── StructuredForm.jsx        # the structured logging form
    │   │   ├── ChatInterface.jsx         # chat UI talking to Nova
    │   │   └── InteractionList.jsx       # history + inline edit
    │   ├── store/
    │   │   ├── store.js
    │   │   ├── interactionSlice.js       # HCPs + interactions (Redux Toolkit + thunks)
    │   │   └── chatSlice.js              # chat session + messages
    │   ├── api/api.js                    # axios client
    │   └── styles/index.css
    └── package.json
```

---

## 5. How to run it

### 5.1 Get a Groq API key

1. Go to <https://console.groq.com>, sign in, open **API Keys**, and create a new key.
2. You'll paste this into `backend/.env` as `GROQ_API_KEY` below.

### 5.2 Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GROQ_API_KEY=your_key_here

python seed.py                  # creates 3 demo HCPs
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

**To use Postgres or MySQL instead of the default SQLite**, set `DATABASE_URL` in
`.env` before running `seed.py`, e.g.:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/hcp_crm
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/hcp_crm
```

### 5.3 Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # defaults to http://localhost:8000, adjust if needed
npm start
```

Opens at `http://localhost:3000`.

### 5.4 Try it

- Pick an HCP from the left sidebar.
- **Structured Form** tab: fill fields, click **Log Interaction**.
- **Chat with Nova** tab: type something like *"Met Dr. Nair virtually, talked about
  GlucoBalance side effects, he seemed neutral, no samples this time, follow up on the
  15th."* — watch it get parsed, saved, and confirmed, with tool-call tags shown under
  the agent's reply.
- Scroll down to **Interaction History** to see the logged entry, edit it inline, or
  delete it.

---

## 6. Notes / assumptions

- SQLite is the default DB so graders can run this with zero external setup; swapping
  to Postgres/MySQL is a one-line env var change (see 5.2).
- The Groq model is called with `temperature=0.2` and asked to return strict JSON for
  extraction/compliance tasks; a fallback call to `llama-3.3-70b-versatile` is attempted
  once if the primary model's output fails to parse.
- Compliance flagging here is a simple LLM-based heuristic for demo purposes, not a
  substitute for a real MLR review process.

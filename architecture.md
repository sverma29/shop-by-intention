# SHOP-BY-INTENTION Architecture

## System Overview

Shop-By-Intention is an agentic AI e-commerce backend built with a multi-agent orchestrated loop. Rather than simple keyword search, the system uses chained LLM agents to parse natural language intentions, retrieve relevant products using semantic vector similarity, logically evaluate combinations of products within budgetary constraints, and autonomously build optimized shopping carts.

## Technology Stack

*   **Backend Framework:** FastAPI (Python)
*   **AI Engine:** Groq API (Llama models)
*   **Vector Search:** `sentence-transformers` for local embeddings and in-memory cosine similarity search (scaling to FAISS/ChromaDB).
*   **Tracing & Telemetry:** Custom thread-local event logging to `jsonl` files for full observability.

---

## Directory Structure

```text
shop-by-intention/
├── api/             # FastAPI Application Layer
│   ├── routes/      # HTTP Endpoints (e.g., /api/v1/shop)
│   └── services/    # Business Logic Orchestration (ShopService)
├── config/          # Centralized Configurations
│   └── taxonomy.json# Predefined canonical boundaries (Categories, Purposes, Preferences)
├── core/            # The Agentic AI Engine
│   ├── agents/      # Specialized LLM Agents
│   ├── ai/          # Groq API Client and Semantic Models
│   ├── events/      # Telemetry, Trace IDs, and Logging
│   └── loops/       # The Agentic Orchestrator and State Machine
├── data/            # Local Databases and Mocks
│   ├── product_catalog.json # E-commerce Inventory
│   ├── benchmark_queries.json # Test Suite
│   └── event_logs.jsonl # Trace History
├── frontend/        # Simple HTML/JS interface
└── update_tax.py    # Utility scripts
```

---

## The Multi-Agent Loop

The core processing logic lives inside `api/services/shop_service.py` via the `process_query` method. The system runs a `while` loop bound by a `max_loops` threshold. 

During each iteration, the query state passes through a pipeline of specialized AI agents:

### 1. Intent Agent (`core/agents/intent_agent.py`)
*   **Goal:** Translates raw unstructured text into a structured JSON configuration.
*   **Taxonomy Limits:** Ingests bounding lists from `config/taxonomy.json` (Category, Purpose, Budget, Preferences) and fiercely enforces that the LLM only selects known canonical variables to prevent hallucination.

### 2. Retrieval Agent (`core/agents/retrieval_agent.py`)
*   **Goal:** Searches the `product_catalog` based on the structured intent.
*   **Methodology:** Combines exact-match filtering (for explicit Category mappings) with Semantic Vector Search (Cosine Similarity against target features/purposes using `sentence-transformers`) to rank and fetch the top N candidates.

### 3. Reasoning Agent (`core/agents/reasoning_agent.py`)
*   **Goal:** Acts as the logical brain evaluating the retrieved candidates.
*   **Responsibility:** It looks at the user's intent, the budget, and the returned products. It assesses which combinations of products make the most sense, rejecting overpriced items or incompatible choices. It returns a scored list of the *best* choices.

### 4. Cart Agent (`core/agents/cart_agent.py`)
*   **Goal:** Mutates the global Cart State.
*   **Responsibility:** Takes the top-ranked suggestions from the Reasoning Agent and attempts to "purchase" them. It checks if adding an item violates the structural budget limits. 

### 5. Evaluation Agent (`core/agents/evaluation_agent.py`)
*   **Goal:** A quality-assurance critic.
*   **Responsibility:** It reviews the current state of the built Cart against the user's original Intent. Did we fulfill the request? Did we stay under budget? Is anything missing? It outputs a boolean `should_continue`.

### 6. Loop Controller (`core/loops/loop_controller.py`)
*   **Goal:** Determines the next step of the state machine.
*   **Responsibility:** If the Evaluation Agent signals the cart is incomplete (e.g., User asked for a "setup" and we only bought a chair, forgetting the desk), the Controller triggers the loop to restart. It might issue an action like `"refine_intent"`, causing the Intent Agent to run again with updated context, fetching the missing items on the next pass.

---

## Observability & Telemetry

Every decision made by every agent in the pipeline is recorded as an `AgenticEvent` (`core/events/event_model.py`).

To trace a single HTTP request coherently through 5 different agents over potentially 3 looping iterations, a ThreadLocal `event_context` generates and injects a single unified `session_id` into the logs. This allows engineers to grep `data/event_logs.jsonl` and instantly visualize the entire lifecycle, reasoning, and prompt confidence of a single user transaction.

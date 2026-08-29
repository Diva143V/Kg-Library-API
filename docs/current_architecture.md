# Current Architecture Audit

## Overview
This document presents an audit of the existing codebase in `conversational-ai-modules-monorepo`, analyzing the structural layout, component boundaries, storage backend integrations, LLM abstractions, and graph reasoning mechanics prior to implementing Diwakar's Knowledge Graph & Think-on-Graph (ToG) component of the Polaris architecture.

---

## 1. Repository Layout & Component Structure

The monorepo contains several loosely coupled packages defined in `pyproject.toml`:

```
.
├── expert_system/       # Conversational AI logic and LangChain retrieval chain wrappers
├── llms/                # LLM client abstractions (Azure OpenAI, Groq, BaseLLM)
├── nlqs/                # Natural Language Query System (SQL generation, NeonDB, ChromaDB)
├── scripts/             # Benchmarking, database migration, and standalone test scripts
├── state_machine/       # Dialogue state management primitives
├── tog/                 # Existing Think-on-Graph implementation & Neo4j KG wrappers
│   ├── config.py        # Default iteration, depth, and pruning parameters
│   ├── kgs/             # Knowledge Graph interface (`kg.py`) & Neo4j driver (`neo4j_kg.py`)
│   ├── models/          # Primitive data models (`entity.py`, `relation.py`, `triple.py`, `path.py`)
│   ├── pipeline/        # Exploration loop, LLM entity extraction & LLM-based relation/entity pruning
│   ├── prompts/         # Prompt templates for LLM entity & relation selection
│   ├── tog.py           # Main entry point for ToG query execution
│   └── utils/           # Logger setup utilities
├── tot/                 # Tree of Thoughts (ToT) reasoning engine
├── utils/               # Common helper utilities (JSON parsers, default LLM factories)
├── aegion.db            # Local SQLite database file
├── pyproject.toml       # Poetry dependency manifest
└── sample.env           # Environment template file
```

---

## 2. Existing Knowledge Graph Implementation (`tog/kgs/`)

- **Interface (`tog/kgs/kg.py`)**: Defines an abstract class `KnowledgeGraph` with methods `query(query_str)` and `size()`. It lacks basic CRUD operations for nodes, relationships, collections, and subgraphs.
- **Neo4j Backend (`tog/kgs/neo4j_kg.py`)**: Implements `KnowledgeGraph` over Neo4j using the official Python driver (`neo4j.GraphDatabase.driver`).
- **Data Models (`tog/models/`)**: Minimal dataclasses for `Entity`, `Relation`, `Triple`, and `Path`.
- **Deficiencies**:
  1. No standalone, database-agnostic in-memory Knowledge Graph engine.
  2. No generic CRUD abstraction (`create_node`, `get_node`, `update_node`, `delete_node`, `create_relationship`, `get_relationships`, `create_collection`, `add_to_collection`, `get_subgraph`).
  3. No distinction between Base Knowledge and Expert Annotations (annotations are absent or treated ad-hoc).

---

## 3. Existing Think-on-Graph (ToG) Implementation (`tog/`)

- **Entry Point (`tog/tog.py`)**:
  - `ToG.explore_and_answer()` orchestrates query execution:
    1. Entity Extraction (`LLMExtractor`)
    2. Entity Mapping (`EntityMapper`)
    3. Exploration Loop (`ExplorationLoop`) via `Neo4jEntityExplorer` and `Neo4jRelationExplorer`
    4. Path formatting and final LLM synthesis (`_generate_answer`)
- **Architectural Violation**:
  - **LLM-Driven Traversal**: In `RelationExplorer.prune_candidates()` and `EntityExplorer`, the system sends candidate relations/nodes to an LLM prompt to select and score which path to take next.
  - **Polaris Architecture Requirement**: Polaris strictly mandates **deterministic graph traversal** executed in standard code (BFS/DFS, max depth, relation filtering). The LLM MUST NOT determine graph traversal steps.

---

## 4. Graph Traversal Implementation

- **Current State**: Traversal is performed dynamically through `ExplorationLoop` which queries Neo4j 1-hop neighbours per iteration and relies on LLM scoring to prune paths.
- **Deficiencies**:
  - Lacks pure programmatic algorithms (BFS, DFS).
  - Lacks deterministic filtering mechanisms (relationship type filters, node label filters, max depth limits, max node limits, visited-set cycle prevention).
  - Lacks structured subgraph extraction algorithms independent of LLMs.

---

## 5. Storage & Database Integrations

- **Neo4j (`tog/kgs/neo4j_kg.py`)**: Graph store accessed via Cypher queries. Requires live Neo4j instance credentials (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`).
- **PostgreSQL / NeonDB (`nlqs/neondb_driver.py`)**: Relational database engine accessed via `psycopg2`.
- **ChromaDB (`nlqs/vectordb_driver.py`)**: Vector store for document retrieval and embedding search.
- **SQLite (`aegion.db`)**: Embedded relational database.

---

## 6. LLM Integration Layer (`llms/` & `utils/llm.py`)

- **Base Abstract LLM (`llms/base_llm.py`)**: Declares `generate()` interface.
- **Implementations**:
  - `AzureOpenAILLM` (`llms/azure_openai_llm.py`): Wraps Azure OpenAI SDK.
  - `GroqLLM` (`llms/groq_llm.py`): Wraps Groq API.
  - `utils/llm.py`: Provides default LLM initializers (`get_default_llm()`, `get_default_embedding_function()`) using LangChain's `AzureChatOpenAI` and `AzureOpenAIEmbeddings`.

---

## 7. Existing API Layer

- **Current APIs**:
  - Flask-based conversation endpoint placeholders in `expert_system/conversation.py`.
  - Gradio UI demo in `scripts/gradio_bot.py`.
- **Missing APIs**:
  - No FastAPI / REST framework providing structured endpoints for Knowledge Graph management (`/kg/*`), Annotation management (`/annotations/*`), or ToG reasoning (`/tog/*`).

---

## 8. Architectural Gaps relative to Polaris Specification

| Feature Boundary | Current Monorepo State | Polaris Diwakar Requirement |
| :--- | :--- | :--- |
| **KG Infrastructure** | Neo4j-specific driver wrapper | Reusable, storage-independent KG library with full CRUD, querying, collections, and subgraph extraction |
| **Annotation Model** | Non-existent | First-class Annotation objects (Opinion, Evidence, Assertion, etc.) with directed Annotation → KG and Annotation → Annotation relations |
| **Graph Traversal** | Nondeterministic, LLM-scored candidate pruning | 100% Deterministic graph traversal (BFS, DFS, bounded depth, relation/node filters, path extraction) |
| **Think-on-Graph Worker** | LLM handles step-by-step traversal decisions | LLM handles query understanding, entity ID, candidate relation selection, & final synthesis; traversal is code-executed |
| **Annotation-Aware ToG** | Single base graph stream | Multi-perspective retrieval: Base KG stream, Expert Annotation stream, and Expert over Base Knowledge stream |
| **API Layer** | Script demos & Flask helpers | Comprehensive REST API (`/kg/nodes`, `/annotations`, `/tog/query`, `/tog/traverse`) |

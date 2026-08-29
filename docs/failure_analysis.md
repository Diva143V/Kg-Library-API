# Empirical Failure Analysis & Issue Classification

## Overview
This document logs the empirical errors, test execution results, and runtime failures observed during **Phase 0 Audit** of the `conversational-ai-modules-monorepo` repository.

Each problem is classified into one of five categories:
- **Dependency problem**
- **Configuration problem**
- **Runtime problem**
- **Implementation problem**
- **Architectural problem**

---

## 1. Summary of Executed Test Suites & Commands

| Executed Command | Result | Major Error / Symptom | Problem Classification |
| :--- | :--- | :--- | :--- |
| `python -m pytest` (full repo) | Hung / Timeout | Infinite discovery / hanging connection attempts to external services (Neo4j / Postgres / Azure) | **Runtime problem** / **Configuration problem** |
| `python -m pytest expert_system/tests` | FAILED (Collection Error) | `ModuleNotFoundError: No module named 'langchain.chains'` in `expert_system/conversation.py:7` | **Dependency problem** |
| `python -m pytest utils/tests` | FAILED (1 failed, 7 passed) | `openai.APIConnectionError: Connection error. httpx.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.` | **Configuration problem** |
| `python -c "import tog"` | PASSED | Module imports cleanly | N/A |
| `python -c "from langchain_classic.chains import create_retrieval_chain"` | PASSED | Function is located in `langchain_classic.chains` | **Dependency problem** |

---

## 2. Detailed Failure Analysis & Root Cause Breakdown

### Issue 1: LangChain Chain Import Failure
- **Location**: `expert_system/conversation.py:7` (`from langchain.chains import create_retrieval_chain`)
- **Error Log**:
  ```
  ImportError while importing test module 'expert_system/tests/test_conversation.py'.
  expert_system/conversation.py:7: in <module>
      from langchain.chains import create_retrieval_chain
  ModuleNotFoundError: No module named 'langchain.chains'
  ```
- **Classification**: **Dependency problem**
- **Root Cause**: In `langchain` v1.3.11 / split package ecosystem, classic chain implementations like `create_retrieval_chain` and `create_stuff_documents_chain` are located under `langchain_classic.chains`.
- **Resolution Strategy**: Update import paths to compatibility packages or standard core abstractions without breaking existing callers.

---

### Issue 2: Azure OpenAI Endpoint Connection Failure
- **Location**: `utils/parameters.py:5` and `utils/llm.py`
- **Error Log**:
  ```
  openai.APIConnectionError: Connection error.
  httpx.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.
  ```
- **Classification**: **Configuration problem**
- **Root Cause**: `utils/parameters.py` sets placeholder default string `"insert_your_azure_openai_endpoint_here"` without `https://` scheme. When `get_default_llm()` initializes `AzureChatOpenAI`, HTTPX fails URL parsing.
- **Resolution Strategy**: Provide fallback handling and environment defaults with valid URI schemes or mock LLM providers for offline testing.

---

### Issue 3: LLM-Driven Graph Traversal Violation
- **Location**: `tog/pipeline/explorer.py:39-60` (`RelationExplorer.prune_candidates`), `tog/pipeline/exploration_loop.py`
- **Classification**: **Architectural problem**
- **Root Cause**: The current Think-on-Graph implementation relies on LLM prompts to prune and choose graph relations during graph traversal.
- **Polaris Requirement**: Polaris Phase 3 & 4 explicitly mandate that graph traversal MUST be 100% deterministic, implemented in code (BFS, DFS, relationship filters, depth limits), and that the LLM MUST NOT determine graph traversal steps.
- **Resolution Strategy**: Implement a clean separation:
  1. Pure deterministic graph traversal engine in Python (`BFS`, `DFS`, k-hop).
  2. LLM reasoning layer operating strictly on retrieved subgraphs.

---

### Issue 4: Missing Reusable Knowledge Graph CRUD & Data Models
- **Location**: `tog/kgs/kg.py`
- **Classification**: **Implementation problem**
- **Root Cause**: `KnowledgeGraph` abstract class only has `query()` and `size()`. It lacks standard node, relationship, collection, and subgraph CRUD operations.
- **Resolution Strategy**: Implement full storage-independent `KnowledgeGraph` library with in-memory graph engine and clear interfaces (`create_node`, `get_node`, `update_node`, `delete_node`, `create_relationship`, `get_relationships`, `create_collection`, `add_to_collection`, `query`, `get_subgraph`).

---

### Issue 5: Absence of Expert Annotation Layer & Separate Perspectives
- **Location**: Base codebase (`tog/`)
- **Classification**: **Architectural problem**
- **Root Cause**: Existing system has no concept of first-class `Annotation` objects or relationships (`ABOUT`, `SUPPORTS`, `CONTRADICTS`, `PROPOSES`, `CORRECTS`). Annotation data is not separated from base knowledge.
- **Resolution Strategy**: Build `Annotation` and `AnnotationGraph` layers in Phase 2 & Phase 5, preserving logical separation between Base Knowledge and Expert Annotations.

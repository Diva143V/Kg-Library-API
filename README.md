# Polaris: Knowledge Graph, Expert Annotations & Hybrid Think-on-Graph (ToG) API

Polaris is a modular, high-performance, and storage-agnostic Knowledge Graph (KG) library, annotation store, and hybrid reasoning worker. It enforces a strict **"Core + Packs"** architecture: keeping base facts separate from expert annotations, executing deterministic graph traversal in Python by default, and optionally escalating to AI providers for advanced reasoning to optimize latency and minimize inference credits.

---

## 🌟 Key Features

1. **Deterministic Graph-First Traversal**: Executed entirely in programmatic code (BFS, DFS, k-hop filters). Graph walking is 100% deterministic and runs in `< 5ms`.
2. **First-class Expert Annotations**: Allows adding annotations (Opinions, Evidence, Observations, Assertions, Hypotheses, Corrections) without flattening or modifying base KG nodes/edges.
3. **AI Escalation Gateway**: Enforces a strict credit-control policy (cost estimation, token limits, remaining budget checks, local-first Ollama/AnythingLLM with Cloud fallback).
4. **Three-Perspective Synthesis**: Formulates query responses across 3 distinct perspectives:
   - **Knowledge**: Summary of facts from base KG traversal paths.
   - **Expert**: Assertions gathered from expert annotations.
   - **Combined**: Semantic synthesis of expert opinions evaluated against base and external evidence.
5. **Domain Packs Retrieval**: Pluggable framework routing queries to specialized external tools/MCP servers (BioMCP, OpenBB, CourtListener, TinyFish general web search).
6. **Telemetry & Observability**: Logs path statistics, traversal latencies, and exact actual vs. estimated token/cost expenditures.

---

## 🚀 Quick Start

### Installation
Polaris manages python dependencies using Poetry. Run:
```bash
poetry install
```
Alternatively, install packages directly:
```bash
pip install -r requirements.txt
```

### Running the API Server
Start the Uvicorn FastAPI daemon:
```bash
python -m uvicorn kg_library_api.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Once launched, explore the interactive Swagger documentation:
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running Tests
Execute the comprehensive verification suite verifying traversal, annotations, packs routing, AI gateway routing, and budget fallback policies:
```bash
python -m pytest
```

---

## 💻 Python SDK Usage

```python
from kg_library_api import KnowledgeGraph, AnnotationManager, ToGWorker, AIGateway, AIEscalationPolicy

# 1. Initialize core graph and annotation manager
kg = KnowledgeGraph() # defaults to InMemoryStorageEngine
ann_mgr = AnnotationManager(kg)

# 2. Build base KG facts
kg.create_node("Gene_1", label="Gene", properties={"name": "BRCA1"})
kg.create_node("Disease_1", label="Disease", properties={"name": "Breast Cancer"})
kg.create_relationship("Gene_1", "Disease_1", type="associated_with")

# 3. Layer expert annotations (without mutating base facts)
ann = ann_mgr.create_annotation(
    type="Evidence", 
    content="High-throughput clinical cohort screening confirms pathogenetic variant.",
    author="Expert Geneticist",
    confidence=0.99
)
ann_mgr.add_annotation_relationship(ann.id, "Gene_1", relation_type="ABOUT")
ann_mgr.add_annotation_relationship(ann.id, "Disease_1", relation_type="SUPPORTS")

# 4. Orchestrate reasoning via ToG Worker (configured with escalation budgets)
policy = AIEscalationPolicy(traversal_mode="hybrid", ai_budget=0.05)
gateway = AIGateway(policy=policy)
worker = ToGWorker(kg, ann_mgr, ai_gateway=gateway)

response = worker.execute_query(
    query="Is there supporting evidence for BRCA1 role in Breast Cancer?",
    traversal_mode="hybrid"
)

print("Answer:", response["answer"])
print("Combined Perspective Summary:", response["perspectives"]["combined"]["summary"])
print("Telemetry cost:", response["metadata"]["actual_cost"])
```

---

## 📁 Repository Layout

```text
kg_library_api/
├── core/             # Storage-agnostic KG facade & models
├── annotations/      # Annotation manager & separate expert graph
├── traversal/        # BFS, DFS, k-hop deterministic traversal algorithms
├── retrieval/        # Domain packs registry & TinyFish/MCP connectors
├── ai/               # AI Gateway, policies, token/cost estimation, & providers
├── tog/              # Hybrid Think-on-Graph loop & synthesizer
└── api/              # FastAPI router endpoints (/annotations, /tog)
tests/                # Comprehensive unit and integration test suite
docs/                 # Architectural specifications
```

# Guide: How to Create and Extend APIs in Polaris

This guide explains how the **Knowledge-Graph Annotation API** and **Think-on-Graph Worker API** were built, how to run them locally, how to extend them with new custom endpoints, and how to consume or deploy them.

---

## 1. Overview & Architecture

The Polaris API layer is built using [FastAPI](https://fastapi.tiangolo.com/), a high-performance Python web framework with automatic OpenAPI documentation and Pydantic schema validation.

### Directory Structure

```text
polaris_kg/
  api/
    __init__.py
    app.py                # Main FastAPI application entry point
    annotation_router.py  # Router for Knowledge-Graph Annotation API
    tog_router.py         # Router for Think-on-Graph Worker API
```

---

## 2. Step-by-Step: How the API Was Created

### Step 1: Define Request & Response Models (Pydantic)

In `polaris_kg/api/annotation_router.py` or `tog_router.py`, define structured data schemas using Pydantic:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CreateAnnotationRequest(BaseModel):
    type: str = Field(description="Annotation type (e.g. Evidence, Hypothesis)")
    content: str = Field(description="Annotation text content")
    author: str = "expert"
    confidence: float = 1.0
    source: str = ""
    provenance: str = ""
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Step 2: Create an APIRouter

Grouping endpoints using `APIRouter` keeps code modular and maintainable:

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/annotations", tags=["Annotations"])

@router.post("", status_code=201)
def create_annotation(req: CreateAnnotationRequest):
    # Business logic call
    return {"id": "ann_123", "status": "created"}
```

### Step 3: Register Routers in Main FastAPI App

In `polaris_kg/api/app.py`:

```python
from fastapi import FastAPI
from polaris_kg.api.annotation_router import router as annotation_router
from polaris_kg.api.tog_router import router as tog_router

app = FastAPI(
    title="Polaris Knowledge Graph & Think-on-Graph Worker API",
    version="1.0.0",
)

# Register routers
app.include_router(annotation_router)
app.include_router(tog_router)
```

---

## 3. How to Add a New Custom Endpoint

Suppose you want to add a new endpoint to query nodes by label in `polaris_kg/api/annotation_router.py`:

```python
from fastapi import APIRouter, Depends
from polaris_kg.api.annotation_router import get_annotation_manager

@router.get("/nodes/search", status_code=200)
def search_nodes(label: str, mgr = Depends(get_annotation_manager)):
    """Search base knowledge graph nodes by label."""
    matching_nodes = mgr.base_kg.query({"label": label})
    return {"nodes": [n.to_dict() for n in matching_nodes]}
```

FastAPI automatically parses query parameters (`?label=Gene`), generates documentation, and validates types!

---

## 4. How to Run the API Server

### Local Development Server

Run Uvicorn from the project root directory:

```powershell
python -m uvicorn polaris_kg.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive Documentation

Open your browser to view generated interactive docs:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 5. How to Test Endpoints Automatically

FastAPI provides `TestClient` for unit and integration testing without launching a network socket:

```python
import pytest
from fastapi.testclient import TestClient
from polaris_kg.api.app import app

client = TestClient(app)

def test_create_annotation():
    response = client.post("/annotations", json={
        "type": "Evidence",
        "content": "Test content",
        "author": "Dr. Smith"
    })
    assert response.status_code == 201
    assert response.json()["type"] == "Evidence"
```

Run test suite with pytest:

```powershell
python -m pytest tests/test_phase4_annotation_api.py -v
```

---

## 6. Public Endpoint Reference

### Knowledge-Graph Annotation API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/annotations/collections` | Create an annotation collection |
| `POST` | `/annotations/collections/{id}/bulk` | Bulk upload an expert annotation dataset |
| `POST` | `/annotations` | Create a single expert annotation |
| `GET` | `/annotations/{id}` | Retrieve an annotation by ID |
| `POST` | `/annotations/{id}/relationships` | Create an Annotation → KG or Annotation → Annotation relationship |
| `GET` | `/annotations/about/{entity_id}` | Retrieve all annotations associated with an entity |
| `POST` | `/annotations/subgraph` | Retrieve connected annotation subgraphs |

### Think-on-Graph Worker API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/tog/query` | Execute Think-on-Graph query (`traversal_mode`: `"manual"` or `"ai"`) |

---

## 7. Client Usage Examples

### Python (`requests`)

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Bulk Ingest Annotations
bulk_resp = requests.post(f"{BASE_URL}/annotations/collections/coll_1/bulk", json={
    "annotations": [
        {"id": "ann_1", "type": "Evidence", "content": "Sample assay result."}
    ],
    "relationships": [
        {"source_annotation_id": "ann_1", "target_id": "Protein_X", "relation_type": "ABOUT"}
    ]
})
print("Bulk Status:", bulk_resp.json())

# 2. Query Think-on-Graph Worker
tog_resp = requests.post(f"{BASE_URL}/tog/query", json={
    "query": "What evidence supports Protein X?",
    "include_annotations": True,
    "max_depth": 3,
    "traversal_mode": "manual" # or "ai"
})
print("Answer:", tog_resp.json()["answer"])
```

### cURL

```bash
# Query Think-on-Graph Worker
curl -X POST "http://localhost:8000/tog/query" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "What evidence supports Protein X?",
           "include_annotations": true,
           "max_depth": 3,
           "traversal_mode": "manual"
         }'
```

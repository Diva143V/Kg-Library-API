"""
Main FastAPI Application combining Knowledge-Graph Annotation API and Think-on-Graph Worker API deliverables.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from polaris_kg.api.annotation_router import router as annotation_router
from polaris_kg.api.tog_router import router as tog_router

app = FastAPI(
    title="Polaris Knowledge Graph & Think-on-Graph Worker API",
    description="Reusable infrastructure deliverables for the Polaris architecture.",
    version="1.0.0",
)

app.include_router(annotation_router)
app.include_router(tog_router)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "polaris_kg"}


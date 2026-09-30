"""FastAPI entry point for predictive emergency dispatch."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph_solver import solve_dispatch


class DispatchRequest(BaseModel):
    rainfall_rate_mm: float = Field(ge=0, le=150)
    insar_displacement_mm: float = Field(ge=0, le=50)


app = FastAPI(title="Aerograph AI Dispatch API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "OK"}


@app.post("/api/v1/predict-dispatch")
def predict_dispatch(payload: DispatchRequest) -> dict:
    result = solve_dispatch(payload.rainfall_rate_mm, payload.insar_displacement_mm)
    return {"status": "success", **result}

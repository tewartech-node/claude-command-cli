"""
LLM Gateway - FastAPI wrapper for Ollama

Provides REST API interface for containerized LLM with monitoring.
"""

import os
import time
import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

logger = logging.getLogger(__name__)

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
API_PORT = int(os.getenv("API_PORT", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

app = FastAPI(
    title="LLM Gateway",
    description="API gateway for Ollama LLM service",
    version="1.0.0"
)


class InferenceRequest(BaseModel):
    model: str = "mistral"
    prompt: str
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: Optional[int] = None
    stream: bool = False


class InferenceResponse(BaseModel):
    model: str
    prompt: str
    response: str
    done: bool
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    ollama_host: str
    uptime_seconds: float
    models: List[str]


# Metrics tracking
class Metrics:
    def __init__(self):
        self.start_time = time.time()
        self.total_requests = 0
        self.total_tokens = 0
        self.total_duration = 0
        self.errors = 0
        self.model_counts: Dict[str, int] = {}

    def record_request(self, model: str, duration: int, tokens: int, success: bool):
        self.total_requests += 1
        if success:
            self.total_tokens += tokens
            self.total_duration += duration
            self.model_counts[model] = self.model_counts.get(model, 0) + 1
        else:
            self.errors += 1

    def get_stats(self) -> Dict:
        uptime = time.time() - self.start_time
        avg_duration = self.total_duration / max(self.total_requests, 1)
        avg_tokens_per_sec = (self.total_tokens / self.total_duration * 1e9) if self.total_duration > 0 else 0

        return {
            "uptime_seconds": uptime,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "average_request_duration_ms": avg_duration / 1e6,
            "tokens_per_second": avg_tokens_per_sec,
            "error_count": self.errors,
            "error_rate": self.errors / max(self.total_requests, 1),
            "models_used": self.model_counts,
        }


metrics = Metrics()


@app.on_event("startup")
async def startup():
    """Verify Ollama connection on startup"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)
            if response.status_code == 200:
                logger.info(f"Connected to Ollama at {OLLAMA_HOST}")
                data = response.json()
                logger.info(f"Available models: {len(data.get('models', []))}")
            else:
                logger.error(f"Ollama health check failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)

            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                stats = metrics.get_stats()

                return HealthResponse(
                    status="healthy",
                    ollama_host=OLLAMA_HOST,
                    uptime_seconds=stats["uptime_seconds"],
                    models=models,
                )
            else:
                raise HTTPException(status_code=503, detail="Ollama service unavailable")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}")


@app.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """Run inference on LLM"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Forward request to Ollama
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": False,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
            }

            if request.max_tokens:
                payload["num_predict"] = request.max_tokens

            start_time = time.time()
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json=payload,
                timeout=300.0
            )

            if response.status_code != 200:
                metrics.record_request(request.model, 0, 0, False)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama error: {response.text}"
                )

            data = response.json()
            duration_ms = int((time.time() - start_time) * 1e6)  # Convert to nanoseconds

            # Record metrics
            eval_count = data.get("eval_count", 0)
            metrics.record_request(request.model, duration_ms, eval_count, True)

            return InferenceResponse(
                model=request.model,
                prompt=request.prompt,
                response=data.get("response", ""),
                done=data.get("done", True),
                total_duration=data.get("total_duration", duration_ms),
                load_duration=data.get("load_duration", 0),
                prompt_eval_count=data.get("prompt_eval_count", 0),
                prompt_eval_duration=data.get("prompt_eval_duration", 0),
                eval_count=eval_count,
                eval_duration=data.get("eval_duration", 0),
                timestamp=datetime.utcnow().isoformat(),
            )

    except httpx.ConnectError as e:
        metrics.record_request(request.model, 0, 0, False)
        logger.error(f"Failed to connect to Ollama: {e}")
        raise HTTPException(status_code=503, detail="Ollama service unavailable")
    except httpx.TimeoutException:
        metrics.record_request(request.model, 0, 0, False)
        logger.error("Inference request timed out")
        raise HTTPException(status_code=504, detail="Inference request timed out")
    except Exception as e:
        metrics.record_request(request.model, 0, 0, False)
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")


@app.get("/models")
async def list_models():
    """List available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)

            if response.status_code == 200:
                data = response.json()
                return {
                    "models": [
                        {
                            "name": m["name"],
                            "size": m.get("size", 0),
                            "modified_at": m.get("modified_at", ""),
                        }
                        for m in data.get("models", [])
                    ]
                }
            else:
                raise HTTPException(status_code=503, detail="Ollama service unavailable")
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")


@app.get("/stats")
async def get_stats():
    """Get gateway statistics"""
    return metrics.get_stats()


@app.get("/")
async def root():
    """API root"""
    return {
        "name": "LLM Gateway",
        "version": "1.0.0",
        "description": "API gateway for Ollama LLM service",
        "endpoints": {
            "health": "/health",
            "inference": "/inference",
            "models": "/models",
            "stats": "/stats",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level=LOG_LEVEL)

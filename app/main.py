from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import asyncio
import random
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import redis
import asyncpg
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="Kubernetes Machine Gun Target", version="1.0.0")

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/machinegun")
engine = create_engine(DATABASE_URL)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.on_event("startup")
async def startup():
    # Create tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint VARCHAR(255),
                method VARCHAR(10),
                response_time FLOAT,
                status_code INTEGER,
                user_agent TEXT,
                ip_address INET
            )
        """))
        conn.commit()

@app.get("/")
async def root():
    return {"message": "Machine Gun Target Ready", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/cpu-intensive")
async def cpu_intensive(n: int = 1000000):
    """CPU intensive endpoint"""
    start_time = time.time()
    result = sum(i * i for i in range(n))
    response_time = time.time() - start_time
    
    # Log to database
    await log_request("/cpu-intensive", "GET", response_time, 200)
    
    return {
        "result": result,
        "computation_time": response_time,
        "n": n
    }

@app.get("/memory-intensive")
async def memory_intensive(size_mb: int = 100):
    """Memory intensive endpoint"""
    start_time = time.time()
    
    # Allocate memory
    data = [random.random() for _ in range(size_mb * 1024 * 1024 // 8)]
    
    # Do some processing
    result = sum(data) / len(data)
    
    response_time = time.time() - start_time
    await log_request("/memory-intensive", "GET", response_time, 200)
    
    return {
        "average": result,
        "size_mb": size_mb,
        "processing_time": response_time
    }

@app.get("/database-heavy")
async def database_heavy(queries: int = 100):
    """Database intensive endpoint"""
    start_time = time.time()
    
    results = []
    with engine.connect() as conn:
        for _ in range(queries):
            result = conn.execute(text("SELECT COUNT(*) FROM requests")).fetchone()
            results.append(result[0])
    
    response_time = time.time() - start_time
    await log_request("/database-heavy", "GET", response_time, 200)
    
    return {
        "query_count": queries,
        "total_requests": sum(results),
        "response_time": response_time
    }

@app.post("/queue-task")
async def queue_task(task_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Queue a background task"""
    start_time = time.time()
    
    # Add to Redis queue
    task_id = f"task_{int(time.time() * 1000)}"
    redis_client.lpush("tasks", json.dumps({
        "id": task_id,
        "data": task_data,
        "created_at": datetime.now().isoformat()
    }))
    
    response_time = time.time() - start_time
    await log_request("/queue-task", "POST", response_time, 200)
    
    return {
        "task_id": task_id,
        "queued": True,
        "response_time": response_time
    }

@app.get("/slow-endpoint")
async def slow_endpoint(delay: float = 2.0):
    """Slow endpoint to test timeouts"""
    await asyncio.sleep(delay)
    response_time = delay
    await log_request("/slow-endpoint", "GET", response_time, 200)
    
    return {
        "delay": delay,
        "message": "Slow response completed"
    }

@app.get("/error-prone")
async def error_prone(error_rate: float = 0.1):
    """Endpoint that randomly fails"""
    start_time = time.time()
    
    if random.random() < error_rate:
        response_time = time.time() - start_time
        await log_request("/error-prone", "GET", response_time, 500)
        raise HTTPException(status_code=500, detail="Random error occurred")
    
    response_time = time.time() - start_time
    await log_request("/error-prone", "GET", response_time, 200)
    
    return {
        "success": True,
        "error_rate": error_rate,
        "response_time": response_time
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/stats")
async def stats():
    """Basic stats endpoint"""
    with engine.connect() as conn:
        total_requests = conn.execute(text("SELECT COUNT(*) FROM requests")).fetchone()[0]
        avg_response_time = conn.execute(text("SELECT AVG(response_time) FROM requests")).fetchone()[0]
        error_count = conn.execute(text("SELECT COUNT(*) FROM requests WHERE status_code >= 400")).fetchone()[0]
    
    return {
        "total_requests": total_requests,
        "average_response_time": float(avg_response_time) if avg_response_time else 0,
        "error_count": error_count,
        "error_rate": error_count / total_requests if total_requests > 0 else 0
    }

async def log_request(endpoint: str, method: str, response_time: float, status_code: int):
    """Log request to database"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO requests (endpoint, method, response_time, status_code, user_agent, ip_address)
                VALUES (:endpoint, :method, :response_time, :status_code, :user_agent, :ip_address)
            """), {
                "endpoint": endpoint,
                "method": method,
                "response_time": response_time,
                "status_code": status_code,
                "user_agent": "MachineGun/1.0",
                "ip_address": "127.0.0.1"
            })
            conn.commit()
    except Exception as e:
        print(f"Failed to log request: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json

app = FastAPI()

# ✅ Enable CORS properly for any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins
    allow_credentials=True,
    allow_methods=["*"],          # allow all HTTP methods
    allow_headers=["*"],          # allow all headers
)

# Load telemetry data once at startup
with open("q-vercel-latency.json") as f:
    DATA = json.load(f)

@app.options("/")
async def options_handler():
    """Handles preflight CORS requests."""
    return {"message": "ok"}

@app.post("/")
async def check_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        region_data = [d for d in DATA if d["region"] == region]
        if not region_data:
            continue
        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_pct"] for d in region_data]
        breaches = sum(1 for d in region_data if d["latency_ms"] > threshold)

        result[region] = {
            "avg_latency": round(np.mean(latencies), 2),
            "p95_latency": round(np.percentile(latencies, 95), 2),
            "avg_uptime": round(np.mean(uptimes), 3),
            "breaches": breaches
        }

    # ✅ Explicitly add CORS headers to the response
    from fastapi.responses import JSONResponse
    response = JSONResponse(content=result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

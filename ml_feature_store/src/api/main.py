"""FastAPI application for Feature Store serving."""

import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import structlog

logger = structlog.get_logger()

# Metrics
REQUEST_COUNT = Counter(
    "feature_requests_total",
    "Total feature requests",
    ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "feature_serving_latency_seconds",
    "Feature serving latency",
    ["endpoint"]
)

# FastAPI app
app = FastAPI(
    title="ML Feature Store API",
    description="API for serving ML features in real-time and batch",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class OnlineFeatureRequest(BaseModel):
    """Request model for online feature retrieval."""
    entity_ids: List[str]
    feature_names: Optional[List[str]] = None


class OnlineFeatureResponse(BaseModel):
    """Response model for online features."""
    entity_id: str
    features: dict
    timestamp: datetime


class OfflineFeatureRequest(BaseModel):
    """Request model for offline/historical features."""
    entity_ids: List[str]
    feature_names: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/features/online", response_model=List[OnlineFeatureResponse])
async def get_online_features(request: OnlineFeatureRequest):
    """Get features from online store for real-time inference."""
    with REQUEST_LATENCY.labels(endpoint="online").time():
        try:
            responses = []

            for entity_id in request.entity_ids:
                # Simulated feature retrieval
                # In production, this would query Feast/Redis
                features = _get_mock_features(entity_id)

                if request.feature_names:
                    features = {
                        k: v for k, v in features.items()
                        if k in request.feature_names
                    }

                responses.append(OnlineFeatureResponse(
                    entity_id=entity_id,
                    features=features,
                    timestamp=datetime.utcnow()
                ))

            REQUEST_COUNT.labels(endpoint="online", status="success").inc()
            logger.info("Online features retrieved", count=len(responses))

            return responses

        except Exception as e:
            REQUEST_COUNT.labels(endpoint="online", status="error").inc()
            logger.error("Error retrieving online features", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/features/offline")
async def get_offline_features(request: OfflineFeatureRequest):
    """Get historical features from offline store for batch training."""
    with REQUEST_LATENCY.labels(endpoint="offline").time():
        try:
            # Simulated offline feature retrieval
            # In production, this would query Feast/Parquet
            results = []

            for entity_id in request.entity_ids:
                features = _get_mock_features(entity_id)
                results.append({
                    "entity_id": entity_id,
                    "features": features,
                    "event_timestamp": datetime.utcnow().isoformat()
                })

            REQUEST_COUNT.labels(endpoint="offline", status="success").inc()

            return {"results": results, "count": len(results)}

        except Exception as e:
            REQUEST_COUNT.labels(endpoint="offline", status="error").inc()
            logger.error("Error retrieving offline features", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/features/list")
async def list_features():
    """List all available features."""
    return {
        "feature_views": [
            {
                "name": "user_features",
                "entity": "user_id",
                "features": [
                    "total_purchases",
                    "total_spend",
                    "avg_purchase_value",
                    "days_since_last_purchase",
                    "purchase_frequency"
                ]
            },
            {
                "name": "product_features",
                "entity": "product_id",
                "features": [
                    "price",
                    "category",
                    "avg_rating",
                    "total_sales",
                    "stock_level"
                ]
            }
        ]
    }


@app.get("/entities")
async def list_entities():
    """List all registered entities."""
    return {
        "entities": [
            {"name": "user_id", "type": "STRING"},
            {"name": "product_id", "type": "STRING"}
        ]
    }


def _get_mock_features(entity_id: str) -> dict:
    """Get mock features for testing."""
    import hashlib

    # Generate deterministic mock features based on entity_id
    hash_val = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)

    return {
        "total_purchases": hash_val % 100,
        "total_spend": round((hash_val % 5000) + 50.0, 2),
        "avg_purchase_value": round((hash_val % 200) + 10.0, 2),
        "days_since_last_purchase": hash_val % 365,
        "purchase_frequency": round((hash_val % 50) / 10, 2)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

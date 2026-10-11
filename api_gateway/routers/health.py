"""Health Check Router - System health monitoring endpoints"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def health_overview():
    """
    Basic health check for the API Gateway
    
    Returns status of:
    - API Gateway itself (always healthy if this endpoint responds)
    - Service availability (checked lazily to avoid startup failures)
    """
    # Check service availability without importing at module level
    services_status = {}
    
    try:
        sys.path.insert(0, '../services')
        from api_gateway.dependencies import (
            get_discovery_client,
            get_ingestion_client,
            get_rag_client
        )
        
        discovery_client = get_discovery_client()
        ingestion_client = get_ingestion_client()
        rag_client = get_rag_client()
        
        services_status = {
            "discovery_service": "available" if discovery_client.check_availability() else "unavailable",
            "ingestion_service": "available" if ingestion_client.check_availability() else "unavailable",
            "rag_service": "available" if rag_client.check_availability() else "unavailable"
        }
    except Exception as e:
        # If dependencies fail to load, mark services as unavailable but keep API healthy
        services_status = {
            "discovery_service": "initializing",
            "ingestion_service": "initializing", 
            "rag_service": "initializing",
            "_note": f"Services loading: {str(e)}"
        }
    
    return {
        "status": "healthy",
        "api_gateway": "operational",
        "services": services_status,
        "version": "1.0.0"
    }


@router.get("/discovery")
async def discovery_health():
    """Discovery service specific health check"""
    try:
        from api_gateway.dependencies import get_discovery_client
        client = get_discovery_client()
        
        if not client.check_availability():
            raise HTTPException(
                status_code=503, 
                detail="Discovery service unavailable"
            )
            
        return client.get_status()
        
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle the 503 response properly
        raise
    except Exception as e:
        # Catch unexpected errors (e.g., connection errors) and return a 500
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

'''
@router.get("/ingestion")
async def ingestion_health():
    """Ingestion service specific health check"""
    if not client.check_availability():
        raise HTTPException(
            status_code=503, 
            detail="Ingestion service unavailable"
        )
    
    return client.get_status()


@router.get("/rag")
def rag_health(client = get_rag_client()):
    """RAG service specific health check"""
    if not client.check_availability():
        raise HTTPException(
            status_code=503, 
            detail="RAG service unavailable"
        )
    
    return client.get_status()
'''                                                                                                                                                                                                                                 
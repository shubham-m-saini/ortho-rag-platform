"""
API Gateway Dependencies Module

This module provides dependency injection for service clients used across routers.
It abstracts the underlying service implementations and handles availability checks.
"""

import sys
import os
from typing import Optional
from functools import lru_cache

# Ensure paths are set up correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))


class ServiceUnavailableError(Exception):
    """Raised when a required service is not available"""
    pass


# ============================================================================
# SERVICE CLIENT WRAPPERS
# ============================================================================

class DiscoveryServiceClient:
    """Client wrapper for Discovery Service (YouTube operations)"""
    
    def __init__(self):
        self.available = False
        self.youtube_api_configured = False
        
        try:
            from services.discovery_service.src.fetcher import test_youtube_connection
            from app_config.config import Config
            
            self.test_connection = test_youtube_connection
            self.youtube_api_key = Config.get_youtube_api_key()
            self.available = True
            self.youtube_api_configured = self.youtube_api_key is not None
            
        except ImportError as e:
            print(f"⚠️ Discovery Service Client not available: {e}")
        except Exception as e:
            print(f"⚠️ Discovery Service initialization error: {e}")
    
    def check_availability(self) -> bool:
        """Check if discovery service is available"""
        return self.available
    
    def get_status(self) -> dict:
        """Get detailed status of discovery service"""
        return {
            "available": self.available,
            "youtube_api_configured": self.youtube_api_configured
        }


class IngestionServiceClient:
    """Client wrapper for Ingestion Service (Download & Transcribe)"""
    
    def __init__(self):
        self.available = False
        
        try:
            from services.ingestion_worker.src.download_video import download_video
            from services.ingestion_worker.src.transcribe_worker import transcribe_video
            
            self.download_video = download_video
            self.transcribe_video = transcribe_video
            self.available = True
            
        except ImportError as e:
            print(f"⚠️ Ingestion Service Client not available: {e}")
        except Exception as e:
            print(f"⚠️ Ingestion Service initialization error: {e}")
    
    def check_availability(self) -> bool:
        """Check if ingestion service is available"""
        return self.available
    
    def get_status(self) -> dict:
        """Get detailed status of ingestion service"""
        return {"available": self.available}


class RAGServiceClient:
    """Client wrapper for RAG Service (Query & Indexing)"""
    
    def __init__(self):
        self.available = False
        
        try:
            from services.rag_api_service.src import rag_engine
            
            self.rag_engine = rag_engine
            self.available = True
            
        except ImportError as e:
            print(f"⚠️ RAG Service Client not available: {e}")
        except Exception as e:
            print(f"⚠️ RAG Service initialization error: {e}")
    
    def check_availability(self) -> bool:
        """Check if RAG service is available"""
        return self.available
    
    def get_status(self) -> dict:
        """Get detailed status of RAG service"""
        return {"available": self.available}


# ============================================================================
# SINGLETON INSTANCES (Cached for performance)
# ============================================================================

@lru_cache()
def get_discovery_client() -> DiscoveryServiceClient:
    """Get singleton instance of Discovery Service Client"""
    return DiscoveryServiceClient()


@lru_cache()
def get_ingestion_client() -> IngestionServiceClient:
    """Get singleton instance of Ingestion Service Client"""
    return IngestionServiceClient()


@lru_cache()
def get_rag_client() -> RAGServiceClient:
    """Get singleton instance of RAG Service Client"""
    return RAGServiceClient()


# ============================================================================
# FASTAPI DEPENDENCIES
# ============================================================================

from fastapi import Depends, HTTPException, status


class ServiceDependencies:
    """FastAPI dependency injection helpers for services"""
    
    @staticmethod
    def require_discovery_service(
        client: DiscoveryServiceClient = Depends(get_discovery_client)
    ) -> DiscoveryServiceClient:
        """Dependency that raises 503 if discovery service is unavailable"""
        if not client.check_availability():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Discovery service is currently unavailable"
            )
        return client
    
    @staticmethod
    def require_ingestion_service(
        client: IngestionServiceClient = Depends(get_ingestion_client)
    ) -> IngestionServiceClient:
        """Dependency that raises 503 if ingestion service is unavailable"""
        if not client.check_availability():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ingestion service is currently unavailable"
            )
        return client
    
    @staticmethod
    def require_rag_service(
        client: RAGServiceClient = Depends(get_rag_client)
    ) -> RAGServiceClient:
        """Dependency that raises 503 if RAG service is unavailable"""
        if not client.check_availability():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG service is currently unavailable"
            )
        return client


# Convenience aliases for use in routers
discovery_service = ServiceDependencies.require_discovery_service
ingestion_service = ServiceDependencies.require_ingestion_service
rag_service = ServiceDependencies.require_rag_service

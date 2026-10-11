import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file (Silent fail if missing for local dev)
load_dotenv()

class Config:
    """
    Centralized Configuration Manager for Ortho RAG System.
    
    Architecture: Hybrid (RabbitMQ + Redis + Qdrant)
    - RabbitMQ: Message Broker for Celery Task Queue (Reliability).
    - Redis: Result Backend, Job Status Cache, and Rate Limiting (Speed).
    - Qdrant: Vector Database for RAG Embeddings and Metadata.
    """

    # --- Environment Variables ---
    
    # YouTube API Key
    _YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    
    # Application Environment
    APP_ENV = os.getenv("APP_ENV", "development") # 'production' or 'development'

    # RabbitMQ Configuration (Broker)
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

    # Redis Configuration (Backend/Cache)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # Qdrant Configuration (Vector DB)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None) # Optional: For Cloud/Secure instances
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "ortho_rag_corpus")
    
    # Data Directory (Production: Mount volume, Local: Project root)
    _DATA_BASE_DIR_RAW = os.getenv("DATA_BASE_DIR")
    
    # Daily Quota Limit Override
    _DAILY_LIMIT_OVERRIDE = os.getenv("DAILY_SEARCH_LIMIT")

    # --- Connection Strings & Helpers ---

    @classmethod
    def get_rabbitmq_url(cls) -> str:
        """Constructs the AMQP URL for RabbitMQ."""
        return f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASSWORD}@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}{cls.RABBITMQ_VHOST}"

    @classmethod
    def get_redis_url(cls) -> str:
        """Constructs the Redis URL for Backend/Cache."""
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"

    @classmethod
    def get_qdrant_client_config(cls) -> Dict[str, Any]:
        """
        Returns a dictionary of arguments ready to be passed to QdrantClient().
        Handles both local (localhost) and cloud (API Key + URL) scenarios.
        """
        config = {
            "host": cls.QDRANT_HOST,
            "port": cls.QDRANT_PORT,
            "prefer_grpc": True, # Use gRPC for better performance if available
        }

        # If API Key is provided (Cloud or Secure Local), include it
        if cls.QDRANT_API_KEY:
            config["api_key"] = cls.QDRANT_API_KEY
        
        return config

    @classmethod
    def get_qdrant_collection_name(cls) -> str:
        """Returns the collection name to use."""
        return cls.QDRANT_COLLECTION_NAME

    # --- API & Mode Management ---

    @classmethod
    def get_youtube_api_key(cls) -> Optional[str]:
        """Returns API key if set, otherwise None to trigger Mock Mode."""
        return cls._YOUTUBE_API_KEY

    @classmethod
    def is_production_mode(cls) -> bool:
        """Determines if the app should run in strict production mode."""
        if cls.APP_ENV == "production":
            return True
        # Fallback heuristic
        return cls._YOUTUBE_API_KEY is not None and len(cls._YOUTUBE_API_KEY) > 10

    @classmethod
    def validate_production_setup(cls):
        """
        Call this at app startup. 
        Raises ValueError if running in production but missing critical keys.
        """
        if cls.is_production_mode():
            errors = []
            if not cls._YOUTUBE_API_KEY:
                errors.append("Missing YOUTUBE_API_KEY")
            
            # Optional: Enforce Qdrant API Key for cloud deployments if needed
            # if not cls.QDRANT_API_KEY and cls.QDRANT_HOST != "localhost":
            #     errors.append("QDRANT_API_KEY required for remote host")

            if errors:
                raise ValueError(
                    f"CRITICAL: Production deployment missing config: {', '.join(errors)}. "
                    "Please update your .env file."
                )

    # --- Path Management (Local vs Production) ---

    @classmethod
    def get_base_data_dir(cls) -> Path:
        """Returns the root directory for user data storage."""
        if cls._DATA_BASE_DIR_RAW:
            return Path(cls._DATA_BASE_DIR_RAW)
        
        # Fallback to project root relative path for local dev
        return Path(__file__).parent.parent / "data"

    @classmethod
    def get_daily_limit(cls) -> int:
        """Returns the daily search limit, preferring ENV override."""
        if cls._DAILY_LIMIT_OVERRIDE:
            try:
                return int(cls._DAILY_LIMIT_OVERRIDE)
            except ValueError:
                pass
        
        # Fallback to default or YAML config (loaded later)
        return 25

    # --- Seed Configuration Loading ---

    _seeds_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def get_seeds_config(cls) -> Dict[str, Any]:
        """
        Loads and caches the seeds.yaml configuration.
        Raises FileNotFoundError if config is missing (Critical for both modes).
        """
        if cls._seeds_cache:
            return cls._seeds_cache

        # Path to seeds.yaml relative to this file
        seeds_path = Path(__file__).parent.parent / "app_config" / "seeds.yaml"
        
        if not seeds_path.exists():
            raise FileNotFoundError(
                f"Critical Error: {seeds_path} not found. "
                "Please ensure config/seeds.yaml exists in the project root."
            )

        try:
            import yaml
            with open(seeds_path, 'r', encoding='utf-8') as f:
                cls._seeds_cache = yaml.safe_load(f)
            
            if not isinstance(cls._seeds_cache, dict):
                raise ValueError("seeds.yaml must be a valid YAML dictionary.")
                
            return cls._seeds_cache
            
        except Exception as e:
            raise RuntimeError(f"Failed to load seeds configuration: {e}")

    @classmethod
    def get_flattened_seeds(cls) -> List[str]:
        """Helper to flatten all categories into a single list of keywords."""
        config = cls.get_seeds_config()
        seeds_list = []
        
        ortho_seeds = config.get('orthopedic_seeds', {})
        for category, keywords in ortho_seeds.items():
            if isinstance(keywords, list):
                seeds_list.extend(keywords)
        
        return seeds_list

# --- Initialization Check (Optional) ---
# Uncomment the line below to fail immediately on startup if APP_ENV=production and keys are missing
# Config.validate_production_setup()

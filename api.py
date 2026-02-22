from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import json
from pathlib import Path
from datetime import datetime

# Optional DB imports (SQLAlchemy)
try:
    from sqlalchemy import create_engine, Column, String, Text, DateTime
    from sqlalchemy.orm import declarative_base, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except Exception:
    SQLALCHEMY_AVAILABLE = False

# Import existing agent functionality
from main import run_agent, agent

# Load environment variables
load_dotenv()

# API Key for authentication
API_KEY = os.getenv("DR_KAI_API_KEY", "default-api-key-change-in-production")

app = FastAPI(
    title="Dr. KAI Medical Assistant API",
    description="AI-powered medical assistant that provides evidence-based health information from approved Swedish medical sources",
    version="1.0.0"
)

# Add CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class MedicalQuery(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class MedicalResponse(BaseModel):
    response: str
    conversation_id: str
    sources_used: List[str] = []
    user_language: str = "unknown"

# Simple in-memory conversation storage (in production, use Redis or database)
conversations = {}

# Directory to persist conversation files
# Use absolute path for conversations directory so server cwd differences don't hide files
CONV_DIR = Path(os.path.join(os.getcwd(), "conversations"))
CONV_DIR.mkdir(parents=True, exist_ok=True)

# Configure basic logging so we can debug persistence issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dr_kai_api")

# PostgreSQL / SQLAlchemy setup (if DATABASE_URL configured and SQLAlchemy available)
DB_URL = os.getenv("DATABASE_URL")
DB_ENGINE = None
SessionLocal = None
Base = None
ConversationModel = None

if DB_URL and SQLALCHEMY_AVAILABLE:
    try:
        DB_ENGINE = create_engine(DB_URL, echo=False, future=True)
        SessionLocal = sessionmaker(bind=DB_ENGINE, autoflush=False, autocommit=False)
        Base = declarative_base()

        class ConversationModel(Base):
            __tablename__ = "conversations"
            id = Column(String(128), primary_key=True, index=True)
            history = Column(Text, nullable=False)
            created_at = Column(DateTime, nullable=False)
            updated_at = Column(DateTime, nullable=False)

        # Create tables (best-effort)
        try:
            Base.metadata.create_all(DB_ENGINE)
        except Exception:
            pass
    except Exception:
        DB_ENGINE = None
        SessionLocal = None
        Base = None
        ConversationModel = None


def save_conversation_to_file(conversation_id: str, history: List[BaseMessage]):
    """Persist a conversation's history to a JSON file (overwrites on each save)."""
    try:
        out = []
        for msg in history:
            role = "assistant" if isinstance(msg, AIMessage) else "user"
            out.append({
                "role": role,
                "content": msg.content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        file_path = CONV_DIR / f"{conversation_id}.json"
        tmp_path = CONV_DIR / f"{conversation_id}.json.tmp"

        # Write to a temp file and atomically replace to avoid partial writes
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # os.fsync may not be available on some platforms, ignore if it fails
                pass

        try:
            os.replace(tmp_path, file_path)
        except Exception:
            # Fall back to rename if atomic replace not available
            tmp_path.rename(file_path)

        # Log success and file metadata for debugging
        try:
            stat = file_path.stat()
            logger.info("Saved conversation %s -> %s (bytes=%d)", conversation_id, str(file_path), stat.st_size)
        except Exception:
            logger.info("Saved conversation %s -> %s", conversation_id, str(file_path))

    except Exception:
        # Log exception but do not raise; persistence is best-effort
        logger.exception("Failed to save conversation %s to file", conversation_id)


def save_conversation_to_db(conversation_id: str, history: List[BaseMessage]):
    """Save or update conversation record in Postgres via SQLAlchemy (best-effort)."""
    if not (DB_ENGINE and SessionLocal and Base):
        return
    try:
        # Convert history to plain list
        out = []
        for msg in history:
            role = "assistant" if isinstance(msg, AIMessage) else "user"
            out.append({
                "role": role,
                "content": msg.content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        payload = json.dumps(out, ensure_ascii=False)

        session = SessionLocal()
        try:
            now = datetime.utcnow()
            obj = session.get(ConversationModel, conversation_id)
            if obj:
                obj.history = payload
                obj.updated_at = now
            else:
                obj = ConversationModel(
                    id=conversation_id,
                    history=payload,
                    created_at=now,
                    updated_at=now,
                )
                session.add(obj)
            session.commit()
        finally:
            session.close()
    except Exception:
        # Best-effort: ignore DB errors
        pass


def load_conversation_from_file(conversation_id: str) -> Optional[List[BaseMessage]]:
    """Load conversation history from disk (JSON) and return list of BaseMessage or None."""
    try:
        file_path = CONV_DIR / f"{conversation_id}.json"
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        msgs: List[BaseMessage] = []
        for item in data:
            role = item.get("role")
            content = item.get("content", "")
            if role == "assistant":
                msgs.append(AIMessage(content=content))
            else:
                msgs.append(HumanMessage(content=content))

        logger.info("Loaded conversation %s from file (%d messages)", conversation_id, len(msgs))
        return msgs
    except Exception:
        logger.exception("Failed to load conversation %s from file", conversation_id)
        return None


def load_conversation_from_db(conversation_id: str) -> Optional[List[BaseMessage]]:
    """Load conversation history from DB and return list of BaseMessage or None."""
    if not (DB_ENGINE and SessionLocal and Base):
        return None
    try:
        session = SessionLocal()
        try:
            obj = session.get(ConversationModel, conversation_id)
            if not obj:
                return None
            data = json.loads(obj.history)
            msgs: List[BaseMessage] = []
            for item in data:
                role = item.get("role")
                content = item.get("content", "")
                if role == "assistant":
                    msgs.append(AIMessage(content=content))
                else:
                    msgs.append(HumanMessage(content=content))
            return msgs
        finally:
            session.close()
    except Exception:
        return None


def delete_conversation_from_db(conversation_id: str):
    if not (DB_ENGINE and SessionLocal and Base):
        return
    try:
        session = SessionLocal()
        try:
            obj = session.get(ConversationModel, conversation_id)
            if obj:
                session.delete(obj)
                session.commit()
        finally:
            session.close()
    except Exception:
        pass

def verify_api_key(authorization: str = Header(None)):
    """Verify API key from Bearer token in Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Missing or invalid Authorization header. Use: Authorization: Bearer YOUR_API_KEY"
        )

    token = authorization.replace("Bearer ", "").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return token

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Dr. KAI Medical Assistant API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    serpapi_key = bool(os.getenv("SERPAPI_API_KEY"))
    openai_key = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "status": "healthy" if (serpapi_key and openai_key) else "degraded",
        "services": {
            "openai_api": "configured" if openai_key else "missing",
            "serpapi": "configured" if serpapi_key else "missing"
        },
        "approved_sources": ["1177.se", "socialstyrelsen.se", "viss.nu", "fass.se"]
    }

@app.post("/api/medical-query", response_model=MedicalResponse)
async def medical_query(
    request: MedicalQuery,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a medical query and return evidence-based information from approved Swedish sources.

    - **query**: The medical question or symptom description (can be in any language)
    - **conversation_id**: Optional ID to maintain conversation context

    Returns a response in the user's original language with proper source citations.
    """
    try:
        # Get or create conversation history
        conversation_id = request.conversation_id or f"conv_{os.urandom(8).hex()}"
        history = conversations.get(conversation_id, [])

        # If not in memory, try loading from DB (if configured), then from disk
        if not history:
            try:
                loaded = load_conversation_from_db(conversation_id)
                if loaded:
                    history = loaded
                    conversations[conversation_id] = history
            except Exception:
                pass

        if not history:
            # Try file-based load as a fallback when DB isn't configured or the record isn't found
            try:
                loaded_file = load_conversation_from_file(conversation_id)
                if loaded_file:
                    history = loaded_file
                    conversations[conversation_id] = history
            except Exception:
                pass

        # Debug: log how many messages are present before invoking the agent
        try:
            logger.info("Invoking agent for %s (history messages=%d)", conversation_id, len(history))
            if len(history) > 0:
                # show a short preview of first and last messages
                first = history[0].content if hasattr(history[0], 'content') else str(history[0])
                last = history[-1].content if hasattr(history[-1], 'content') else str(history[-1])
                logger.info("History preview - first: %s | last: %s", (first[:120] if first else ''), (last[:120] if last else ''))
        except Exception:
            logger.exception("Failed to log history preview for %s", conversation_id)

        # Run the agent
        response = run_agent(request.query, history)

        # Extract sources from the response (basic parsing)
        sources_used = []
        if "🔗 Source:" in response.content:
            lines = response.content.split('\n')
            for line in lines:
                if line.startswith("   🔗 Source:"):
                    sources_used.append(line.replace("   🔗 Source:", "").strip())

        # Extract user language from response (if available)
        user_language = "unknown"
        if "[Original query language:" in response.content:
            try:
                lang_part = response.content.split("[Original query language:")[1].split("]")[0].strip()
                user_language = lang_part
            except:
                pass

        # Update conversation history
        history.extend([
            HumanMessage(content=request.query),
            response
        ])
        conversations[conversation_id] = history

        # Persist conversation to disk (best-effort)
        try:
            save_conversation_to_file(conversation_id, history)
        except Exception:
            pass
        # Also persist to DB if available (best-effort)
        try:
            save_conversation_to_db(conversation_id, history)
        except Exception:
            pass

        # Clean up old conversations (keep last 1000)
        if len(conversations) > 1000:
            # Remove oldest conversations
            oldest_keys = list(conversations.keys())[:100]
            for key in oldest_keys:
                del conversations[key]

        return MedicalResponse(
            response=response.content,
            conversation_id=conversation_id,
            sources_used=sources_used,
            user_language=user_language
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Clear conversation history for a specific conversation ID"""
    # Remove in-memory state if present
    if conversation_id in conversations:
        del conversations[conversation_id]

    # Remove persisted file if present (best-effort)
    try:
        file_path = CONV_DIR / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted conversation file %s", str(file_path))
    except Exception:
        logger.exception("Failed to delete conversation file %s", conversation_id)
        # Remove DB record if present (best-effort)
        try:
            delete_conversation_from_db(conversation_id)
        except Exception:
            pass
        return {"message": f"Conversation {conversation_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


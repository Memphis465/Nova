"""
Persistent memory system for Nova - remembers everything across sessions
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib


class NovaMemory:
    """
    Nova's long-term memory system.
    Stores conversations, facts learned, and context forever.
    """
    
    def __init__(self, db_path: str = "~/.nova/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                nova_response TEXT NOT NULL,
                tools_used TEXT,
                context TEXT
            )
        """)
        
        # Facts/knowledge table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                UNIQUE(content)
            )
        """)
        
        # Stephen's profile/preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Activity log (what Stephen is doing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_conversation(
        self, 
        user_message: str, 
        nova_response: str,
        tools_used: List[str] = None,
        context: Dict[str, Any] = None
    ):
        """Save a conversation exchange."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (timestamp, user_message, nova_response, tools_used, context)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            user_message,
            nova_response,
            json.dumps(tools_used or []),
            json.dumps(context or {})
        ))
        
        conn.commit()
        conn.close()
    
    def learn_fact(
        self,
        fact_type: str,
        content: str,
        source: str = "conversation",
        confidence: float = 1.0
    ):
        """Store a new fact/piece of knowledge."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO knowledge (timestamp, fact_type, content, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                fact_type,
                content,
                source,
                confidence
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Fact already exists, update confidence
            cursor.execute("""
                UPDATE knowledge 
                SET confidence = ?, updated_at = ?
                WHERE content = ?
            """, (confidence, datetime.utcnow().isoformat(), content))
            conn.commit()
        finally:
            conn.close()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, user_message, nova_response, tools_used, context
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "user": row[1],
                "nova": row[2],
                "tools": json.loads(row[3]) if row[3] else [],
                "context": json.loads(row[4]) if row[4] else {}
            }
            for row in rows
        ][::-1]  # Reverse to chronological order
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search past conversations and knowledge."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search conversations
        cursor.execute("""
            SELECT timestamp, user_message, nova_response
            FROM conversations
            WHERE user_message LIKE ? OR nova_response LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        conv_results = cursor.fetchall()
        
        # Search knowledge
        cursor.execute("""
            SELECT timestamp, fact_type, content
            FROM knowledge
            WHERE content LIKE ?
            ORDER BY confidence DESC, id DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        knowledge_results = cursor.fetchall()
        conn.close()
        
        results = []
        
        for row in conv_results:
            results.append({
                "type": "conversation",
                "timestamp": row[0],
                "user": row[1],
                "nova": row[2]
            })
        
        for row in knowledge_results:
            results.append({
                "type": "knowledge",
                "timestamp": row[0],
                "fact_type": row[1],
                "content": row[2]
            })
        
        return results
    
    def update_profile(self, key: str, value: Any):
        """Update Stephen's profile/preferences."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO profile (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, json.dumps(value), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_profile(self, key: str, default: Any = None) -> Any:
        """Get profile value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM profile WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return default
    
    def log_activity(self, activity_type: str, description: str, metadata: Dict = None):
        """Log what Stephen is doing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity (timestamp, activity_type, description, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            activity_type,
            description,
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_activity(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent activity log."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, activity_type, description, metadata
            FROM activity
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "type": row[1],
                "description": row[2],
                "metadata": json.loads(row[3]) if row[3] else {}
            }
            for row in rows
        ][::-1]
    
    def get_context_for_prompt(self) -> str:
        """Generate context string for Nova's system prompt."""
        recent_convs = self.get_recent_conversations(limit=5)
        recent_activity = self.get_recent_activity(limit=3)
        
        context_parts = []
        
        # Recent conversations
        if recent_convs:
            context_parts.append("=== RECENT CONVERSATION HISTORY ===")
            for conv in recent_convs:
                context_parts.append(f"You: {conv['user']}")
                context_parts.append(f"Nova: {conv['nova']}")
            context_parts.append("")
        
        # Recent activity
        if recent_activity:
            context_parts.append("=== WHAT STEPHEN HAS BEEN DOING ===")
            for act in recent_activity:
                context_parts.append(f"- {act['description']}")
            context_parts.append("")
        
        # Profile/preferences
        profile_keys = ['favorite_topics', 'current_projects', 'mood', 'goals']
        profile_data = {k: self.get_profile(k) for k in profile_keys if self.get_profile(k)}
        
        if profile_data:
            context_parts.append("=== STEPHEN'S PROFILE ===")
            for key, value in profile_data.items():
                context_parts.append(f"{key}: {value}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_convs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        total_facts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM activity")
        total_activities = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "conversations": total_convs,
            "facts_learned": total_facts,
            "activities_logged": total_activities
        }

"""
Epistemic Engine - Nova learns and gets smarter over time

This system:
1. Extracts knowledge from conversations
2. Builds semantic knowledge graph
3. Self-improves by recognizing patterns
4. Updates beliefs based on new evidence
"""

import json
import re
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict


class EpistemicEngine:
    """
    Self-improving knowledge system.
    Learns from interactions and builds structured knowledge.
    """
    
    def __init__(self, memory_system):
        self.memory = memory_system
        self.knowledge_graph = KnowledgeGraph()
    
    def process_conversation(
        self,
        user_message: str,
        nova_response: str,
        tools_used: List[str] = None
    ):
        """
        Extract and store knowledge from a conversation.
        """
        # Extract facts about Stephen
        user_facts = self._extract_user_facts(user_message)
        for fact in user_facts:
            self.memory.learn_fact(
                fact_type="user_preference",
                content=fact,
                source="conversation",
                confidence=0.8
            )
            self.knowledge_graph.add_fact("stephen", fact)
        
        # Extract technical knowledge
        tech_facts = self._extract_technical_knowledge(user_message, nova_response)
        for fact in tech_facts:
            self.memory.learn_fact(
                fact_type="technical",
                content=fact,
                source="conversation",
                confidence=0.7
            )
        
        # Extract task patterns
        if tools_used:
            pattern = self._extract_task_pattern(user_message, tools_used)
            if pattern:
                self.memory.learn_fact(
                    fact_type="task_pattern",
                    content=json.dumps(pattern),
                    source="tool_usage",
                    confidence=0.9
                )
    
    def _extract_user_facts(self, message: str) -> List[str]:
        """Extract facts about Stephen from his message."""
        facts = []
        message_lower = message.lower()
        
        # "I like/love/prefer X"
        patterns = [
            (r"i (?:like|love|prefer|enjoy) (.+?)(?:\.|,|!|\?|$)", "likes: {}"),
            (r"i (?:hate|dislike|can't stand) (.+?)(?:\.|,|!|\?|$)", "dislikes: {}"),
            (r"i'm (?:working on|building|creating) (.+?)(?:\.|,|!|\?|$)", "current_project: {}"),
            (r"my (?:favorite|favourite) (.+?) is (.+?)(?:\.|,|!|\?|$)", "favorite_{}: {}"),
            (r"i (?:usually|always|often) (.+?)(?:\.|,|!|\?|$)", "habit: {}"),
        ]
        
        for pattern, template in patterns:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    fact = template.format(*match)
                else:
                    fact = template.format(match)
                facts.append(fact.strip())
        
        return facts
    
    def _extract_technical_knowledge(self, user_msg: str, nova_msg: str) -> List[str]:
        """Extract technical facts/knowledge."""
        facts = []
        
        # Code/tech terms
        tech_keywords = ['python', 'javascript', 'api', 'database', 'server', 'function', 
                        'class', 'algorithm', 'framework', 'library']
        
        combined = (user_msg + " " + nova_msg).lower()
        
        # Extract definitions/explanations
        definition_patterns = [
            r"(.+?) is (?:a|an) (.+?)(?:\.|,|!|\?|$)",
            r"(.+?) means (.+?)(?:\.|,|!|\?|$)",
            r"(?:define|what is|what's) (.+?)\?",
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for match in matches[:3]:  # Limit to avoid noise
                if any(keyword in str(match).lower() for keyword in tech_keywords):
                    if isinstance(match, tuple):
                        fact = f"{match[0]}: {match[1]}"
                    else:
                        fact = str(match)
                    facts.append(fact.strip())
        
        return facts
    
    def _extract_task_pattern(self, user_message: str, tools_used: List[str]) -> Dict:
        """
        Learn task patterns: what user asks for → what tools to use
        """
        # Extract action verbs
        action_verbs = re.findall(
            r'\b(create|make|build|search|find|move|copy|delete|run|execute|check|analyze|edit)\b',
            user_message.lower()
        )
        
        if not action_verbs:
            return None
        
        return {
            "intent_keywords": action_verbs,
            "tools_sequence": tools_used,
            "example_query": user_message[:100]
        }
    
    def suggest_response_improvements(self, user_message: str) -> Dict[str, Any]:
        """
        Based on past patterns, suggest better responses.
        """
        # Search similar past conversations
        similar = self.memory.search_memory(user_message, limit=3)
        
        # Extract tools used in similar contexts
        tools_used_before = set()
        for item in similar:
            if item['type'] == 'conversation' and item.get('tools'):
                tools_used_before.update(item['tools'])
        
        suggestions = {
            "similar_past_queries": len(similar),
            "tools_previously_used": list(tools_used_before),
            "confidence": 0.7 if similar else 0.0
        }
        
        return suggestions
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of what Nova knows."""
        stats = self.memory.get_stats()
        
        # Get top facts by type
        conn = self.memory.db_path
        import sqlite3
        db = sqlite3.connect(conn)
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT fact_type, COUNT(*) as count
            FROM knowledge
            GROUP BY fact_type
            ORDER BY count DESC
        """)
        
        fact_types = dict(cursor.fetchall())
        db.close()
        
        return {
            "total_facts": stats['facts_learned'],
            "fact_types": fact_types,
            "conversations_analyzed": stats['conversations'],
            "knowledge_graph_nodes": len(self.knowledge_graph.nodes)
        }
    
    def improve_from_feedback(self, feedback_type: str, context: Dict):
        """
        Learn from explicit feedback.
        
        feedback_type: 'correct', 'incorrect', 'helpful', 'unhelpful'
        """
        if feedback_type in ['correct', 'helpful']:
            # Reinforce this pattern
            if 'tools_used' in context:
                pattern = self._extract_task_pattern(
                    context.get('user_message', ''),
                    context['tools_used']
                )
                if pattern:
                    self.memory.learn_fact(
                        fact_type="task_pattern",
                        content=json.dumps(pattern),
                        source="positive_feedback",
                        confidence=0.95
                    )
        
        elif feedback_type in ['incorrect', 'unhelpful']:
            # Mark this pattern as less reliable
            # In a full system, would adjust confidence scores
            pass


class KnowledgeGraph:
    """
    Simple knowledge graph structure.
    Nodes = entities, Edges = relationships
    """
    
    def __init__(self):
        self.nodes: Dict[str, Set[str]] = defaultdict(set)
        self.edges: Dict[Tuple[str, str], str] = {}
    
    def add_fact(self, entity: str, fact: str):
        """Add a fact about an entity."""
        self.nodes[entity].add(fact)
    
    def add_relationship(self, entity1: str, relation: str, entity2: str):
        """Add relationship between entities."""
        self.edges[(entity1, entity2)] = relation
    
    def get_facts(self, entity: str) -> Set[str]:
        """Get all facts about an entity."""
        return self.nodes.get(entity, set())
    
    def get_related(self, entity: str) -> List[Tuple[str, str]]:
        """Get entities related to this one."""
        related = []
        for (e1, e2), relation in self.edges.items():
            if e1 == entity:
                related.append((relation, e2))
            elif e2 == entity:
                related.append((relation, e1))
        return related


def create_epistemic_engine(memory_system):
    """Create and initialize epistemic engine."""
    return EpistemicEngine(memory_system)

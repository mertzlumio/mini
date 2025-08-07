# modes/chat/memory/__init__.py
# Empty init file

# modes/chat/memory/memory_manager.py
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

@dataclass
class MemoryEntry:
    """Structured memory entry"""
    content: str
    timestamp: datetime
    memory_type: str  # 'fact', 'preference', 'conversation', 'task'
    importance: float  # 0.0 to 1.0
    tags: List[str]
    context: Dict[str, Any]
    source_session: str
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data):
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class ConversationSummarizer:
    """Handles conversation summarization using Mistral"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def summarize_conversation(self, messages: List[Dict]) -> str:
        """Create a concise summary of conversation messages"""
        if not messages:
            return ""
        
        # Prepare conversation text
        conv_text = self._format_messages_for_summary(messages)
        
        summary_prompt = [
            {
                "role": "system",
                "content": "You are a conversation summarizer. Create a concise but comprehensive summary of the following conversation. Focus on: key facts mentioned, user preferences, important decisions made, and ongoing tasks/projects. Be specific about details the user might want referenced later."
            },
            {
                "role": "user", 
                "content": f"Summarize this conversation:\n\n{conv_text}"
            }
        ]
        
        try:
            response = self.api_client(summary_prompt)
            return response.get('content', 'Summary generation failed')
        except Exception as e:
            return f"Summary error: {str(e)}"
    
    def extract_facts(self, messages: List[Dict]) -> List[Dict]:
        """Extract key facts, preferences, and information from messages"""
        if not messages:
            return []
        
        conv_text = self._format_messages_for_summary(messages)
        
        extraction_prompt = [
            {
                "role": "system",
                "content": """You are a fact extractor. Analyze the conversation and extract key information in JSON format.
                
Return a JSON array where each item has:
{
  "content": "specific fact or information",
  "type": "fact|preference|task|project|person|location|tool",
  "importance": 0.8,
  "tags": ["relevant", "keywords"],
  "context": {"any": "additional context"}
}

Focus on information the user might want referenced later: preferences, ongoing projects, important facts, people mentioned, tools used, etc."""
            },
            {
                "role": "user",
                "content": f"Extract key facts from this conversation:\n\n{conv_text}"
            }
        ]
        
        try:
            response = self.api_client(extraction_prompt)
            content = response.get('content', '[]')
            # Try to parse JSON response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"Fact extraction error: {e}")
            return []
    
    def _format_messages_for_summary(self, messages: List[Dict]) -> str:
        """Format messages for summarization"""
        formatted = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if role == 'user':
                formatted.append(f"User: {content}")
            elif role == 'assistant':
                formatted.append(f"Assistant: {content}")
            elif role == 'tool':
                tool_name = msg.get('name', 'unknown_tool')
                formatted.append(f"Tool ({tool_name}): {content[:200]}...")
        return '\n'.join(formatted)

class SemanticMemory:
    """Handles long-term memory storage and retrieval"""
    
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        self.facts_file = os.path.join(memory_dir, 'facts.json')
        self.summaries_file = os.path.join(memory_dir, 'summaries.json')
        self.preferences_file = os.path.join(memory_dir, 'preferences.json')
        
        os.makedirs(memory_dir, exist_ok=True)
        
        self.facts = self._load_facts()
        self.summaries = self._load_summaries()
        self.preferences = self._load_preferences()
    
    def _load_facts(self) -> List[MemoryEntry]:
        """Load stored facts"""
        if not os.path.exists(self.facts_file):
            return []
        try:
            with open(self.facts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MemoryEntry.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading facts: {e}")
            return []
    
    def _load_summaries(self) -> List[Dict]:
        """Load conversation summaries"""
        if not os.path.exists(self.summaries_file):
            return []
        try:
            with open(self.summaries_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading summaries: {e}")
            return []
    
    def _load_preferences(self) -> Dict:
        """Load user preferences"""
        if not os.path.exists(self.preferences_file):
            return {}
        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return {}
    
    def save_fact(self, fact: MemoryEntry):
        """Save a fact to memory"""
        # Check for duplicates
        fact_hash = hashlib.md5(fact.content.encode()).hexdigest()
        for existing_fact in self.facts:
            existing_hash = hashlib.md5(existing_fact.content.encode()).hexdigest()
            if fact_hash == existing_hash:
                # Update importance if new fact is more important
                if fact.importance > existing_fact.importance:
                    existing_fact.importance = fact.importance
                    existing_fact.timestamp = fact.timestamp
                    self._save_facts()
                return
        
        self.facts.append(fact)
        self._save_facts()
    
    def save_summary(self, summary: str, session_id: str, message_count: int):
        """Save conversation summary"""
        summary_entry = {
            "session_id": session_id,
            "summary": summary,
            "message_count": message_count,
            "timestamp": datetime.now().isoformat(),
        }
        self.summaries.append(summary_entry)
        self._save_summaries()
    
    def update_preference(self, key: str, value: Any, context: str = ""):
        """Update user preference"""
        self.preferences[key] = {
            "value": value,
            "context": context,
            "updated": datetime.now().isoformat()
        }
        self._save_preferences()
    
    def search_memories(self, query: str, memory_types: List[str] = None, limit: int = 10) -> List[MemoryEntry]:
        """Search through stored memories"""
        query_lower = query.lower()
        matches = []
        
        for fact in self.facts:
            if memory_types and fact.memory_type not in memory_types:
                continue
            
            score = 0.0
            
            # Content match
            if query_lower in fact.content.lower():
                score += 1.0
            
            # Tag match
            for tag in fact.tags:
                if query_lower in tag.lower():
                    score += 0.5
            
            # Context match
            for key, value in fact.context.items():
                if query_lower in str(value).lower():
                    score += 0.3
            
            if score > 0:
                matches.append((fact, score * fact.importance))
        
        # Sort by relevance score
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches[:limit]]
    
    def get_recent_facts(self, days: int = 7, limit: int = 20) -> List[MemoryEntry]:
        """Get recent facts within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_facts = [
            fact for fact in self.facts 
            if fact.timestamp >= cutoff_date
        ]
        recent_facts.sort(key=lambda x: x.timestamp, reverse=True)
        return recent_facts[:limit]
    
    def get_context_for_conversation(self) -> str:
        """Get relevant context to inject into new conversations - IMPROVED"""
        context_parts = []
        
        # ALWAYS include recent important facts (not just > 0.7 importance)
        recent_facts = self.get_recent_facts(days=90, limit=15)  # Increased timeframe
        if recent_facts:
            fact_summaries = [f"- {fact.content}" for fact in recent_facts if fact.importance > 0.5]  # Lowered threshold
            if fact_summaries:
                context_parts.append("Key information about the user:")
                context_parts.extend(fact_summaries)
        
        # Add ALL preferences (not limited)
        if self.preferences:
            pref_items = []
            for key, pref in self.preferences.items():
                if isinstance(pref, dict) and 'value' in pref:
                    pref_items.append(f"- {key}: {pref['value']}")
                else:
                    pref_items.append(f"- {key}: {pref}")
            if pref_items:
                context_parts.append("\nUser preferences:")
                context_parts.extend(pref_items)
        
        # Add recent conversation summaries for additional context
        if self.summaries:
            recent_summaries = self.summaries[-2:]  # Last 2 summaries
            if recent_summaries:
                context_parts.append("\nRecent conversation context:")
                for summary in recent_summaries:
                    summary_text = summary.get('summary', '')[:200] + "..." if len(summary.get('summary', '')) > 200 else summary.get('summary', '')
                    context_parts.append(f"- {summary_text}")
        
        result = '\n'.join(context_parts) if context_parts else ""
        print(f"DEBUG: Generated context ({len(result)} chars): {result[:100]}...")
        return result
    
    def _save_facts(self):
        """Save facts to file"""
        try:
            data = [fact.to_dict() for fact in self.facts]
            with open(self.facts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving facts: {e}")
    
    def _save_summaries(self):
        """Save summaries to file"""
        try:
            with open(self.summaries_file, 'w', encoding='utf-8') as f:
                json.dump(self.summaries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving summaries: {e}")
    
    def _save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving preferences: {e}")

class MemoryManager:
    """Main memory management class that coordinates everything"""
    
    def __init__(self, memory_dir: str, api_client):
        self.memory_dir = memory_dir
        self.api_client = api_client
        
        self.summarizer = ConversationSummarizer(api_client)
        self.semantic_memory = SemanticMemory(memory_dir)
        
        # Working memory (current session)
        self.working_memory = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_to_working_memory(self, message: Dict):
        """Add message to current working memory"""
        self.working_memory.append(message)
    
    def get_enhanced_history(self, max_recent: int = 15) -> List[Dict]:
        """Get history enhanced with long-term memory context"""
        recent_messages = self.working_memory[-max_recent:] if self.working_memory else []
        
        # Get relevant context from long-term memory
        context = self.semantic_memory.get_context_for_conversation()
        print(f"DEBUG: Context retrieved: {context}")  # ADD THIS LINE
        
        if context and recent_messages:
        # ... rest of method
            # Inject context as a system message after any existing system message
            enhanced_history = []
            system_added = False
            
            for msg in recent_messages:
                enhanced_history.append(msg)
                # Add context after first system message or before first user message
                if not system_added and (msg.get('role') == 'system' or msg.get('role') == 'user'):
                    context_msg = {
                        "role": "system",
                        "content": f"Relevant context from previous conversations:\n{context}\n\nUse this context when relevant, but don't mention it explicitly unless directly asked about past conversations."
                    }
                    enhanced_history.insert(-1 if msg.get('role') == 'user' else len(enhanced_history), context_msg)
                    system_added = True
            
            return enhanced_history
        
        return recent_messages
    
    def process_conversation_chunk(self, messages: List[Dict], chunk_size: int = 20):
        """Process a chunk of conversation for long-term storage"""
        if len(messages) < 3:  # Need meaningful conversation
            return
        
        # Create summary
        summary = self.summarizer.summarize_conversation(messages)
        if summary and "error" not in summary.lower():
            self.semantic_memory.save_summary(summary, self.session_id, len(messages))
        
        # Extract and save facts
        facts = self.summarizer.extract_facts(messages)
        for fact_data in facts:
            try:
                memory_entry = MemoryEntry(
                    content=fact_data.get('content', ''),
                    timestamp=datetime.now(),
                    memory_type=fact_data.get('type', 'fact'),
                    importance=float(fact_data.get('importance', 0.5)),
                    tags=fact_data.get('tags', []),
                    context=fact_data.get('context', {}),
                    source_session=self.session_id
                )
                self.semantic_memory.save_fact(memory_entry)
            except Exception as e:
                print(f"Error saving extracted fact: {e}")
    
    def should_compress_memory(self, threshold: int = 30) -> bool:
        """Check if working memory should be compressed"""
        return len(self.working_memory) > threshold
    
    def compress_working_memory(self, keep_recent: int = 10):
        """Compress old working memory into long-term storage"""
        if len(self.working_memory) <= keep_recent:
            return
        
        # Get messages to compress (everything except recent ones)
        messages_to_compress = self.working_memory[:-keep_recent]
        
        # Process them for long-term storage
        self.process_conversation_chunk(messages_to_compress)
        
        # Keep only recent messages in working memory
        self.working_memory = self.working_memory[-keep_recent:]
        
        return len(messages_to_compress)
    
    def search_memory(self, query: str) -> str:
        """Search memory and return formatted results"""
        results = self.semantic_memory.search_memories(query, limit=5)
        
        if not results:
            return f"No memories found for '{query}'"
        
        formatted_results = [f"🧠 Memory search results for '{query}':"]
        
        for i, memory in enumerate(results, 1):
            age = datetime.now() - memory.timestamp
            age_str = f"{age.days}d ago" if age.days > 0 else "today"
            
            formatted_results.append(
                f"{i}. [{memory.memory_type}] {memory.content} "
                f"({age_str}, importance: {memory.importance:.1f})"
            )
        
        return '\n'.join(formatted_results)
    
    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        return {
            "working_memory_size": len(self.working_memory),
            "total_facts": len(self.semantic_memory.facts),
            "total_summaries": len(self.semantic_memory.summaries),
            "preferences_count": len(self.semantic_memory.preferences),
            "session_id": self.session_id,
        }
    
    def clear_session(self):
        """Clear working memory and start new session"""
        # Process current working memory before clearing
        if len(self.working_memory) > 5:
            self.process_conversation_chunk(self.working_memory)
        
        self.working_memory = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
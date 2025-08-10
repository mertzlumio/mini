# FIXED: modes/chat/memory/memory_manager.py
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import difflib

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
    """FIXED: Enhanced semantic memory with better search and retrieval"""
    
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
        print(f"DEBUG: Saved fact: {fact.content} (total facts: {len(self.facts)})")
    
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
        """COMPLETELY REWRITTEN: Much smarter semantic search"""
        if not query.strip():
            return []
            
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        matches = []
        
        print(f"DEBUG: Searching {len(self.facts)} facts for query: '{query}'")
        
        # Special case: if user wants "all facts" or similar, return everything
        if any(phrase in query_lower for phrase in ['all facts', 'everything', 'what do you know', 'stored facts', 'all memories']):
            print(f"DEBUG: Detected 'show all' query - returning all facts")
            # Return all facts sorted by importance and recency
            all_facts = sorted(self.facts, key=lambda f: (f.importance, f.timestamp), reverse=True)
            return all_facts[:limit]
        
        for fact in self.facts:
            if memory_types and fact.memory_type not in memory_types:
                continue
            
            score = 0.0
            content_lower = fact.content.lower()
            
            # 1. EXACT PHRASE MATCH (highest score)
            if query_lower in content_lower:
                score += 10.0
                print(f"DEBUG: Exact phrase match: '{query}' in '{fact.content}'")
            
            # 2. WORD OVERLAP SCORING (very important)
            content_words = set(content_lower.split())
            word_matches = query_words.intersection(content_words)
            if word_matches:
                # Score based on percentage of query words found
                word_score = (len(word_matches) / len(query_words)) * 8.0
                score += word_score
                print(f"DEBUG: Word matches {word_matches}: +{word_score:.1f} for '{fact.content}'")
            
            # 3. SEMANTIC KEYWORD MATCHING
            # Map common query patterns to content
            semantic_matches = {
                'name': ['name', 'called', 'martz', 'lumio'],
                'food': ['ice cream', 'dairy', 'eat', 'food'],
                'games': ['dota', 'play', 'gaming'],
                'preferences': ['likes', 'wants', 'prefers', 'avoiding'],
                'personal': ['user', 'i am', 'my', 'me']
            }
            
            for query_word in query_words:
                for category, keywords in semantic_matches.items():
                    if query_word in keywords or any(kw in content_lower for kw in keywords):
                        score += 3.0
                        print(f"DEBUG: Semantic match '{query_word}' -> {category}: +3.0 for '{fact.content}'")
                        break
            
            # 4. PARTIAL WORD MATCHING (for typos and variations)
            for query_word in query_words:
                for content_word in content_words:
                    # Check if words are similar (handles typos)
                    if len(query_word) > 2 and len(content_word) > 2:
                        # Simple similarity check
                        if (query_word in content_word or content_word in query_word or
                            abs(len(query_word) - len(content_word)) <= 2):
                            
                            # Calculate similarity ratio
                            similarity = difflib.SequenceMatcher(None, query_word, content_word).ratio()
                            if similarity > 0.6:  # 60% similar
                                score += similarity * 2.0
                                print(f"DEBUG: Partial match '{query_word}' ~ '{content_word}': +{similarity * 2.0:.1f}")
            
            # 5. TAG MATCHING (exact and partial)
            for tag in fact.tags:
                tag_lower = tag.lower()
                for query_word in query_words:
                    if query_word in tag_lower or tag_lower in query_word:
                        score += 4.0
                        print(f"DEBUG: Tag match '{query_word}' in tag '{tag}': +4.0")
            
            # 6. CONTEXT MATCHING
            for key, value in fact.context.items():
                value_str = str(value).lower()
                if any(word in value_str for word in query_words):
                    score += 2.0
                    print(f"DEBUG: Context match in {key}: +2.0")
            
            # Apply importance weighting (but don't let it dominate)
            importance_multiplier = 0.7 + (fact.importance * 0.3)  # Range: 0.7 to 1.0
            final_score = score * importance_multiplier
            
            print(f"DEBUG: Fact '{fact.content[:50]}...' - Raw score: {score:.1f}, Final: {final_score:.1f}")
            
            if final_score > 0.5:  # Lower threshold to catch more matches
                matches.append((fact, final_score))
        
        # Sort by relevance score
        matches.sort(key=lambda x: x[1], reverse=True)
        results = [match[0] for match in matches[:limit]]
        
        print(f"DEBUG: Found {len(results)} matching memories out of {len(self.facts)} total")
        
        # If still no results, try a desperate fallback
        if not results and len(query_words) == 1:
            query_word = list(query_words)[0]
            print(f"DEBUG: Fallback search for single word '{query_word}'")
            
            for fact in self.facts:
                # Very loose matching as last resort
                if (query_word in fact.content.lower() or 
                    any(query_word in tag.lower() for tag in fact.tags) or
                    any(query_word in str(value).lower() for value in fact.context.values())):
                    results.append(fact)
                    print(f"DEBUG: Fallback match found: '{fact.content}'")
                    if len(results) >= limit:
                        break
        
        return results
    
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
        """FIXED: Get relevant context to inject into new conversations"""
        context_parts = []
        
        print(f"DEBUG: Building context from {len(self.facts)} facts and {len(self.preferences)} preferences")
        
        # Get recent important facts (expanded search)
        recent_facts = self.get_recent_facts(days=30, limit=10)  # Look back further
        important_facts = [fact for fact in self.facts if fact.importance > 0.6][-10:]  # Get recent high-importance facts
        
        # Combine and deduplicate
        all_relevant_facts = []
        seen_content = set()
        
        for fact in recent_facts + important_facts:
            content_hash = hashlib.md5(fact.content.encode()).hexdigest()
            if content_hash not in seen_content:
                all_relevant_facts.append(fact)
                seen_content.add(content_hash)
        
        if all_relevant_facts:
            context_parts.append("=== STORED FACTS ===")
            for fact in all_relevant_facts[:8]:  # Limit to most relevant
                context_parts.append(f"• {fact.content}")
        
        # Add ALL preferences
        if self.preferences:
            context_parts.append("\n=== USER PREFERENCES ===")
            for key, pref in self.preferences.items():
                if isinstance(pref, dict) and 'value' in pref:
                    context_parts.append(f"• {key}: {pref['value']}")
                else:
                    context_parts.append(f"• {key}: {pref}")
        
        # Add recent summaries for more context
        if self.summaries:
            recent_summaries = self.summaries[-2:]  # Last 2 summaries
            if recent_summaries:
                context_parts.append("\n=== RECENT CONTEXT ===")
                for summary in recent_summaries:
                    summary_text = summary.get('summary', '')
                    if len(summary_text) > 150:
                        summary_text = summary_text[:150] + "..."
                    context_parts.append(f"• {summary_text}")
        
        result = '\n'.join(context_parts) if context_parts else ""
        print(f"DEBUG: Generated context ({len(result)} chars)")
        if result:
            print(f"DEBUG: Context preview: {result[:200]}...")
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
        """FIXED: Get history enhanced with long-term memory context"""
        recent_messages = self.working_memory[-max_recent:] if self.working_memory else []
        
        # Get relevant context from long-term memory
        context = self.semantic_memory.get_context_for_conversation()
        
        if context and recent_messages:
            # FIXED: Better context injection - always inject before user messages
            enhanced_history = []
            context_injected = False
            
            for i, msg in enumerate(recent_messages):
                # Inject context before the first user message
                if not context_injected and msg.get('role') == 'user':
                    context_msg = {
                        "role": "system",
                        "content": f"MEMORY CONTEXT (reference when relevant):\n{context}\n\nRefer to stored facts naturally in conversation. Don't mention 'memory system' explicitly."
                    }
                    enhanced_history.append(context_msg)
                    context_injected = True
                
                enhanced_history.append(msg)
            
            # If no user messages yet, add context at the end
            if not context_injected:
                context_msg = {
                    "role": "system", 
                    "content": f"MEMORY CONTEXT:\n{context}"
                }
                enhanced_history.append(context_msg)
            
            print(f"DEBUG: Enhanced history with {len(enhanced_history)} messages (context injected: {context_injected})")
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
            return 0
        
        # Get messages to compress (everything except recent ones)
        messages_to_compress = self.working_memory[:-keep_recent]
        
        # Process them for long-term storage
        self.process_conversation_chunk(messages_to_compress)
        
        # Keep only recent messages in working memory
        self.working_memory = self.working_memory[-keep_recent:]
        
        return len(messages_to_compress)
    
    def search_memory(self, query: str) -> str:
        """FIXED: Search memory and return better formatted results"""
        results = self.semantic_memory.search_memories(query, limit=5)
        
        if not results:
            # Also search preferences
            pref_matches = []
            query_lower = query.lower()
            for key, pref in self.semantic_memory.preferences.items():
                if query_lower in key.lower() or query_lower in str(pref).lower():
                    pref_matches.append(f"[preference] {key}: {pref.get('value', pref) if isinstance(pref, dict) else pref}")
            
            if pref_matches:
                return f"🔍 Found in preferences:\n" + "\n".join(pref_matches)
            
            return f"❌ No memories found for '{query}'\n💡 Try different keywords or check if the information was stored correctly"
        
        formatted_results = [f"🧠 Memory search results for '{query}':"]
        
        for i, memory in enumerate(results, 1):
            age = datetime.now() - memory.timestamp
            age_str = f"{age.days}d ago" if age.days > 0 else "today"
            
            formatted_results.append(
                f"\n{i}. [{memory.memory_type}] {memory.content}"
                f"\n   └─ {age_str}, importance: {memory.importance:.1f}"
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

# DEBUGGING HELPER FUNCTIONS
def debug_memory_search(memory_manager, query):
    """Debug helper to see what's happening in memory search"""
    print(f"\n=== DEBUG MEMORY SEARCH: '{query}' ===")
    facts = memory_manager.semantic_memory.facts
    print(f"Total facts in memory: {len(facts)}")
    
    for i, fact in enumerate(facts):
        print(f"{i+1}. [{fact.memory_type}] {fact.content} (importance: {fact.importance})")
    
    print(f"\nSearching...")
    results = memory_manager.semantic_memory.search_memories(query)
    print(f"Found {len(results)} results")
    
    return results

def test_memory_system():
    """Test the memory system with sample data"""
    import tempfile
    
    # Create temp memory directory
    temp_dir = tempfile.mkdtemp()
    
    # Mock API client
    def mock_api_client(messages):
        return {"content": "Mock summary of conversation"}
    
    # Create memory manager
    mm = MemoryManager(temp_dir, mock_api_client)
    
    # Add test facts
    from datetime import datetime
    
    test_facts = [
        MemoryEntry("User's name is John Smith", datetime.now(), "fact", 0.9, ["name", "personal"], {}, "test"),
        MemoryEntry("User prefers Python programming", datetime.now(), "preference", 0.8, ["coding", "language"], {}, "test"),
        MemoryEntry("User works at TechCorp", datetime.now(), "fact", 0.7, ["work", "company"], {}, "test"),
    ]
    
    for fact in test_facts:
        mm.semantic_memory.save_fact(fact)
    
    # Test searches
    queries = ["name", "John", "Python", "work", "company", "TechCorp"]
    
    for query in queries:
        print(f"\n--- Testing query: '{query}' ---")
        result = mm.search_memory(query)
        print(result)
    
    return mm
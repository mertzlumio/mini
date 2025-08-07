# modes/chat/capabilities/memory_tools.py
from datetime import datetime
from ..memory.memory_manager import MemoryEntry

def remember_fact(fact_content: str, importance: float = 0.7, tags: str = "", context: str = ""):
    """
    Store a fact in long-term memory that the agent can recall later.
    Use this when the user shares important information that should be remembered.
    """
    from ..core import get_memory_manager
    
    if not isinstance(fact_content, str) or not fact_content.strip():
        return "Error: Fact content cannot be empty"
    
    try:
        # Parse tags if provided
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Parse context if provided
        context_dict = {}
        if context:
            context_dict["additional_context"] = context
        
        # Create memory entry
        memory_entry = MemoryEntry(
            content=fact_content.strip(),
            timestamp=datetime.now(),
            memory_type="fact",
            importance=max(0.0, min(1.0, importance)),  # Clamp between 0-1
            tags=tag_list,
            context=context_dict,
            source_session=get_memory_manager().session_id
        )
        
        # Store the fact
        get_memory_manager().semantic_memory.save_fact(memory_entry)
        
        return f"✅ Remembered: '{fact_content}' (importance: {importance})"
        
    except Exception as e:
        return f"Error storing fact: {str(e)}"

def recall_information(query: str, limit: int = 5):
    """
    Search long-term memory for relevant information based on a query.
    Use this to find previously stored facts, preferences, or context.
    """
    from ..core import get_memory_manager
    
    if not isinstance(query, str) or not query.strip():
        return "Error: Search query cannot be empty"
    
    try:
        memory_manager = get_memory_manager()
        results = memory_manager.semantic_memory.search_memories(
            query.strip(), 
            limit=max(1, min(10, limit))
        )
        
        if not results:
            return f"No memories found for '{query}'"
        
        formatted_results = []
        for i, memory in enumerate(results, 1):
            age = datetime.now() - memory.timestamp
            age_str = f"{age.days}d ago" if age.days > 0 else "today"
            
            formatted_results.append(
                f"{i}. {memory.content} "
                f"[{memory.memory_type}, {age_str}, importance: {memory.importance:.1f}]"
            )
        
        return "🧠 Recalled information:\n" + "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error recalling information: {str(e)}"

def update_preference(preference_key: str, preference_value: str, context: str = ""):
    """
    Update or set a user preference that should be remembered long-term.
    Use this when the user expresses preferences about how they like things done.
    """
    from ..core import get_memory_manager
    
    if not isinstance(preference_key, str) or not preference_key.strip():
        return "Error: Preference key cannot be empty"
    
    if not isinstance(preference_value, str):
        preference_value = str(preference_value)
    
    try:
        memory_manager = get_memory_manager()
        memory_manager.semantic_memory.update_preference(
            preference_key.strip(),
            preference_value.strip(),
            context.strip() if context else ""
        )
        
        return f"✅ Updated preference '{preference_key}' = '{preference_value}'"
        
    except Exception as e:
        return f"Error updating preference: {str(e)}"

def get_memory_stats():
    """
    Get statistics about the current memory system state.
    Use this to understand how much information is stored.
    """
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        stats = memory_manager.get_stats()
        
        return f"""🧠 Memory System Stats:
- Working Memory: {stats['working_memory_size']} messages
- Long-term Facts: {stats['total_facts']} stored
- Conversation Summaries: {stats['total_summaries']}  
- User Preferences: {stats['preferences_count']}
- Current Session: {stats['session_id']}"""
        
    except Exception as e:
        return f"Error getting memory stats: {str(e)}"

def compress_working_memory():
    """
    Manually compress current working memory into long-term storage.
    Use this to free up working memory while preserving important information.
    """
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        if len(memory_manager.working_memory) <= 10:
            return "Working memory is small enough, no compression needed"
        
        compressed_count = memory_manager.compress_working_memory(keep_recent=8)
        return f"✨ Compressed {compressed_count} messages into long-term memory"
        
    except Exception as e:
        return f"Error compressing memory: {str(e)}"
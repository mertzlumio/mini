# FIXED: modes/chat/capabilities/memory_tools.py
from datetime import datetime
from ..memory.memory_manager import MemoryEntry
from datetime import datetime

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
        
        # ADDED: Debug confirmation
        print(f"DEBUG: Stored fact - {fact_content} (importance: {importance})")
        
        return f"✅ Remembered: '{fact_content}' (importance: {importance})"
        
    except Exception as e:
        return f"Error storing fact: {str(e)}"

def recall_information(query: str, limit: int = 5):
    """
    ENHANCED: Search long-term memory with much better intelligence
    """
    from ..core import get_memory_manager
    
    if not isinstance(query, str) or not query.strip():
        return "Error: Search query cannot be empty"
    
    try:
        memory_manager = get_memory_manager()
        
        print(f"DEBUG: Enhanced recall search for '{query}'")
        
        # Use the improved search method
        results = memory_manager.semantic_memory.search_memories(
            query.strip(), 
            limit=max(1, min(10, limit))
        )
        
        if not results:
            # Check preferences as fallback
            pref_results = []
            query_lower = query.lower()
            
            for key, pref in memory_manager.semantic_memory.preferences.items():
                pref_value = pref.get('value', pref) if isinstance(pref, dict) else str(pref)
                if (query_lower in key.lower() or 
                    query_lower in str(pref_value).lower()):
                    pref_results.append(f"[preference] {key}: {pref_value}")
            
            if pref_results:
                return f"🧠 Found in preferences:\n" + "\n".join(pref_results)
            
            # Enhanced "not found" message with suggestions
            total_facts = len(memory_manager.semantic_memory.facts)
            
            # Show what IS available
            if total_facts > 0:
                sample_facts = memory_manager.semantic_memory.facts[:3]
                samples = [f"'{fact.content[:30]}...'" for fact in sample_facts]
                
                return f"""❌ No direct matches for '{query}'

🧠 I have {total_facts} facts stored. Here are some examples:
{chr(10).join(f"  • {sample}" for sample in samples)}

💡 Try searching for:
  • Specific names or keywords from the facts
  • "all facts" to see everything
  • "name" to find personal info"""
            else:
                return f"❌ No memories found - no facts are currently stored."
        
        # Format results nicely
        formatted_results = [f"🧠 Found {len(results)} memories for '{query}':"]
        
        for i, memory in enumerate(results, 1):
            age = datetime.now() - memory.timestamp
            age_str = f"{age.days}d ago" if age.days > 0 else "today"
            
            formatted_results.append(
                f"\n{i}. [{memory.memory_type}] {memory.content}"
                f"\n   └─ {age_str}, importance: {memory.importance:.1f}"
            )
            
            # Add tags if they exist
            if memory.tags:
                formatted_results.append(f"   └─ tags: {', '.join(memory.tags)}")
        
        return '\n'.join(formatted_results)
        
    except Exception as e:
        print(f"DEBUG: Error in enhanced recall: {e}")
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
        
        # ADDED: Debug confirmation
        print(f"DEBUG: Updated preference - {preference_key}: {preference_value}")
        
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
        
        # IMPROVED: More detailed stats
        facts_by_type = {}
        for fact in memory_manager.semantic_memory.facts:
            facts_by_type[fact.memory_type] = facts_by_type.get(fact.memory_type, 0) + 1
        
        type_breakdown = ", ".join([f"{t}: {c}" for t, c in facts_by_type.items()]) if facts_by_type else "none"
        
        return f"""🧠 Memory System Stats:
- Working Memory: {stats['working_memory_size']} messages
- Long-term Facts: {stats['total_facts']} stored ({type_breakdown})
- Conversation Summaries: {stats['total_summaries']}  
- User Preferences: {stats['preferences_count']}
- Current Session: {stats['session_id']}

Recent activity: {len(memory_manager.semantic_memory.get_recent_facts(days=7, limit=50))} facts in last 7 days"""
        
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

# DEBUGGING FUNCTIONS
def debug_memory_state():
    """Debug function to examine current memory state"""
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        print("\n=== MEMORY DEBUG STATE ===")
        print(f"Working memory: {len(memory_manager.working_memory)} messages")
        print(f"Facts stored: {len(memory_manager.semantic_memory.facts)}")
        print(f"Preferences: {len(memory_manager.semantic_memory.preferences)}")
        
        print("\n--- STORED FACTS ---")
        for i, fact in enumerate(memory_manager.semantic_memory.facts[-5:], 1):  # Last 5 facts
            print(f"{i}. {fact.content} (type: {fact.memory_type}, importance: {fact.importance})")
        
        print("\n--- STORED PREFERENCES ---")
        for key, pref in memory_manager.semantic_memory.preferences.items():
            value = pref.get('value', pref) if isinstance(pref, dict) else pref
            print(f"- {key}: {value}")
        
        return "Debug complete - check console output"
        
    except Exception as e:
        return f"Debug error: {str(e)}"

def test_memory_recall(query: str):
    """Test memory recall with detailed debugging"""
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        print(f"\n=== TESTING MEMORY RECALL: '{query}' ===")
        
        # Show what we're searching through
        print(f"Total facts to search: {len(memory_manager.semantic_memory.facts)}")
        
        if memory_manager.semantic_memory.facts:
            print("Facts in memory:")
            for i, fact in enumerate(memory_manager.semantic_memory.facts):
                print(f"  {i+1}. {fact.content} (tags: {fact.tags})")
        
        # Perform search with debugging
        results = memory_manager.semantic_memory.search_memories(query)
        
        print(f"Search returned {len(results)} results")
        
        return recall_information(query)
        
    except Exception as e:
        return f"Test error: {str(e)}"

# Memory System Diagnostic Tool
# Add this to your memory_tools.py to debug what's happening

def diagnose_memory_system():
    """Comprehensive diagnosis of the memory system"""
    print("\n" + "="*50)
    print("MEMORY SYSTEM DIAGNOSTIC REPORT")
    print("="*50)
    
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        # 1. Basic Statistics
        print(f"\n1. BASIC STATS:")
        print(f"   - Facts stored: {len(memory_manager.semantic_memory.facts)}")
        print(f"   - Preferences: {len(memory_manager.semantic_memory.preferences)}")
        print(f"   - Working memory: {len(memory_manager.working_memory)} messages")
        
        # 2. Show all stored facts
        print(f"\n2. ALL STORED FACTS:")
        if not memory_manager.semantic_memory.facts:
            print("   ❌ NO FACTS STORED")
        else:
            for i, fact in enumerate(memory_manager.semantic_memory.facts, 1):
                age = (datetime.now() - fact.timestamp).days
                print(f"   {i}. \"{fact.content}\"")
                print(f"      - Type: {fact.memory_type}")
                print(f"      - Importance: {fact.importance}")
                print(f"      - Tags: {fact.tags}")
                print(f"      - Age: {age} days")
                print()
        
        # 3. Test context generation
        print(f"3. CONTEXT GENERATION TEST:")
        context = memory_manager.semantic_memory.get_context_for_conversation()
        if context:
            print(f"   ✅ Context generated ({len(context)} chars)")
            print(f"   Preview: {context[:200]}...")
        else:
            print(f"   ❌ NO CONTEXT GENERATED")
        
        # 4. Test search with common queries
        print(f"\n4. SEARCH TESTS:")
        test_queries = ["name", "user", "ice cream", "dairy", "Martz", "Lumio"]
        
        for query in test_queries:
            print(f"\n   Testing query: '{query}'")
            results = memory_manager.semantic_memory.search_memories(query)
            print(f"   Results: {len(results)} matches")
            
            if results:
                for j, result in enumerate(results[:2], 1):  # Show top 2
                    print(f"     {j}. \"{result.content}\" (importance: {result.importance})")
            else:
                # Manual check - why no results?
                print(f"   🔍 Manual check:")
                for fact in memory_manager.semantic_memory.facts:
                    if query.lower() in fact.content.lower():
                        print(f"     ❌ SHOULD MATCH: \"{fact.content}\"")
        
        # 5. Test enhanced history
        print(f"\n5. ENHANCED HISTORY TEST:")
        history = memory_manager.get_enhanced_history()
        
        context_messages = [msg for msg in history if msg.get('role') == 'system' and 'MEMORY CONTEXT' in msg.get('content', '')]
        
        if context_messages:
            print(f"   ✅ Context injected ({len(context_messages)} system messages)")
            for msg in context_messages:
                print(f"   Content preview: {msg['content'][:150]}...")
        else:
            print(f"   ❌ NO CONTEXT IN HISTORY")
        
        print(f"\n" + "="*50)
        print("DIAGNOSIS COMPLETE")
        print("="*50)
        
        return "Diagnostic complete - check console output for details"
        
    except Exception as e:
        print(f"DIAGNOSTIC ERROR: {e}")
        import traceback
        traceback.print_exc()
        return f"Diagnostic failed: {e}"

def test_search_step_by_step(query: str):
    """Step-by-step search debugging"""
    print(f"\n=== STEP-BY-STEP SEARCH DEBUG: '{query}' ===")
    
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        facts = memory_manager.semantic_memory.facts
        print(f"Step 1: Found {len(facts)} facts to search")
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        print(f"Step 2: Query words: {query_words}")
        
        matches = []
        
        for i, fact in enumerate(facts):
            print(f"\nStep 3.{i+1}: Checking fact: \"{fact.content}\"")
            
            score = 0.0
            content_lower = fact.content.lower()
            
            # Test exact match
            if query_lower in content_lower:
                score += 5.0
                print(f"  ✅ Exact match found! Score: +5.0")
            else:
                print(f"  ❌ No exact match")
            
            # Test word overlap
            content_words = set(content_lower.split())
            word_matches = query_words.intersection(content_words)
            if word_matches:
                word_score = len(word_matches) / len(query_words) * 3.0
                score += word_score
                print(f"  ✅ Word matches: {word_matches} Score: +{word_score:.1f}")
            else:
                print(f"  ❌ No word matches")
            
            # Final score with importance
            final_score = score * (0.5 + fact.importance * 0.5)
            print(f"  Final score: {score} * (0.5 + {fact.importance} * 0.5) = {final_score}")
            
            if final_score > 0:
                matches.append((fact, final_score))
                print(f"  ✅ ADDED TO RESULTS")
            else:
                print(f"  ❌ SCORE TOO LOW - NOT ADDED")
        
        print(f"\nStep 4: Found {len(matches)} total matches")
        matches.sort(key=lambda x: x[1], reverse=True)
        
        print("Final results:")
        for i, (fact, score) in enumerate(matches[:3], 1):
            print(f"  {i}. Score {score:.2f}: \"{fact.content}\"")
        
        return f"Step-by-step search complete for '{query}'"
        
    except Exception as e:
        return f"Debug failed: {e}"

def fix_context_injection_test():
    """Test if context injection is working"""
    print("\n=== CONTEXT INJECTION TEST ===")
    
    try:
        from ..core import get_memory_manager
        memory_manager = get_memory_manager()
        
        # Add a test message to working memory
        test_message = {"role": "user", "content": "Hello, do you know anything about me?"}
        memory_manager.add_to_working_memory(test_message)
        
        # Get enhanced history
        history = memory_manager.get_enhanced_history()
        
        print(f"Enhanced history has {len(history)} messages:")
        
        for i, msg in enumerate(history):
            role = msg.get('role')
            content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
            
            print(f"  {i+1}. [{role}] {content}")
            
            if role == 'system' and ('MEMORY CONTEXT' in msg.get('content', '') or 'STORED FACTS' in msg.get('content', '')):
                print(f"       ✅ CONTEXT MESSAGE FOUND!")
        
        return "Context injection test complete"
        
    except Exception as e:
        return f"Context test failed: {e}"



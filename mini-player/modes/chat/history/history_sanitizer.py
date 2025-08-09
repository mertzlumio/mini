# modes/chat/history/history_sanitizer.py
from collections import deque

def sanitize_and_trim_history(history, max_messages=15):
    """
    Sanitizes the chat history to ensure valid role order and structure,
    then trims it to a specified length while preserving tool call integrity.
    """
    if not history:
        return []

    # --- Sanitization Pass ---
    sanitized = []
    last_role = None
    
    # Use a deque for efficient popping from the left
    message_queue = deque(history)

    while message_queue:
        msg = message_queue.popleft()
        role = msg.get("role")

        # Rule 1: Ensure user/assistant roles alternate.
        # If the same role appears twice, keep the newest one.
        if role in ("user", "assistant") and role == last_role:
            # Overwrite the previous message of the same role
            if sanitized:
                sanitized[-1] = msg
            else:
                sanitized.append(msg)
            continue
        
        # Rule 2: Ensure tool calls are valid
        if role == "assistant" and msg.get("tool_calls"):
            # Look ahead to find all corresponding 'tool' messages
            tool_calls = msg.get("tool_calls", [])
            tool_ids_needed = {tc['id'] for tc in tool_calls}
            
            found_tools = []
            temp_queue = deque()

            while message_queue:
                next_msg = message_queue.popleft()
                if next_msg.get("role") == "tool" and next_msg.get("tool_call_id") in tool_ids_needed:
                    found_tools.append(next_msg)
                    tool_ids_needed.remove(next_msg.get("tool_call_id"))
                else:
                    # It's not the tool we're looking for, put it back
                    temp_queue.append(next_msg)
                
                if not tool_ids_needed:
                    break # Found all tools for this call
            
            # Put back the non-matching messages at the front of the queue
            message_queue.extendleft(reversed(temp_queue))

            # Only add the assistant message and its tools if all were found
            if not tool_ids_needed:
                sanitized.append(msg)
                sanitized.extend(found_tools)
                last_role = "tool" # The last message added was a tool
            # If not all tools were found, the assistant call is orphaned and discarded.
            
        elif role == "tool":
            # Discard orphaned tool messages not preceded by a tool_call
            # The logic above handles keeping valid tools, so any tool message
            # reaching here is considered an orphan.
            continue
        else:
            sanitized.append(msg)
            last_role = role

    # --- Trimming Pass ---
    if len(sanitized) <= max_messages:
        return sanitized

    trimmed = []
    tool_call_ids_to_keep = set()

    # Walk backward from the end of the *sanitized* list
    for msg in reversed(sanitized):
        role = msg.get("role")

        if role == "tool":
            tool_call_ids_to_keep.add(msg.get("tool_call_id"))
            trimmed.insert(0, msg)
        elif role == "assistant" and msg.get("tool_calls"):
            # Keep this assistant message only if it's responsible for a tool call we are keeping
            tool_ids_in_msg = {tc["id"] for tc in msg["tool_calls"]}
            if tool_call_ids_to_keep.intersection(tool_ids_in_msg):
                trimmed.insert(0, msg)
                # This assistant message is kept, so we no longer need to track the tool call ID
                tool_call_ids_to_keep.difference_update(tool_ids_in_msg)
        elif role in ("user", "assistant"): # Assistant without tool calls
            trimmed.insert(0, msg)
        
        # Stop when we have enough messages, but ensure the first message is a user message
        if len(trimmed) >= max_messages:
            if trimmed[0].get("role") == "user":
                break
    
    # Final check to ensure the conversation doesn't start with an assistant
    while trimmed and trimmed[0].get("role") != "user":
        trimmed.pop(0)

    return trimmed
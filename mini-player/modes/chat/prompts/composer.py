"""Main prompt composition system inspired by LangChain"""

import os
from typing import List, Dict, Any, Optional
from .base import BASE_PERSONALITY, RESPONSE_FORMATTING
from .memory import MEMORY_INSTRUCTIONS
from .visual import VISUAL_INSTRUCTIONS
from .capabilities import generate_capability_descriptions

class PromptComposer:
    """Composes system prompts dynamically based on available capabilities"""
    
    def __init__(self):
        self.base_prompt = BASE_PERSONALITY
        self.formatting_rules = RESPONSE_FORMATTING
        
        # Module registry - maps capability names to instruction blocks
        self.instruction_modules = {
            'memory': MEMORY_INSTRUCTIONS,
            'visual': VISUAL_INSTRUCTIONS,
        }
    
    def build_system_prompt(self, 
                           active_capabilities: Optional[List[str]] = None,
                           include_tools: bool = True,
                           include_formatting: bool = True) -> str:
        """
        Build a complete system prompt based on active capabilities
        
        Args:
            active_capabilities: List of capabilities to include (auto-detected if None)
            include_tools: Whether to include auto-generated tool descriptions
            include_formatting: Whether to include formatting guidelines
        """
        prompt_parts = [self.base_prompt]
        
        # Auto-detect capabilities if not provided
        if active_capabilities is None:
            active_capabilities = self._detect_active_capabilities()
        
        # Add capability-specific instructions
        for capability in active_capabilities:
            if capability in self.instruction_modules:
                prompt_parts.append(self.instruction_modules[capability])
        
        # Add auto-generated tool documentation
        if include_tools:
            tool_docs = generate_capability_descriptions()
            if tool_docs and "Error" not in tool_docs:
                prompt_parts.append(f"## Available Tools:\n{tool_docs}")
        
        # Add formatting guidelines
        if include_formatting:
            prompt_parts.append(self.formatting_rules)
        
        return "\n\n".join(prompt_parts)
    
    def _detect_active_capabilities(self) -> List[str]:
        """Auto-detect what capabilities are currently available"""
        capabilities = []
        
        # Check for memory system
        try:
            from ..memory.memory_manager import MemoryManager
            capabilities.append('memory')
        except ImportError:
            pass
        
        # Check for vision capabilities
        try:
            from config import supports_vision
            if supports_vision():
                capabilities.append('visual')
        except ImportError:
            pass
        
        # Check for web search
        try:
            from ..capabilities.web_search import search_web
            capabilities.append('web_search')
        except ImportError:
            pass
        
        # Check for file operations
        try:
            from ..capabilities.file_reader import read_file
            capabilities.append('file_operations')
        except ImportError:
            pass
        
        # Check for task management
        try:
            from ..capabilities.task_manager import add_task_to_notes
            capabilities.append('task_management')
        except ImportError:
            pass
        
        return capabilities
    
    def get_capability_status(self) -> Dict[str, bool]:
        """Get status of all possible capabilities"""
        return {
            'memory': 'memory' in self._detect_active_capabilities(),
            'visual': 'visual' in self._detect_active_capabilities(),
            'web_search': 'web_search' in self._detect_active_capabilities(),
            'file_operations': 'file_operations' in self._detect_active_capabilities(),
            'task_management': 'task_management' in self._detect_active_capabilities(),
        }
    
    def add_custom_instructions(self, name: str, instructions: str):
        """Add custom instruction module"""
        self.instruction_modules[name] = instructions
    
    def preview_prompt(self, max_length: int = 500) -> str:
        """Preview the generated prompt (truncated for display)"""
        full_prompt = self.build_system_prompt()
        if len(full_prompt) <= max_length:
            return full_prompt
        return full_prompt[:max_length] + f"\n\n... (truncated, full length: {len(full_prompt)} chars)"

# Singleton instance for easy access
_composer = None

def get_prompt_composer() -> PromptComposer:
    """Get the global prompt composer instance"""
    global _composer
    if _composer is None:
        _composer = PromptComposer()
    return _composer

def get_system_prompt() -> str:
    """Main entry point - replaces the old monolithic system prompt"""
    composer = get_prompt_composer()
    return composer.build_system_prompt()

# Backward compatibility
def get_current_system_prompt():
    """Alias for backward compatibility"""
    return get_system_prompt()

# Development/debugging helpers
def debug_prompt_composition():
    """Debug helper to see how the prompt is composed"""
    composer = get_prompt_composer()
    
    print("=== PROMPT COMPOSITION DEBUG ===")
    print(f"Detected capabilities: {composer._detect_active_capabilities()}")
    print(f"Capability status: {composer.get_capability_status()}")
    print(f"Available modules: {list(composer.instruction_modules.keys())}")
    print("\n=== COMPOSED PROMPT PREVIEW ===")
    print(composer.preview_prompt(800))
    print(f"\nFull prompt length: {len(composer.build_system_prompt())} characters")

if __name__ == "__main__":
    # Test the composition system
    debug_prompt_composition()
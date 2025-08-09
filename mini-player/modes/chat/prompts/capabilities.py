"""Auto-generated capability descriptions from actual tools"""

def generate_capability_descriptions():
    """Auto-generate capability descriptions from tool definitions"""
    try:
        from .tools import get_mistral_tools
        
        capabilities = []
        for tool in get_mistral_tools():
            func = tool['function']
            name = func['name']
            desc = func['description']
            
            # Group by category
            if 'memory' in name or 'remember' in name or 'recall' in name:
                category = "🧠 Memory"
            elif 'search_web' in name:
                category = "🌐 Web Search"
            elif 'file' in name or 'read' in name:
                category = "📁 File Operations"
            elif 'task' in name or 'note' in name:
                category = "📋 Task Management"
            elif 'screen' in name or 'visual' in name or 'capture' in name:
                category = "👁️ Visual Analysis"
            else:
                category = "🔧 General Tools"
                
            capabilities.append((category, name, desc))
        
        # Group and format
        grouped = {}
        for category, name, desc in capabilities:
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(f"- **{name}**: {desc}")
        
        result = []
        for category, tools in grouped.items():
            result.append(f"### {category}")
            result.extend(tools)
            result.append("")  # Empty line between categories
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error generating capability descriptions: {e}"
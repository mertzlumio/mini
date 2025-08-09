"""
Enhanced file reader with better security, usability, and self-discovery features
"""
import os
import json
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class FileReader:
    """Enhanced file reader with security and usability improvements"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize file reader with base directory
        
        Args:
            base_dir: Base directory for file operations (defaults to mini-player directory)
        """
        if base_dir is None:
            # Auto-detect the mini-player directory
            current_file = Path(__file__).resolve()
            self.base_dir = current_file.parents[3]  # Go up to mini-player root
        else:
            self.base_dir = Path(base_dir).resolve()
        
        # Define allowed directories relative to base_dir
        self.allowed_dirs = [
            "modes/chat/capabilities",
            "modes/chat/prompts", 
            "modes/chat/memory",
            "modes/chat/history",
            "modes/chat/docs",
            "modes/notes",
            "modes/bash", 
            "modes/music",
            "config",
            "docs",
            ".",  # Root directory for config files
        ]
        
        # Supported file extensions
        self.supported_extensions = {
            '.py': 'python',
            '.json': 'json',
            '.txt': 'text',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.toml': 'toml',
            '.env': 'environment',
            '.cfg': 'config',
            '.ini': 'config',
            '.log': 'log'
        }
    
    def read_file(self, file_path: str, max_size_kb: int = 500) -> str:
        """
        Read and return the contents of a file with security checks
        
        Args:
            file_path: Path to the file (relative to base_dir or absolute within allowed dirs)
            max_size_kb: Maximum file size to read in KB (prevents memory issues)
        """
        try:
            # Convert to Path object and resolve
            path = Path(file_path)
            
            # If it's not absolute, make it relative to base_dir
            if not path.is_absolute():
                full_path = (self.base_dir / path).resolve()
            else:
                full_path = path.resolve()
            
            # Security check - ensure path is within allowed directories
            if not self._is_path_allowed(full_path):
                allowed_list = '\n  '.join([f"- {d}" for d in self.allowed_dirs])
                return f"❌ Access denied to '{file_path}'\n\nAllowed directories:\n  {allowed_list}\n\nTip: Use list_available_files() to see what's available."
            
            # Check if file exists
            if not full_path.exists():
                # Provide helpful suggestions
                suggestions = self._suggest_similar_files(full_path)
                error_msg = f"❌ File not found: '{file_path}'"
                if suggestions:
                    error_msg += f"\n\nDid you mean one of these?\n  " + "\n  ".join(f"- {s}" for s in suggestions)
                return error_msg
            
            # Check file size
            file_size_kb = full_path.stat().st_size / 1024
            if file_size_kb > max_size_kb:
                return f"❌ File too large: {file_size_kb:.1f}KB (max: {max_size_kb}KB)\nUse a smaller max_size_kb parameter if needed."
            
            # Determine encoding and read strategy
            encoding = self._detect_encoding(full_path)
            
            with open(full_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Format based on file type
            return self._format_content(content, full_path)
            
        except PermissionError:
            return f"❌ Permission denied reading '{file_path}'"
        except UnicodeDecodeError as e:
            return f"❌ Cannot read '{file_path}': Text encoding error ({e}). File might be binary."
        except Exception as e:
            return f"❌ Error reading '{file_path}': {str(e)}"
    
    def list_available_files(self, directory: str = "modes/chat/capabilities", 
                           recursive: bool = False, 
                           show_sizes: bool = True) -> str:
        """
        List files in a directory with enhanced information
        
        Args:
            directory: Directory to list (relative to base_dir)
            recursive: Whether to search subdirectories
            show_sizes: Whether to show file sizes
        """
        try:
            dir_path = self.base_dir / directory
            
            # Security check
            if not self._is_path_allowed(dir_path):
                return f"❌ Access denied to directory '{directory}'"
            
            if not dir_path.exists():
                return f"❌ Directory not found: '{directory}'"
            
            if not dir_path.is_dir():
                return f"❌ '{directory}' is not a directory"
            
            # Collect files
            files_info = []
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for item_path in dir_path.glob(pattern):
                if item_path.is_file() and self._is_readable_file(item_path):
                    rel_path = item_path.relative_to(self.base_dir)
                    size_info = ""
                    
                    if show_sizes:
                        size_kb = item_path.stat().st_size / 1024
                        if size_kb < 1:
                            size_info = f" ({item_path.stat().st_size}B)"
                        else:
                            size_info = f" ({size_kb:.1f}KB)"
                    
                    file_type = self._get_file_type(item_path)
                    files_info.append({
                        'path': str(rel_path),
                        'name': item_path.name,
                        'type': file_type,
                        'size_info': size_info
                    })
            
            if not files_info:
                return f"📁 No readable files found in '{directory}'"
            
            # Sort by type, then by name
            files_info.sort(key=lambda x: (x['type'], x['name']))
            
            # Format output
            result = [f"📁 Available files in '{directory}':"]
            
            current_type = None
            for file_info in files_info:
                if file_info['type'] != current_type:
                    current_type = file_info['type']
                    result.append(f"\n  {current_type.upper()} files:")
                
                result.append(f"    - {file_info['path']}{file_info['size_info']}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error listing directory '{directory}': {str(e)}"
    
    def search_files(self, query: str, search_dirs: Optional[List[str]] = None) -> str:
        """
        Search for files by name or content
        
        Args:
            query: Search term (filename or content)
            search_dirs: Directories to search (defaults to all allowed dirs)
        """
        if search_dirs is None:
            search_dirs = ["modes/chat", "modes", "config", "docs"]
        
        matches = []
        
        for search_dir in search_dirs:
            try:
                dir_path = self.base_dir / search_dir
                if not dir_path.exists() or not self._is_path_allowed(dir_path):
                    continue
                
                # Search by filename
                for item_path in dir_path.rglob("*"):
                    if (item_path.is_file() and 
                        self._is_readable_file(item_path) and
                        query.lower() in item_path.name.lower()):
                        
                        rel_path = item_path.relative_to(self.base_dir)
                        matches.append(f"📄 {rel_path} (filename match)")
                
                # Search by content (limited to small text files)
                for item_path in dir_path.rglob("*.py"):
                    if (item_path.is_file() and 
                        self._is_readable_file(item_path) and
                        item_path.stat().st_size < 100 * 1024):  # < 100KB
                        
                        try:
                            with open(item_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if query.lower() in content.lower():
                                rel_path = item_path.relative_to(self.base_dir)
                                matches.append(f"📄 {rel_path} (content match)")
                        except:
                            pass  # Skip files that can't be read
                            
            except Exception:
                continue
        
        if not matches:
            return f"🔍 No files found matching '{query}'"
        
        return f"🔍 Search results for '{query}':\n  " + "\n  ".join(matches[:10])  # Limit results
    
    def get_project_structure(self, max_depth: int = 3) -> str:
        """Get an overview of the project structure"""
        try:
            structure = []
            self._build_structure_tree(self.base_dir, structure, max_depth, 0)
            return f"📁 Mini-Player Project Structure:\n" + "\n".join(structure)
        except Exception as e:
            return f"❌ Error building project structure: {str(e)}"
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories"""
        try:
            path = path.resolve()
            base = self.base_dir.resolve()
            
            # Must be under base directory
            if not str(path).startswith(str(base)):
                return False
            
            # Get relative path from base
            rel_path = path.relative_to(base)
            rel_path_str = str(rel_path)
            
            # Check against allowed directories
            for allowed_dir in self.allowed_dirs:
                allowed_path = Path(allowed_dir)
                if (rel_path_str.startswith(str(allowed_path)) or 
                    rel_path_str == str(allowed_path) or
                    allowed_dir == "."):
                    return True
            
            return False
        except (ValueError, OSError):
            return False
    
    def _is_readable_file(self, path: Path) -> bool:
        """Check if a file is readable based on extension"""
        return path.suffix.lower() in self.supported_extensions
    
    def _get_file_type(self, path: Path) -> str:
        """Get the file type description"""
        ext = path.suffix.lower()
        return self.supported_extensions.get(ext, 'unknown')
    
    def _detect_encoding(self, path: Path) -> str:
        """Detect file encoding (basic implementation)"""
        # For now, default to utf-8 with fallback
        return 'utf-8'
    
    def _format_content(self, content: str, path: Path) -> str:
        """Format file content based on file type"""
        ext = path.suffix.lower()
        
        # Add header with file info
        header = f"📄 File: {path.name} ({self._get_file_type(path)})\n{'=' * 50}\n"
        
        if ext == '.json':
            try:
                # Pretty-print JSON
                json_data = json.loads(content)
                formatted_content = json.dumps(json_data, indent=2)
                return header + formatted_content
            except json.JSONDecodeError:
                return header + content
        
        return header + content
    
    def _suggest_similar_files(self, path: Path) -> List[str]:
        """Suggest similar filenames when a file is not found"""
        if not path.parent.exists():
            return []
        
        target_name = path.name.lower()
        suggestions = []
        
        try:
            for item in path.parent.iterdir():
                if (item.is_file() and 
                    self._is_readable_file(item) and
                    item.name.lower() != target_name):
                    
                    # Simple similarity check
                    item_name = item.name.lower()
                    if (target_name in item_name or 
                        item_name in target_name or
                        item.stem.lower() == path.stem.lower()):
                        rel_path = item.relative_to(self.base_dir)
                        suggestions.append(str(rel_path))
        except:
            pass
        
        return suggestions[:3]  # Max 3 suggestions
    
    def _build_structure_tree(self, path: Path, structure: List[str], 
                            max_depth: int, current_depth: int):
        """Build a tree structure representation"""
        if current_depth > max_depth:
            return
        
        indent = "  " * current_depth
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            
            for item in items:
                if item.name.startswith('.') and item.name not in ['.env', '.gitignore']:
                    continue
                
                if item.is_dir():
                    if self._is_path_allowed(item):
                        structure.append(f"{indent}📁 {item.name}/")
                        if current_depth < max_depth:
                            self._build_structure_tree(item, structure, max_depth, current_depth + 1)
                elif self._is_readable_file(item):
                    structure.append(f"{indent}📄 {item.name}")
        except PermissionError:
            structure.append(f"{indent}❌ Permission denied")


# Global instance
_file_reader = None

def get_file_reader() -> FileReader:
    """Get the global file reader instance"""
    global _file_reader
    if _file_reader is None:
        _file_reader = FileReader()
    return _file_reader

# Public API functions (used by AI tools)
def read_file(file_path: str, max_size_kb: int = 500) -> str:
    """
    Read and return the contents of a file with enhanced security and usability
    """
    reader = get_file_reader()
    return reader.read_file(file_path, max_size_kb)

def list_available_files(directory: str = "modes/chat/capabilities", 
                        recursive: bool = False) -> str:
    """
    List files in a directory with enhanced information
    """
    reader = get_file_reader()
    return reader.list_available_files(directory, recursive)

def search_files(query: str, search_dirs: List[str] = None) -> str:
    """
    Search for files by name or content
    """
    reader = get_file_reader()
    return reader.search_files(query, search_dirs)

def get_project_structure() -> str:
    """
    Get an overview of the project structure
    """
    reader = get_file_reader()
    return reader.get_project_structure()

# Development helper
def debug_file_reader():
    """Debug the file reader configuration"""
    reader = get_file_reader()
    print(f"Base directory: {reader.base_dir}")
    print(f"Allowed directories: {reader.allowed_dirs}")
    print(f"Supported extensions: {list(reader.supported_extensions.keys())}")
    print(f"\nProject structure preview:")
    print(reader.get_project_structure())

if __name__ == "__main__":
    debug_file_reader()
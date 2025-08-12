"""
Enhanced bash execution capability for the chat agent
File: modes/chat/capabilities/bash_executor.py
"""
import subprocess
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

class BashExecutor:
    """Secure bash command execution for the chat agent"""
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.command_history = []
        self.max_history = 50
        
        # Security: Define allowed commands (extend as needed)
        self.allowed_commands = {
            # File operations
            'ls', 'dir', 'cat', 'head', 'tail', 'find', 'grep', 'wc', 'sort', 'uniq',
            'file', 'stat', 'du', 'df', 'pwd', 'which', 'whereis',
            
            # Text processing
            'echo', 'printf', 'cut', 'sed', 'awk', 'tr', 'rev',
            
            # System info (safe read-only commands)
            'uname', 'whoami', 'id', 'date', 'uptime', 'ps', 'top', 'htop',
            'free', 'lscpu', 'lsblk', 'lsusb', 'lspci', 'env', 'printenv',
            
            # Network (read-only)
            'ping', 'curl', 'wget', 'nslookup', 'dig', 'host',
            
            # Git operations
            'git',
            
            # Development tools
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
            'java', 'javac', 'gcc', 'g++', 'make', 'cmake',
            
            # Package managers (with restrictions)
            'apt', 'yum', 'brew', 'pacman', 'dnf'
        }
        
        # Dangerous commands to block
        self.blocked_commands = {
            'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd',
            'shutdown', 'reboot', 'halt', 'poweroff', 'init',
            'chmod', 'chown', 'chgrp', 'passwd', 'su', 'sudo',
            'mount', 'umount', 'fsck', 'crontab', 'systemctl',
            'service', 'kill', 'killall', 'pkill'
        }
    
    def execute_command(self, command: str, timeout: int = 30, 
                       safe_mode: bool = True) -> Dict[str, Any]:
        """
        Execute a bash command with security checks
        
        Args:
            command: The command to execute
            timeout: Maximum execution time in seconds
            safe_mode: If True, only allow safe commands
        
        Returns:
            Dict with execution results
        """
        # Clean and validate command
        command = command.strip()
        if not command:
            return self._error_result("Empty command")
        
        # Security check
        if safe_mode and not self._is_command_safe(command):
            return self._error_result(
                f"Command blocked for security: '{command.split()[0]}'\n"
                f"Allowed commands include: ls, cat, grep, find, ps, git, python, etc."
            )
        
        # Handle directory changes specially
        if command.startswith('cd '):
            return self._handle_cd_command(command)
        
        # Record command in history
        self._add_to_history(command)
        
        try:
            # Execute with timeout
            start_time = time.time()
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            execution_time = time.time() - start_time
            
            # Prepare result
            output = result.stdout
            error = result.stderr
            
            # Combine output and error if both exist
            if output and error:
                combined_output = f"{output}\nSTDERR: {error}"
            elif error:
                combined_output = f"STDERR: {error}"
            else:
                combined_output = output or "(no output)"
            
            return {
                'success': result.returncode == 0,
                'output': combined_output,
                'return_code': result.returncode,
                'execution_time': execution_time,
                'working_directory': self.working_dir,
                'command': command
            }
            
        except subprocess.TimeoutExpired:
            return self._error_result(f"Command timed out after {timeout} seconds")
        except FileNotFoundError:
            return self._error_result(f"Command not found: '{command.split()[0]}'")
        except Exception as e:
            return self._error_result(f"Execution error: {str(e)}")
    
    def _is_command_safe(self, command: str) -> bool:
        """Check if a command is safe to execute"""
        # Get the base command (first word)
        base_command = command.split()[0].lower()
        
        # Block dangerous commands
        if base_command in self.blocked_commands:
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            '&&', '||', ';', '|', '>', '>>', '<', '$(', '`',
            'rm -', 'rm /', 'format', 'del /', 'sudo', 'su -'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        
        # Allow if explicitly in allowed list
        if base_command in self.allowed_commands:
            return True
        
        # Allow relative path execution for scripts in current directory
        if base_command.startswith('./') and not '..' in command:
            return True
        
        return False
    
    def _handle_cd_command(self, command: str) -> Dict[str, Any]:
        """Handle directory change commands"""
        try:
            # Parse target directory
            parts = command.split(maxsplit=1)
            if len(parts) == 1:
                # cd with no arguments goes to home
                target = os.path.expanduser("~")
            else:
                target = parts[1]
            
            # Resolve path
            if not os.path.isabs(target):
                target = os.path.join(self.working_dir, target)
            
            target = os.path.abspath(target)
            
            # Check if directory exists
            if not os.path.isdir(target):
                return self._error_result(f"Directory not found: {target}")
            
            # Update working directory
            old_dir = self.working_dir
            self.working_dir = target
            
            return {
                'success': True,
                'output': f"Changed directory from {old_dir} to {target}",
                'return_code': 0,
                'execution_time': 0.0,
                'working_directory': self.working_dir,
                'command': command
            }
            
        except Exception as e:
            return self._error_result(f"Directory change failed: {str(e)}")
    
    def _error_result(self, message: str) -> Dict[str, Any]:
        """Create a standardized error result"""
        return {
            'success': False,
            'output': message,
            'return_code': -1,
            'execution_time': 0.0,
            'working_directory': self.working_dir,
            'command': ''
        }
    
    def _add_to_history(self, command: str):
        """Add command to history"""
        self.command_history.append({
            'command': command,
            'timestamp': time.time(),
            'working_dir': self.working_dir
        })
        
        # Keep history size manageable
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    def get_command_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history"""
        return self.command_history[-count:]
    
    def get_working_directory(self) -> str:
        """Get current working directory"""
        return self.working_dir
    
    def set_working_directory(self, path: str) -> bool:
        """Set working directory"""
        try:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                self.working_dir = abs_path
                return True
            return False
        except:
            return False

# Global bash executor instance
_bash_executor = None

def get_bash_executor() -> BashExecutor:
    """Get the global bash executor instance"""
    global _bash_executor
    if _bash_executor is None:
        _bash_executor = BashExecutor()
    return _bash_executor

# Tool functions for the agent (these get called by Mistral)
def execute_bash_command(command: str, timeout: int = 30, safe_mode: bool = True) -> str:
    """
    Execute a bash command securely
    
    Args:
        command: The bash command to execute
        timeout: Maximum execution time (default: 30 seconds)
        safe_mode: Enable security restrictions (default: True)
    """
    executor = get_bash_executor()
    result = executor.execute_command(command, timeout, safe_mode)
    
    if result['success']:
        return f"✅ Command executed successfully in {result['execution_time']:.2f}s\n" \
               f"Working directory: {result['working_directory']}\n" \
               f"Output:\n{result['output']}"
    else:
        return f"❌ Command failed (exit code: {result['return_code']})\n" \
               f"Working directory: {result['working_directory']}\n" \
               f"Error:\n{result['output']}"

def get_current_directory() -> str:
    """Get the current working directory for bash operations"""
    executor = get_bash_executor()
    current_dir = executor.get_working_directory()
    
    try:
        # Get directory contents for context
        contents = os.listdir(current_dir)
        files = [f for f in contents if os.path.isfile(os.path.join(current_dir, f))]
        dirs = [d for d in contents if os.path.isdir(os.path.join(current_dir, d))]
        
        result = f"📁 Current directory: {current_dir}\n"
        if dirs:
            result += f"Directories ({len(dirs)}): {', '.join(dirs[:10])}"
            if len(dirs) > 10:
                result += f" ... and {len(dirs)-10} more"
            result += "\n"
        
        if files:
            result += f"Files ({len(files)}): {', '.join(files[:10])}"
            if len(files) > 10:
                result += f" ... and {len(files)-10} more"
        
        return result
        
    except Exception as e:
        return f"📁 Current directory: {current_dir}\n❌ Could not list contents: {str(e)}"

def change_directory(path: str) -> str:
    """Change the working directory for bash operations"""
    executor = get_bash_executor()
    
    if executor.set_working_directory(path):
        return f"✅ Changed directory to: {executor.get_working_directory()}"
    else:
        return f"❌ Could not change to directory: {path} (directory may not exist)"

def get_bash_command_history(count: int = 5) -> str:
    """Get recent bash command history"""
    executor = get_bash_executor()
    history = executor.get_command_history(count)
    
    if not history:
        return "📚 No bash commands executed yet"
    
    result = f"📚 Recent bash commands (last {len(history)}):\n"
    for i, entry in enumerate(reversed(history), 1):
        timestamp = time.strftime("%H:%M:%S", time.localtime(entry['timestamp']))
        result += f"  {i}. [{timestamp}] {entry['command']}\n"
    
    return result

# For debugging
def debug_bash_executor():
    """Debug the bash executor"""
    executor = get_bash_executor()
    print(f"Working directory: {executor.working_directory}")
    print(f"Allowed commands: {len(executor.allowed_commands)} commands")
    print(f"Blocked commands: {len(executor.blocked_commands)} commands")
    print(f"Command history: {len(executor.command_history)} entries")
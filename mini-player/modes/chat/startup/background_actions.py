# Background Agent System for Mini

import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import schedule

@dataclass
class MonitoringTask:
    """A task that Mini monitors in the background"""
    id: str
    user_request: str  # Original user request
    task_type: str     # "news_tracking", "deadline_monitoring", etc.
    keywords: List[str]
    check_frequency: str  # "hourly", "daily", "weekly"
    created: datetime
    last_checked: datetime
    status: str        # "active", "paused", "completed"
    context: Dict      # Additional task-specific data
    importance: str    # "low", "medium", "high", "critical"

@dataclass
class Finding:
    """Something Mini discovered and wants to share"""
    id: str
    task_id: str
    title: str
    content: str
    url: Optional[str]
    importance: str
    discovered: datetime
    notified: bool = False

class BackgroundAgent:
    """Silent background agent that monitors and tracks things for user"""
    
    def __init__(self, memory_dir: str, api_client, console=None):
        self.memory_dir = memory_dir
        self.api_client = api_client
        self.console = console  # For notifications
        
        self.monitoring_tasks: List[MonitoringTask] = []
        self.findings: List[Finding] = []
        self.is_running = False
        self.worker_thread = None
        
        self.load_state()
        self.setup_scheduler()
    
    def add_monitoring_task(self, user_request: str, task_type: str, 
                          keywords: List[str], frequency: str = "daily",
                          importance: str = "medium") -> str:
        """Add a new background monitoring task"""
        
        task_id = f"task_{int(time.time())}"
        task = MonitoringTask(
            id=task_id,
            user_request=user_request,
            task_type=task_type,
            keywords=keywords,
            check_frequency=frequency,
            created=datetime.now(),
            last_checked=datetime.now(),
            status="active",
            context={},
            importance=importance
        )
        
        self.monitoring_tasks.append(task)
        self.save_state()
        
        # Schedule the task
        self.schedule_task(task)
        
        return task_id
    
    def schedule_task(self, task: MonitoringTask):
        """Schedule a monitoring task"""
        
        def run_task():
            if task.status == "active":
                self.execute_monitoring_task(task)
        
        if task.check_frequency == "hourly":
            schedule.every().hour.do(run_task)
        elif task.check_frequency == "daily":
            schedule.every().day.at("09:00").do(run_task)  # Morning check
            schedule.every().day.at("18:00").do(run_task)  # Evening check
        elif task.check_frequency == "weekly":
            schedule.every().monday.at("09:00").do(run_task)
    
    def execute_monitoring_task(self, task: MonitoringTask):
        """Execute a single monitoring task silently"""
        
        try:
            if task.task_type == "news_tracking":
                self.check_news_updates(task)
            elif task.task_type == "deadline_monitoring":
                self.check_deadline_updates(task)
            elif task.task_type == "website_monitoring":
                self.check_website_changes(task)
            
            task.last_checked = datetime.now()
            self.save_state()
            
        except Exception as e:
            print(f"Background task {task.id} failed: {e}")
    
    def check_news_updates(self, task: MonitoringTask):
        """Check for news updates related to keywords"""
        
        # Build search query
        search_query = " ".join(task.keywords[:3])  # Limit to avoid long queries
        
        # Use web search (this should be silent - no console output)
        try:
            # Call your existing web search capability
            search_results = self.silent_web_search(search_query)
            
            # Analyze results for important updates
            findings = self.analyze_search_results(task, search_results)
            
            # Add any important findings
            for finding in findings:
                self.add_finding(finding)
                
        except Exception as e:
            print(f"News check failed for task {task.id}: {e}")
    
    def silent_web_search(self, query: str) -> List[Dict]:
        """Perform web search without showing it to user"""
        
        # This would use your existing web search tools
        # But capture results without displaying them
        
        try:
            # Mock implementation - replace with actual search
            from modes.chat.capabilities.web_tools import search_web
            
            # Capture search results silently
            results = search_web(query, max_results=5)
            return results
            
        except Exception as e:
            print(f"Silent search failed: {e}")
            return []
    
    def analyze_search_results(self, task: MonitoringTask, results: List[Dict]) -> List[Finding]:
        """Analyze search results to find important updates"""
        
        findings = []
        
        for result in results:
            # Check if this is actually new/important
            if self.is_significant_update(task, result):
                finding = Finding(
                    id=f"finding_{int(time.time())}_{len(findings)}",
                    task_id=task.id,
                    title=result.get('title', 'Update found'),
                    content=result.get('snippet', ''),
                    url=result.get('url'),
                    importance=self.assess_importance(task, result),
                    discovered=datetime.now()
                )
                findings.append(finding)
        
        return findings
    
    def is_significant_update(self, task: MonitoringTask, result: Dict) -> bool:
        """Determine if a search result represents a significant update"""
        
        # Check if we've seen this before
        title = result.get('title', '').lower()
        url = result.get('url', '')
        
        for existing_finding in self.findings:
            if existing_finding.task_id == task.id:
                if (title in existing_finding.title.lower() or 
                    url == existing_finding.url):
                    return False  # Already found this
        
        # Check for important keywords
        important_keywords = [
            'registration', 'deadline', 'announced', 'released', 
            'updated', 'new', 'breaking', 'urgent', 'important'
        ]
        
        content = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
        
        return any(keyword in content for keyword in important_keywords)
    
    def assess_importance(self, task: MonitoringTask, result: Dict) -> str:
        """Assess how important this finding is"""
        
        content = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
        
        # Critical keywords
        if any(word in content for word in ['deadline', 'urgent', 'last date', 'closing soon']):
            return "critical"
        
        # High importance
        if any(word in content for word in ['registration', 'announced', 'released']):
            return "high"
        
        # Medium importance  
        if any(word in content for word in ['updated', 'new', 'changes']):
            return "medium"
        
        return "low"
    
    def add_finding(self, finding: Finding):
        """Add a new finding and potentially notify user"""
        
        self.findings.append(finding)
        self.save_state()
        
        # Notify user if important enough
        if finding.importance in ["high", "critical"] and not finding.notified:
            self.notify_user(finding)
            finding.notified = True
    
    def notify_user(self, finding: Finding):
        """Notify user about an important finding"""
        
        if not self.console:
            return
        
        # Get the original task for context
        task = next((t for t in self.monitoring_tasks if t.id == finding.task_id), None)
        if not task:
            return
        
        # Format notification based on importance
        if finding.importance == "critical":
            icon = "🚨"
            tag = "error"
        elif finding.importance == "high":
            icon = "🔔"
            tag = "accent"
        else:
            icon = "ℹ️"
            tag = "dim"
        
        # Insert notification into console
        self.console.insert("end", f"\n{icon} Background Update: {finding.title}\n", tag)
        
        if finding.content:
            self.console.insert("end", f"   {finding.content[:100]}...\n", "dim")
        
        if finding.url:
            self.console.insert("end", f"   Source: {finding.url}\n", "dim")
        
        self.console.insert("end", f"   (Related to: {task.user_request})\n", "dim")
        self.console.see("end")
    
    def start(self):
        """Start the background agent"""
        
        if self.is_running:
            return
        
        self.is_running = True
        
        def worker():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        
        print("🤖 Background agent started - monitoring tasks silently")
    
    def stop(self):
        """Stop the background agent"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def get_active_tasks(self) -> List[MonitoringTask]:
        """Get list of active monitoring tasks"""
        return [task for task in self.monitoring_tasks if task.status == "active"]
    
    def get_recent_findings(self, hours: int = 24) -> List[Finding]:
        """Get recent findings"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [f for f in self.findings if f.discovered > cutoff]
    
    def pause_task(self, task_id: str):
        """Pause a monitoring task"""
        for task in self.monitoring_tasks:
            if task.id == task_id:
                task.status = "paused"
                break
        self.save_state()
    
    def resume_task(self, task_id: str):
        """Resume a monitoring task"""
        for task in self.monitoring_tasks:
            if task.id == task_id:
                task.status = "active"
                break
        self.save_state()
    
    def save_state(self):
        """Save agent state to disk"""
        state = {
            "tasks": [
                {
                    "id": task.id,
                    "user_request": task.user_request,
                    "task_type": task.task_type,
                    "keywords": task.keywords,
                    "check_frequency": task.check_frequency,
                    "created": task.created.isoformat(),
                    "last_checked": task.last_checked.isoformat(),
                    "status": task.status,
                    "context": task.context,
                    "importance": task.importance
                }
                for task in self.monitoring_tasks
            ],
            "findings": [
                {
                    "id": finding.id,
                    "task_id": finding.task_id,
                    "title": finding.title,
                    "content": finding.content,
                    "url": finding.url,
                    "importance": finding.importance,
                    "discovered": finding.discovered.isoformat(),
                    "notified": finding.notified
                }
                for finding in self.findings
            ]
        }
        
        import os
        os.makedirs(self.memory_dir, exist_ok=True)
        
        with open(f"{self.memory_dir}/background_agent.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load agent state from disk"""
        try:
            with open(f"{self.memory_dir}/background_agent.json", "r") as f:
                state = json.load(f)
            
            # Load tasks
            self.monitoring_tasks = []
            for task_data in state.get("tasks", []):
                task = MonitoringTask(
                    id=task_data["id"],
                    user_request=task_data["user_request"],
                    task_type=task_data["task_type"],
                    keywords=task_data["keywords"],
                    check_frequency=task_data["check_frequency"],
                    created=datetime.fromisoformat(task_data["created"]),
                    last_checked=datetime.fromisoformat(task_data["last_checked"]),
                    status=task_data["status"],
                    context=task_data["context"],
                    importance=task_data["importance"]
                )
                self.monitoring_tasks.append(task)
            
            # Load findings
            self.findings = []
            for finding_data in state.get("findings", []):
                finding = Finding(
                    id=finding_data["id"],
                    task_id=finding_data["task_id"],
                    title=finding_data["title"],
                    content=finding_data["content"],
                    url=finding_data["url"],
                    importance=finding_data["importance"],
                    discovered=datetime.fromisoformat(finding_data["discovered"]),
                    notified=finding_data["notified"]
                )
                self.findings.append(finding)
                
        except FileNotFoundError:
            # No saved state, start fresh
            pass
        except Exception as e:
            print(f"Error loading background agent state: {e}")


# Integration with chat commands
class BackgroundAgentCommands:
    """Chat commands for managing background agent"""
    
    def __init__(self, agent: BackgroundAgent):
        self.agent = agent
    
    def handle_monitor_command(self, user_input: str, console) -> bool:
        """Handle monitoring-related commands"""
        
        input_lower = user_input.lower()
        
        # Track/monitor commands
        if any(phrase in input_lower for phrase in [
            "keep track of", "monitor", "follow up on", "watch for", 
            "let me know when", "alert me about"
        ]):
            return self.setup_monitoring(user_input, console)
        
        # Status commands
        elif input_lower in ["monitoring status", "what are you tracking", "background tasks"]:
            return self.show_monitoring_status(console)
        
        # Recent findings
        elif input_lower in ["any updates", "background updates", "recent findings"]:
            return self.show_recent_findings(console)
        
        return False
    
    def setup_monitoring(self, user_input: str, console) -> bool:
        """Set up a new monitoring task"""
        
        # Extract what to monitor (simple keyword extraction)
        keywords = self.extract_keywords(user_input)
        
        if not keywords:
            console.insert("end", "❌ I couldn't identify what to monitor. Try: 'Keep track of GATE exam updates'\n", "error")
            return True
        
        # Determine task type and frequency
        task_type = self.determine_task_type(user_input)
        frequency = self.determine_frequency(user_input)
        importance = self.determine_importance(user_input)
        
        # Add monitoring task
        task_id = self.agent.add_monitoring_task(
            user_request=user_input,
            task_type=task_type,
            keywords=keywords,
            frequency=frequency,
            importance=importance
        )
        
        console.insert("end", f"✅ Now monitoring: {' '.join(keywords)}\n", "success")
        console.insert("end", f"   Checking {frequency} for updates\n", "dim")
        console.insert("end", f"   I'll notify you when I find something important\n", "dim")
        
        return True
    
    def extract_keywords(self, user_input: str) -> List[str]:
        """Extract monitoring keywords from user input"""
        
        # Simple extraction - could be improved with NLP
        important_phrases = [
            "gate exam", "gate 2025", "gate registration",
            "neet exam", "jee exam", "upsc exam",
            "admission", "deadline", "notification"
        ]
        
        input_lower = user_input.lower()
        keywords = []
        
        for phrase in important_phrases:
            if phrase in input_lower:
                keywords.extend(phrase.split())
        
        # If no specific phrases found, extract key words
        if not keywords:
            words = input_lower.split()
            # Remove common words
            stop_words = {"keep", "track", "of", "monitor", "follow", "up", "on", "let", "me", "know", "when"}
            keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        return keywords[:5]  # Limit to 5 keywords
    
    def determine_task_type(self, user_input: str) -> str:
        """Determine the type of monitoring task"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["news", "update", "announcement"]):
            return "news_tracking"
        elif any(word in input_lower for word in ["deadline", "date", "registration"]):
            return "deadline_monitoring"
        elif any(word in input_lower for word in ["website", "page"]):
            return "website_monitoring"
        else:
            return "news_tracking"  # Default
    
    def determine_frequency(self, user_input: str) -> str:
        """Determine how often to check"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["urgent", "critical", "important"]):
            return "hourly"
        elif any(word in input_lower for word in ["daily", "every day"]):
            return "daily"
        elif any(word in input_lower for word in ["weekly", "every week"]):
            return "weekly"
        else:
            return "daily"  # Default
    
    def determine_importance(self, user_input: str) -> str:
        """Determine importance level"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ["urgent", "critical", "very important"]):
            return "critical"
        elif any(word in input_lower for word in ["important", "high priority"]):
            return "high"
        else:
            return "medium"  # Default
    
    def show_monitoring_status(self, console) -> bool:
        """Show current monitoring status"""
        active_tasks = self.agent.get_active_tasks()
        
        if not active_tasks:
            console.insert("end", "📋 No active monitoring tasks\n", "dim")
            return True
        
        console.insert("end", f"📋 Background Monitoring ({len(active_tasks)} active):\n", "accent")
        
        for task in active_tasks:
            days_ago = (datetime.now() - task.created).days
            console.insert("end", f"   • {task.user_request[:50]}...\n")
            console.insert("end", f"     Started {days_ago} days ago, checking {task.check_frequency}\n", "dim")
        
        return True
    
    def show_recent_findings(self, console) -> bool:
        """Show recent findings"""
        findings = self.agent.get_recent_findings(hours=48)  # Last 48 hours
        
        if not findings:
            console.insert("end", "📊 No recent updates from background monitoring\n", "dim")
            return True
        
        console.insert("end", f"📊 Recent Background Findings ({len(findings)}):\n", "accent")
        
        for finding in findings[-5:]:  # Show last 5
            hours_ago = int((datetime.now() - finding.discovered).total_seconds() / 3600)
            console.insert("end", f"   • {finding.title}\n")
            console.insert("end", f"     {hours_ago}h ago • {finding.importance} importance\n", "dim")
        
        return True


# Simple integration function
def initialize_background_agent(memory_dir: str, api_client, console) -> BackgroundAgent:
    """Initialize and start the background agent"""
    
    agent = BackgroundAgent(memory_dir, api_client, console)
    agent.start()
    
    return agent


#     # In handlers.py, replace the startup initialization with:
# def initialize_background_agent_if_needed(console, memory_dir):
#     try:
#         from modes.chat.background_agent import initialize_background_agent
#         from modes.chat.api_client import call_mistral_api
        
#         agent = initialize_background_agent(memory_dir, call_mistral_api, console)
#         console.insert(END, "🤖 Background monitoring ready\n", "dim")
#         return agent
#     except Exception as e:
#         console.insert(END, f"Background agent unavailable: {e}\n", "dim")
#         return None
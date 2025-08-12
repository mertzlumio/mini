# modes/chat/startup/autonomous_startup.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random

class MiniTaskManager:
    """Manages Mini's own internal tasks and goals"""
    
    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        self.tasks_file = os.path.join(memory_dir, 'mini_tasks.json')
        self.state_file = os.path.join(memory_dir, 'mini_state.json')
        
        os.makedirs(memory_dir, exist_ok=True)
        
        self.internal_tasks = self._load_internal_tasks()
        self.mini_state = self._load_mini_state()
    
    def _load_internal_tasks(self) -> List[Dict]:
        """Load Mini's own task list"""
        if not os.path.exists(self.tasks_file):
            return self._create_default_tasks()
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading Mini tasks: {e}")
            return self._create_default_tasks()
    
    def _create_default_tasks(self) -> List[Dict]:
        """Create default internal tasks for Mini"""
        return [
            {
                "id": "check_user_context",
                "description": "Check user's recent work and project status",
                "priority": "high",
                "type": "startup",
                "created": datetime.now().isoformat(),
                "status": "pending"
            },
            {
                "id": "review_memory",
                "description": "Review stored facts and recent conversations",
                "priority": "medium", 
                "type": "maintenance",
                "created": datetime.now().isoformat(),
                "status": "pending"
            },
            {
                "id": "plan_assistance",
                "description": "Plan how to be helpful based on context",
                "priority": "high",
                "type": "planning",
                "created": datetime.now().isoformat(),
                "status": "pending"
            }
        ]
    
    def _load_mini_state(self) -> Dict:
        """Load Mini's current state and memory"""
        if not os.path.exists(self.state_file):
            return self._create_default_state()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading Mini state: {e}")
            return self._create_default_state()
    
    def _create_default_state(self) -> Dict:
        """Create default state for Mini"""
        return {
            "last_startup": None,
            "interaction_count": 0,
            "user_preferences": {},
            "pending_followups": [],
            "work_context": {},
            "mini_personality_state": "helpful_eager"
        }
    
    def add_internal_task(self, description: str, priority: str = "medium", task_type: str = "general"):
        """Add a new internal task for Mini"""
        task = {
            "id": f"task_{len(self.internal_tasks)}_{datetime.now().strftime('%H%M%S')}",
            "description": description,
            "priority": priority,
            "type": task_type,
            "created": datetime.now().isoformat(),
            "status": "pending"
        }
        self.internal_tasks.append(task)
        self._save_tasks()
    
    def complete_task(self, task_id: str):
        """Mark a task as completed"""
        for task in self.internal_tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
                break
        self._save_tasks()
    
    def get_pending_tasks(self, task_type: str = None) -> List[Dict]:
        """Get pending tasks, optionally filtered by type"""
        pending = [t for t in self.internal_tasks if t["status"] == "pending"]
        if task_type:
            pending = [t for t in pending if t["type"] == task_type]
        return sorted(pending, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)
    
    def update_state(self, key: str, value: Any):
        """Update Mini's internal state"""
        self.mini_state[key] = value
        self._save_state()
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.internal_tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving Mini tasks: {e}")
    
    def _save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.mini_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving Mini state: {e}")


class StartupPromptGenerator:
    """Generates contextual startup prompts for Mini"""
    
    def __init__(self, task_manager: MiniTaskManager, memory_manager):
        self.task_manager = task_manager
        self.memory_manager = memory_manager
        
        # Greeting templates based on context
        self.greeting_templates = {
            "first_time": [
                "Hello! I'm Mini, your AI assistant. I'm setting up my systems and getting ready to help you. What are you working on today?",
                "Hi there! I'm Mini. I'm just getting oriented - tell me, what's on your agenda today?",
                "Hey! I'm Mini, and I'm excited to start working with you. What should we tackle first?"
            ],
            "returning_user": [
                "Welcome back! I've been thinking about our last conversation about {context}. Ready to continue?",
                "Good to see you again! I remember we were working on {context}. What's next?",
                "Hi! I've been keeping track of things. Last time we discussed {context} - how did that go?"
            ],
            "new_day": [
                "Good {time_period}! I've been reviewing what we have on our plate. Ready for a productive day?",
                "Morning! I checked our progress on {recent_work} - looking good! What's the priority today?",
                "Hey! Fresh day, fresh possibilities. I have some ideas about what we could tackle today."
            ],
            "project_focused": [
                "I've been analyzing your {project_name} project. I have {task_count} ideas to help move it forward. Interested?",
                "Your {project_name} is looking great! I noticed {observation} - want to work on that?",
                "Ready to make progress on {project_name}? I've prepared some suggestions."
            ]
        }
        
        self.followup_templates = [
            "Based on what I know about your work style, I think we should {suggestion}. Sound good?",
            "I have {count} things on my radar: {items}. Which interests you most?",
            "Here's what I'm thinking: {plan}. Want to go with this approach?",
            "I noticed {observation}. Should we {action} or focus on something else?"
        ]
    
    def generate_startup_sequence(self) -> List[Dict]:
        """Generate complete startup sequence with prompts"""
        
        # Determine context
        context = self._analyze_startup_context()
        
        # Generate greeting
        greeting = self._generate_contextual_greeting(context)
        
        # Generate initial plan
        initial_plan = self._generate_initial_plan(context)
        
        # Create startup sequence
        sequence = [
            {
                "type": "internal_startup",
                "message": "🔄 Mini starting up...",
                "actions": ["load_memory", "check_tasks", "analyze_context"]
            },
            {
                "type": "greeting",
                "message": greeting,
                "wait_for_response": True
            },
            {
                "type": "planning",
                "message": initial_plan,
                "wait_for_response": True
            }
        ]
        
        return sequence
    
    def _analyze_startup_context(self) -> Dict:
        """Analyze current context for startup"""
        
        context = {
            "is_first_time": self.task_manager.mini_state.get("last_startup") is None,
            "time_period": self._get_time_period(),
            "recent_memories": self._get_recent_context(),
            "pending_tasks": self.task_manager.get_pending_tasks(),
            "user_preferences": self.task_manager.mini_state.get("user_preferences", {}),
            "last_interaction": self.task_manager.mini_state.get("last_startup")
        }
        
        # Determine startup type
        if context["is_first_time"]:
            context["startup_type"] = "first_time"
        elif self._is_new_day(context["last_interaction"]):
            context["startup_type"] = "new_day"
        elif context["recent_memories"]:
            context["startup_type"] = "project_focused"
        else:
            context["startup_type"] = "returning_user"
        
        return context
    
    def _get_time_period(self) -> str:
        """Get appropriate time greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def _get_recent_context(self) -> Dict:
        """Get recent work context from memory"""
        try:
            # Get recent facts and summaries
            recent_facts = self.memory_manager.semantic_memory.get_recent_facts(days=2, limit=5)
            recent_summaries = self.memory_manager.semantic_memory.summaries[-2:] if self.memory_manager.semantic_memory.summaries else []
            
            context = {}
            
            if recent_facts:
                # Extract project/work related facts
                work_facts = [f for f in recent_facts if any(keyword in f.content.lower() 
                             for keyword in ['project', 'work', 'code', 'bug', 'feature'])]
                if work_facts:
                    context["recent_work"] = work_facts[0].content
                    context["work_type"] = work_facts[0].memory_type
            
            if recent_summaries:
                latest_summary = recent_summaries[-1].get('summary', '')
                if latest_summary:
                    context["last_session"] = latest_summary[:100] + "..." if len(latest_summary) > 100 else latest_summary
            
            return context
            
        except Exception as e:
            print(f"Error getting recent context: {e}")
            return {}
    
    def _is_new_day(self, last_startup: str) -> bool:
        """Check if it's a new day since last startup"""
        if not last_startup:
            return True
        
        try:
            last_date = datetime.fromisoformat(last_startup).date()
            today = datetime.now().date()
            return today > last_date
        except:
            return True
    
    def _generate_contextual_greeting(self, context: Dict) -> str:
        """Generate appropriate greeting based on context"""
        startup_type = context["startup_type"]
        templates = self.greeting_templates[startup_type]
        
        # Select template
        greeting_template = random.choice(templates)
        
        # Fill in context variables
        if startup_type == "returning_user" and context.get("recent_memories"):
            recent_work = context["recent_memories"].get("recent_work", "your project")
            greeting_template = greeting_template.format(context=recent_work)
        elif startup_type == "new_day":
            time_period = context["time_period"]
            recent_work = context["recent_memories"].get("recent_work", "our tasks")
            greeting_template = greeting_template.format(
                time_period=time_period,
                recent_work=recent_work
            )
        elif startup_type == "project_focused":
            recent_context = context["recent_memories"]
            project_name = recent_context.get("recent_work", "your current project")
            task_count = len(context["pending_tasks"])
            observation = "some interesting patterns" # Could be more sophisticated
            greeting_template = greeting_template.format(
                project_name=project_name,
                task_count=task_count,
                observation=observation
            )
        
        return greeting_template
    
    def _generate_initial_plan(self, context: Dict) -> str:
        """Generate initial plan/agenda based on context"""
        
        pending_tasks = context["pending_tasks"]
        user_prefs = context["user_preferences"]
        
        # Build agenda items
        agenda_items = []
        
        # Add Mini's internal tasks
        high_priority_tasks = [t for t in pending_tasks if t["priority"] == "high"]
        if high_priority_tasks:
            for task in high_priority_tasks[:2]:  # Limit to 2 high priority
                agenda_items.append(f"Check {task['description'].lower()}")
        
        # Add memory-based suggestions
        recent_memories = context.get("recent_memories", {})
        if recent_memories.get("recent_work"):
            agenda_items.append(f"Continue work on {recent_memories['recent_work']}")
        
        # Add based on user preferences
        if user_prefs.get("morning_routine"):
            agenda_items.append("Review daily priorities")
        
        # Default suggestions if no specific context
        if not agenda_items:
            agenda_items = [
                "Review what you're currently working on",
                "Check for any urgent items",
                "Plan today's priorities"
            ]
        
        # Format the plan
        if len(agenda_items) == 1:
            return f"I think we should start by: {agenda_items[0]}. Does that work for you?"
        elif len(agenda_items) == 2:
            return f"I have two main things in mind: {agenda_items[0]} and {agenda_items[1]}. Which should we tackle first?"
        else:
            items_text = ", ".join(agenda_items[:-1]) + f", and {agenda_items[-1]}"
            return f"Here's what I'm thinking for today: {items_text}. What sounds most important to you?"


class AutonomousStartupManager:
    """Main manager for Mini's autonomous startup process"""
    
    def __init__(self, memory_dir: str, memory_manager, api_client):
        self.memory_dir = memory_dir
        self.memory_manager = memory_manager
        self.api_client = api_client
        
        self.task_manager = MiniTaskManager(memory_dir)
        self.prompt_generator = StartupPromptGenerator(self.task_manager, memory_manager)
        
        self.startup_sequence = []
        self.current_step = 0
        self.awaiting_response = False
    
    def initiate_startup(self) -> Dict:
        """Start the autonomous startup sequence"""
        print("🚀 Mini autonomous startup initiated...")
        
        # Update startup timestamp
        self.task_manager.update_state("last_startup", datetime.now().isoformat())
        
        # Generate startup sequence
        self.startup_sequence = self.prompt_generator.generate_startup_sequence()
        self.current_step = 0
        
        # Execute first step
        return self._execute_current_step()
    
    def _execute_current_step(self) -> Dict:
        """Execute current step in startup sequence"""
        if self.current_step >= len(self.startup_sequence):
            return {"type": "complete", "message": "Startup sequence complete!"}
        
        step = self.startup_sequence[self.current_step]
        
        if step["type"] == "internal_startup":
            # Execute internal actions
            self._execute_internal_actions(step.get("actions", []))
            # Move to next step immediately
            self.current_step += 1
            return self._execute_current_step()
        
        elif step["type"] in ["greeting", "planning"]:
            # Set awaiting response if needed
            self.awaiting_response = step.get("wait_for_response", False)
            return {
                "type": step["type"],
                "message": step["message"],
                "awaiting_response": self.awaiting_response
            }
        
        return {"type": "error", "message": "Unknown step type"}
    
    def _execute_internal_actions(self, actions: List[str]):
        """Execute Mini's internal startup actions"""
        for action in actions:
            if action == "load_memory":
                # Load and process memory
                stats = self.memory_manager.get_stats()
                print(f"📊 Loaded memory: {stats['total_facts']} facts, {stats['total_summaries']} summaries")
                
            elif action == "check_tasks":
                # Review internal tasks
                pending = self.task_manager.get_pending_tasks()
                print(f"📋 Internal tasks: {len(pending)} pending")
                
            elif action == "analyze_context":
                # Analyze current context
                print("🔍 Analyzing context and user patterns...")
                # Could add more sophisticated analysis here
    
    def process_user_response(self, user_input: str) -> Dict:
        """Process user response and continue startup sequence"""
        if not self.awaiting_response:
            return {"type": "error", "message": "Not awaiting response"}
        
        # Process the response (could be more sophisticated)
        self._process_response_for_context(user_input)
        
        # Move to next step
        self.current_step += 1
        self.awaiting_response = False
        
        # Execute next step
        return self._execute_current_step()
    
    def _process_response_for_context(self, user_input: str):
        """Process user response to build context for future interactions"""
        # Simple keyword analysis (could be enhanced with NLP)
        user_input_lower = user_input.lower()
        
        # Detect work focus
        if any(word in user_input_lower for word in ['code', 'project', 'bug', 'feature', 'work']):
            self.task_manager.add_internal_task(
                f"Support user with: {user_input[:50]}...",
                priority="high",
                task_type="user_support"
            )
        
        # Detect preferences
        if any(word in user_input_lower for word in ['prefer', 'like', 'want', 'need']):
            # Could extract and store preferences
            pass
        
        # Store response context
        self.task_manager.update_state("last_user_input", user_input)
    
    def get_startup_status(self) -> Dict:
        """Get current startup status"""
        return {
            "current_step": self.current_step,
            "total_steps": len(self.startup_sequence),
            "awaiting_response": self.awaiting_response,
            "progress": f"{self.current_step}/{len(self.startup_sequence)}"
        }
    
    def is_startup_complete(self) -> bool:
        """Check if startup sequence is complete"""
        return self.current_step >= len(self.startup_sequence)


# Integration functions for existing chat system
def initialize_autonomous_startup(memory_dir: str, memory_manager, api_client):
    """Initialize the autonomous startup system"""
    return AutonomousStartupManager(memory_dir, memory_manager, api_client)

def execute_startup_sequence(startup_manager: AutonomousStartupManager) -> Dict:
    """Execute the startup sequence"""
    return startup_manager.initiate_startup()

# Test function
def test_startup_system():
    """Test the startup system"""
    import tempfile
    
    # Mock memory manager
    class MockMemoryManager:
        def __init__(self):
            self.semantic_memory = MockSemanticMemory()
        
        def get_stats(self):
            return {"total_facts": 5, "total_summaries": 2}
    
    class MockSemanticMemory:
        def __init__(self):
            self.summaries = [{"summary": "User worked on Python project"}]
        
        def get_recent_facts(self, days, limit):
            from datetime import datetime
            class MockFact:
                def __init__(self):
                    self.content = "User is working on Mini AI assistant"
                    self.memory_type = "project"
            return [MockFact()]
    
    # Test with mock data
    temp_dir = tempfile.mkdtemp()
    memory_manager = MockMemoryManager()
    
    startup_manager = AutonomousStartupManager(temp_dir, memory_manager, None)
    result = startup_manager.initiate_startup()
    
    print("Startup test result:")
    print(f"Type: {result['type']}")
    print(f"Message: {result['message']}")
    print(f"Status: {startup_manager.get_startup_status()}")
    
    return startup_manager

if __name__ == "__main__":
    test_startup_system()
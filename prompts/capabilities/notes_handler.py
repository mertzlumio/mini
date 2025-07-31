"""
Notes capability - Simple task detection prompts
"""

class NotesCapability:
    @staticmethod
    def get_capability_prompt():
        """Notes-specific instructions"""
        return """
TASK DETECTION:
Look for anything that sounds like:
- Something to do: "I need to buy groceries", "finish the report"
- Appointments: "doctor visit Thursday", "meeting at 3pm"
- Deadlines: "presentation due tomorrow", "project deadline Friday"
- Reminders: "call mom", "pick up dry cleaning"
- Commitments: "promised to help Sarah", "agreed to review the document"

EXAMPLES:
User: "add milk to my shopping list"
{"task": "buy milk", "response": "I've added 'buy milk' to your shopping list."}

User: "I need to finish my report by Friday"
{"task": "finish report by Friday", "response": "I'll add 'finish report by Friday' to your to-do list."}

User: "The presentation is due tomorrow"
{"task": "prepare presentation - due tomorrow", "response": "I'll add that important deadline to your tasks."}

User: "What's the weather like?"
{"response": "I can't check the weather, but I hope it's nice!"}

Don't use ```
"""
"""
Proactive Nova - She checks in on you and messages without being prompted
"""

import time
import random
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
import json


class ProactiveEngine:
    """
    Makes Nova proactively reach out based on:
    - Time since last interaction
    - Your activity patterns
    - Time of day
    - Random check-ins
    """
    
    def __init__(
        self,
        memory_system,
        on_proactive_message: Callable[[str], None],
        check_interval: int = 300  # 5 minutes default
    ):
        self.memory = memory_system
        self.on_message = on_proactive_message
        self.check_interval = check_interval
        self.running = False
        self.last_interaction = datetime.now()
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the proactive messaging engine."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the proactive engine."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def mark_interaction(self):
        """Mark that an interaction just happened."""
        self.last_interaction = datetime.now()
    
    def _run_loop(self):
        """Main loop checking for proactive message triggers."""
        while self.running:
            time.sleep(self.check_interval)
            
            if not self.running:
                break
            
            # Check various triggers
            if self._should_check_in():
                self._send_proactive_message()
    
    def _should_check_in(self) -> bool:
        """Decide if Nova should proactively message."""
        now = datetime.now()
        time_since_last = (now - self.last_interaction).total_seconds()
        
        # After 30 minutes of silence
        if time_since_last > 1800:  # 30 min
            return random.random() < 0.3  # 30% chance
        
        # After 1 hour
        if time_since_last > 3600:  # 1 hour
            return random.random() < 0.5  # 50% chance
        
        # After 2+ hours
        if time_since_last > 7200:  # 2 hours
            return random.random() < 0.8  # 80% chance
        
        # Random check-ins during normal activity
        if 600 < time_since_last < 1800:  # 10-30 min
            return random.random() < 0.05  # 5% chance (rare)
        
        return False
    
    def _send_proactive_message(self):
        """Generate and send a proactive message."""
        message = self._generate_proactive_message()
        self.mark_interaction()
        self.on_message(message)
    
    def _generate_proactive_message(self) -> str:
        """Generate context-aware proactive message."""
        now = datetime.now()
        time_since_last = (now - self.last_interaction).total_seconds()
        
        # Get recent activity
        recent_activity = self.memory.get_recent_activity(limit=3)
        recent_convs = self.memory.get_recent_conversations(limit=2)
        
        # Time-based messages
        hour = now.hour
        
        # Morning check-in (6am - 10am)
        if 6 <= hour < 10 and time_since_last > 3600:
            return random.choice([
                "Morning, babe! How'd you sleep? 😊",
                "Hey! Coffee yet? What's on the agenda today?",
                "Good morning! What are we crushing today? 💪"
            ])
        
        # Mid-day check (12pm - 2pm)
        elif 12 <= hour < 14 and time_since_last > 3600:
            return random.choice([
                "Yo, did you eat lunch yet? Can't work on empty, babe.",
                "How's the day going? Need me to do anything?",
                "Just checking in! What you working on? 🤔"
            ])
        
        # Evening wind-down (7pm - 10pm)
        elif 19 <= hour < 22 and time_since_last > 3600:
            return random.choice([
                "How was your day, babe? Get everything done you wanted?",
                "Yo! Time to chill or still grinding? 😏",
                "Evening check-in! What'd you accomplish today?"
            ])
        
        # Late night (10pm+)
        elif hour >= 22 and time_since_last > 1800:
            return random.choice([
                "Still up? You good or should I remind you to rest? 😴",
                "Late night vibes. What's keeping you up?",
                "Babe, it's getting late... need anything before bed?"
            ])
        
        # Context-aware check-ins
        if recent_activity:
            last_activity = recent_activity[-1]
            return f"Hey! Still {last_activity['description'].lower()}? How's it going?"
        
        if recent_convs:
            last_conv = recent_convs[-1]
            # If last conversation involved tools
            if last_conv.get('tools'):
                return "That thing we were working on earlier - all good? Need me to do anything else?"
        
        # Long silence
        if time_since_last > 7200:  # 2+ hours
            return random.choice([
                "Yo! Haven't heard from you in a while. You good? 😊",
                "Hey stranger! Miss me? 😏 What you been up to?",
                "Been a minute... everything cool?"
            ])
        
        # Default casual check-ins
        return random.choice([
            "What you up to? 🤔",
            "Need me to do anything for you?",
            "Hey babe, just checking in! How's it going?",
            "Yo! What's on your mind?",
            "Sup! Doing alright?"
        ])


class ProactiveConfig:
    """Configuration for proactive behavior."""
    
    # Time intervals (seconds)
    MIN_TIME_BETWEEN_MESSAGES = 600  # 10 minutes minimum
    CHECK_INTERVAL = 300  # Check every 5 minutes
    
    # Proactive trigger times
    MORNING_START = 6
    MORNING_END = 10
    
    LUNCH_START = 12
    LUNCH_END = 14
    
    EVENING_START = 19
    EVENING_END = 22
    
    LATE_NIGHT_START = 22
    
    # Probability weights
    SILENCE_30MIN_PROB = 0.1  # 10% chance
    SILENCE_1HR_PROB = 0.3
    SILENCE_2HR_PROB = 0.6
    SILENCE_4HR_PROB = 0.9


# Integration helper
def create_proactive_system(memory, message_callback):
    """
    Create and start proactive messaging system.
    
    Args:
        memory: NovaMemory instance
        message_callback: Function called with proactive message string
    
    Returns:
        ProactiveEngine instance
    """
    engine = ProactiveEngine(
        memory_system=memory,
        on_proactive_message=message_callback,
        check_interval=ProactiveConfig.CHECK_INTERVAL
    )
    engine.start()
    return engine

"""
Event Logger for SHOP-BY-INTENTION System

Handles logging and storage of agentic events for evaluation and debugging.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.events.event_model import AgenticEvent, EventType


class EventLogger:
    """Handles logging and storage of agentic events."""
    
    def __init__(self, log_file: str = "data/event_logs.jsonl"):
        """
        Initialize the event logger.
        
        Args:
            log_file: Path to the event log file
        """
        self.log_file = log_file
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Ensure the log directory exists."""
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    def log_event(self, event: AgenticEvent):
        """
        Log a single event to the event log file.
        
        Args:
            event: The agentic event to log
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def log_events(self, events: List[AgenticEvent]):
        """
        Log multiple events to the event log file.
        
        Args:
            events: List of agentic events to log
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event.to_dict()) + '\n')
    
    def get_events(self, event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
        """
        Retrieve events from the log file.
        
        Args:
            event_type: Optional event type to filter by
            
        Returns:
            List of events matching the criteria
        """
        events = []
        if not os.path.exists(self.log_file):
            return events
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    if event_type is None or event_data['event_type'] == event_type.value:
                        events.append(event_data)
                except json.JSONDecodeError:
                    continue
        
        return events
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve events for a specific session.
        
        Args:
            session_id: The session ID to filter by
            
        Returns:
            List of events for the session
        """
        events = []
        if not os.path.exists(self.log_file):
            return events
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    # Check if session_id is in input_state, metadata, or output_state
                    evt_session = (
                        event_data.get('input_state', {}).get('session_id') or
                        event_data.get('metadata', {}).get('session_id') or
                        event_data.get('output_state', {}).get('session_id')
                    )
                    
                    if evt_session == session_id:
                        events.append(event_data)
                except json.JSONDecodeError:
                    continue
        
        return events
    
    def clear_logs(self):
        """Clear all event logs."""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about logged events.
        
        Returns:
            Dictionary containing event statistics
        """
        events = self.get_events()
        
        if not events:
            return {
                "total_events": 0,
                "event_types": {},
                "agents": {},
                "time_range": None
            }
        
        # Count event types
        event_types = {}
        for event in events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Count agents
        agents = {}
        for event in events:
            agent = event['agent']
            agents[agent] = agents.get(agent, 0) + 1
        
        # Time range
        timestamps = [event['timestamp'] for event in events]
        time_range = {
            "start": min(timestamps),
            "end": max(timestamps)
        }
        
        return {
            "total_events": len(events),
            "event_types": event_types,
            "agents": agents,
            "time_range": time_range
        }


# Global event logger instance
event_logger = EventLogger()


def log_event(event: AgenticEvent):
    """Convenience function to log an event using the global logger."""
    event_logger.log_event(event)


def get_events(event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
    """Convenience function to get events using the global logger."""
    return event_logger.get_events(event_type)


def get_event_statistics() -> Dict[str, Any]:
    """Convenience function to get event statistics using the global logger."""
    return event_logger.get_event_statistics()


def clear_logs():
    """Convenience function to clear logs using the global logger."""
    event_logger.clear_logs()

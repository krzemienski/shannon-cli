#!/usr/bin/env python3
"""
Shannon V3.1 Dashboard - Live Functional Test

Runs the interactive dashboard with simulated data to verify all 4 layers work.
This is a functional test - actually runs the dashboard in the terminal.
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shannon.ui.dashboard_v31.dashboard import InteractiveDashboard
from shannon.ui.dashboard_v31.models import DashboardUIState
from shannon.metrics.collector import MetricsCollector

# Create mock managers for testing
class MockAgentStateTracker:
    """Mock agent tracker with test data"""
    
    def get_all_states(self):
        """Return mock agent states"""
        from shannon.agents.state_tracker import AgentState
        from datetime import datetime, timedelta
        
        return [
            AgentState(
                agent_id='agent-1',
                wave_number=1,
                agent_type='backend-builder',
                task_description='Build REST API with authentication',
                status='active',
                progress_percent=67.0,
                started_at=datetime.now() - timedelta(minutes=5),
                cost_usd=0.45,
                tokens_input=2500,
                tokens_output=1800,
                files_created=['api/routes.py', 'api/auth.py'],
                files_modified=['api/__init__.py']
            ),
            AgentState(
                agent_id='agent-2',
                wave_number=1,
                agent_type='frontend-builder',
                task_description='Build React dashboard UI',
                status='active',
                progress_percent=45.0,
                started_at=datetime.now() - timedelta(minutes=3),
                cost_usd=0.32,
                tokens_input=1800,
                tokens_output=1200,
                files_created=['ui/Dashboard.tsx', 'ui/Chart.tsx'],
                files_modified=[]
            ),
            AgentState(
                agent_id='agent-3',
                wave_number=1,
                agent_type='database-builder',
                task_description='Setup PostgreSQL schema',
                status='complete',
                progress_percent=100.0,
                started_at=datetime.now() - timedelta(minutes=8),
                completed_at=datetime.now() - timedelta(minutes=2),
                cost_usd=0.18,
                tokens_input=1200,
                tokens_output=800,
                files_created=['db/schema.sql', 'db/migrations/001_init.sql'],
                files_modified=[]
            )
        ]
    
    def get_state(self, agent_id):
        """Return specific agent state with messages"""
        from shannon.agents.state_tracker import AgentState
        from shannon.ui.dashboard_v31.models import MessageEntry
        from datetime import datetime
        
        states = {s.agent_id: s for s in self.get_all_states()}
        state = states.get(agent_id)
        
        if state and agent_id == 'agent-1':
            # Add sample messages for agent-1
            state.all_messages = [
                type('Message', (), {
                    'role': 'user',
                    'type': 'text',
                    'content': 'Build a REST API with authentication using FastAPI. Include user registration, login, and JWT tokens.'
                })(),
                type('Message', (), {
                    'role': 'assistant',
                    'type': 'text',
                    'content': 'I\'ll build a complete REST API with authentication. Here\'s my plan:\n\n1. Setup FastAPI project structure\n2. Implement user model and database\n3. Create registration endpoint\n4. Create login endpoint with JWT\n5. Add authentication middleware\n\nLet me start by creating the project structure.'
                })(),
                type('Message', (), {
                    'role': 'tool_use',
                    'type': 'tool_use',
                    'name': 'write_file',
                    'input': {'file_path': 'api/routes.py', 'content': '# API routes implementation'}
                })(),
                type('Message', (), {
                    'role': 'tool_result',
                    'type': 'tool_result',
                    'content': 'Successfully wrote api/routes.py (245 bytes)'
                })()
            ]
        
        return state


class MockContextManager:
    """Mock context manager with test data"""
    
    def get_state(self):
        """Return mock context state"""
        return {
            'loaded_files': [
                'src/api/routes.py',
                'src/api/auth.py',
                'src/api/__init__.py',
                'src/db/schema.sql',
                'src/ui/Dashboard.tsx'
            ],
            'active_memories': ['react-best-practices', 'fastapi-patterns'],
            'available_tools': ['read_file', 'write_file', 'search_replace', 'run_terminal_cmd', 'grep'],
            'total_bytes': 15420,
            'mcp_servers': [
                {'name': 'filesystem', 'status': 'connected', 'tool_count': 5, 'tools': ['read_file', 'write_file', 'search_replace', 'list_dir', 'grep']},
                {'name': 'sequential-thinking', 'status': 'connected', 'tool_count': 1, 'tools': ['sequential_thinking']}
            ]
        }


class MockSessionManager:
    """Mock session manager with test data"""
    
    def get_current_session(self):
        """Return mock session data"""
        return {
            'session_id': 'test-session-001',
            'command': 'wave',
            'goal': 'Build full-stack SaaS application',
            'phase': 'Wave 1: Core Implementation',
            'wave_number': 1,
            'total_waves': 5,
            'started_at': datetime.now().isoformat()
        }


async def run_dashboard_test():
    """Run dashboard with mock data"""
    
    print("🚀 Starting Shannon V3.1 Interactive Dashboard Functional Test\n")
    print("This will run the live dashboard with mock data.")
    print("Navigate using keyboard shortcuts:")
    print("  - [Enter] to drill down into layers")
    print("  - [Esc] to go back")
    print("  - [1-3] to select agents (on Layer 2)")
    print("  - [h] for help")
    print("  - [q] to quit\n")
    
    await asyncio.sleep(2)
    
    # Create metrics collector (it starts automatically)
    metrics = MetricsCollector()
    
    # Create mock managers
    agents = MockAgentStateTracker()
    context = MockContextManager()
    session = MockSessionManager()
    
    # Create dashboard
    dashboard = InteractiveDashboard(
        metrics=metrics,
        agents=agents,
        context=context,
        session=session
    )
    
    print("✅ Dashboard initialized with:")
    print(f"   - 3 agents (1 complete, 2 active)")
    print(f"   - Session: wave execution")
    print(f"   - Goal: Build full-stack SaaS application")
    print(f"\n⏳ Starting dashboard in 2 seconds...\n")
    
    await asyncio.sleep(2)
    
    # Run dashboard
    try:
        # Start dashboard
        dashboard.start()
        
        print("📊 Dashboard is running! Use keyboard to navigate:")
        print("   Layer 1 (Session) → Press [Enter] to see agents")
        print("   Layer 2 (Agents) → Press [1-3] to select agent")
        print("   Layer 3 (Agent Detail) → Press [Enter] for messages")
        print("   Layer 4 (Messages) → Scroll with arrows")
        print("\n   Press [q] to quit\n")
        
        # Run update loop - blocks until user quits with 'q'
        # For automated testing, run for limited duration
        import os
        if os.environ.get('AUTOMATED_TEST'):
            print("Running in automated mode (10 second demo)")
            dashboard.run_update_loop(duration_seconds=10)
        else:
            dashboard.run_update_loop()
        
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard test interrupted by user")
        dashboard.stop()
    except Exception as e:
        print(f"\n\n❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        dashboard.stop()
    finally:
        print("\n✅ Dashboard test complete")


if __name__ == '__main__':
    # Run the test
    asyncio.run(run_dashboard_test())


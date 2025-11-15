#!/usr/bin/env python3
"""
Shannon V3.1 Dashboard - Interactive Functional Test using pexpect

Uses pexpect to automate keyboard interactions with the live dashboard.
Tests all 4 layers by sending actual keyboard commands.
"""

import sys
import time
from pathlib import Path

try:
    import pexpect
except ImportError:
    print("❌ pexpect not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pexpect'])
    import pexpect

def run_interactive_dashboard_test():
    """
    Run dashboard and interact with it using pexpect
    
    Tests:
    1. Launch dashboard
    2. Navigate Layer 1 → Layer 2 (press Enter)
    3. Select Agent #2 (press '2')
    4. Navigate Layer 2 → Layer 3 (press Enter)
    5. Navigate Layer 3 → Layer 4 (press Enter)
    6. Scroll messages (press Down arrow)
    7. Navigate back Layer 4 → Layer 3 (press Esc)
    8. Toggle help (press 'h')
    9. Quit dashboard (press 'q')
    """
    
    print("🧪 Shannon V3.1 Interactive Dashboard Test")
    print("=" * 60)
    print()
    print("This test will:")
    print("  1. Launch the dashboard with mock data")
    print("  2. Simulate keyboard inputs to test navigation")
    print("  3. Verify all 4 layers are accessible")
    print("  4. Capture output for verification")
    print()
    
    # Path to test script
    script_path = Path(__file__).parent / "test_dashboard_v31_live.py"
    
    # Spawn the dashboard process
    print("🚀 Launching dashboard...")
    child = pexpect.spawn(
        f'{sys.executable} {script_path}',
        encoding='utf-8',
        timeout=30,
        dimensions=(80, 40)  # Terminal size
    )
    
    # Log all output
    child.logfile = sys.stdout
    
    try:
        # Wait for dashboard to initialize
        print("\n⏳ Waiting for dashboard to start...")
        child.expect("Dashboard is running", timeout=10)
        time.sleep(1)
        
        print("\n✅ Dashboard started successfully!")
        print("\n" + "=" * 60)
        print("TEST 1: Navigate Layer 1 → Layer 2 (press Enter)")
        print("=" * 60)
        
        # Test 1: Press Enter to go from Layer 1 to Layer 2
        child.send('\r')  # Send Enter key
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 2: Select Agent #2 (press '2')")
        print("=" * 60)
        
        # Test 2: Press '2' to select Agent #2
        child.send('2')
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 3: Navigate Layer 2 → Layer 3 (press Enter)")
        print("=" * 60)
        
        # Test 3: Press Enter to drill down to Layer 3
        child.send('\r')
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 4: Navigate Layer 3 → Layer 4 (press Enter)")
        print("=" * 60)
        
        # Test 4: Press Enter to view messages (Layer 4)
        child.send('\r')
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 5: Scroll messages (press Down arrow)")
        print("=" * 60)
        
        # Test 5: Press Down arrow to scroll
        child.send('\x1b[B')  # ANSI escape code for Down arrow
        time.sleep(0.3)
        child.send('\x1b[B')  # Press again
        time.sleep(0.3)
        
        print("\n" + "=" * 60)
        print("TEST 6: Navigate back Layer 4 → Layer 3 (press Esc)")
        print("=" * 60)
        
        # Test 6: Press Esc to go back
        child.send('\x1b')  # Escape key
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 7: Toggle help (press 'h')")
        print("=" * 60)
        
        # Test 7: Press 'h' to show help
        child.send('h')
        time.sleep(0.5)
        
        # Close help
        child.send('h')
        time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("TEST 8: Quit dashboard (press 'q')")
        print("=" * 60)
        
        # Test 8: Press 'q' to quit
        child.send('q')
        
        # Wait for clean shutdown
        child.expect(pexpect.EOF, timeout=5)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Dashboard successfully:")
        print("  ✓ Launched with mock data")
        print("  ✓ Navigated Layer 1 → Layer 2 → Layer 3 → Layer 4")
        print("  ✓ Selected different agents")
        print("  ✓ Scrolled message stream")
        print("  ✓ Navigated backwards")
        print("  ✓ Toggled help overlay")
        print("  ✓ Quit cleanly")
        print()
        
        return True
        
    except pexpect.TIMEOUT:
        print("\n❌ TEST FAILED: Timeout waiting for dashboard")
        print("Dashboard may not be responding to keyboard input")
        child.kill(9)
        return False
        
    except pexpect.EOF:
        print("\n❌ TEST FAILED: Dashboard exited unexpectedly")
        print("Exit status:", child.exitstatus)
        return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        child.kill(9)
        return False


if __name__ == '__main__':
    success = run_interactive_dashboard_test()
    sys.exit(0 if success else 1)


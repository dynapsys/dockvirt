#!/usr/bin/env python3
"""
Simple command tester for dockvirt - bypasses complex CliRunner issues
"""

import subprocess
import sys
from pathlib import Path

def run_dockvirt_command(cmd_args):
    """Run dockvirt command as subprocess and capture result"""
    try:
        cmd = ["python3", "-m", "dockvirt.cli"] + cmd_args
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30,
            cwd=Path.cwd()
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Exception: {str(e)}"
        }

def test_basic_commands():
    """Test basic dockvirt commands"""
    commands_to_test = [
        (["--help"], "Help command"),
        (["up", "--help"], "Up help command"),
        (["check"], "System check"),
        (["down", "--help"], "Down help command"),
    ]
    
    print("🧪 DockerVirt CLI Basic Commands Test")
    print("=" * 50)
    
    results = []
    
    for cmd_args, description in commands_to_test:
        print(f"\n📝 Testing: {description}")
        print(f"   Command: dockvirt {' '.join(cmd_args)}")
        
        result = run_dockvirt_command(cmd_args)
        results.append((description, cmd_args, result))
        
        if result["success"]:
            print(f"   ✅ SUCCESS (exit code: {result['returncode']})")
            if result["stdout"]:
                print(f"   📄 Output: {result['stdout'][:100]}{'...' if len(result['stdout']) > 100 else ''}")
        else:
            print(f"   ❌ FAILED (exit code: {result['returncode']})")
            if result["stderr"]:
                print(f"   💥 Error: {result['stderr'][:200]}{'...' if len(result['stderr']) > 200 else ''}")
    
    # Summary
    successful = sum(1 for _, _, r in results if r["success"])
    total = len(results)
    
    print(f"\n📊 SUMMARY: {successful}/{total} commands successful")
    
    if successful < total:
        print("\n❌ Failed commands:")
        for desc, cmd, result in results:
            if not result["success"]:
                print(f"   - {desc}: {result['stderr'][:100]}")
    
    return successful == total

if __name__ == "__main__":
    success = test_basic_commands()
    sys.exit(0 if success else 1)

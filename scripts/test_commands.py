#!/usr/bin/env python3
"""
Enhanced command tester for dockvirt README files.
Tests all commands found in markdown files and generates detailed reports.
"""

import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
from click.testing import CliRunner
from dockvirt.cli import main as cli_main


class CommandTester:
    """Test runner for dockvirt commands found in README files."""

    def __init__(self):
        self.runner = CliRunner()
        self.test_results: Dict[str, List[Dict]] = {}
        self.failed_commands: List[str] = []
        self.successful_commands: List[str] = []

    def extract_commands_from_file(self, file_path: Path) -> List[Tuple[str, int]]:
        """Extract dockvirt commands from a markdown file with line numbers."""
        commands = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split('\n')
                
                # Find commands in bash code blocks
                in_bash_block = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("```bash") or line.strip().startswith("```sh"):
                        in_bash_block = True
                        continue
                    elif line.strip() == "```" and in_bash_block:
                        in_bash_block = False
                        continue
                    elif in_bash_block and "dockvirt" in line:
                        cmd = line.strip()
                        if cmd and not cmd.startswith("#"):
                            commands.append((cmd, i + 1))
                
                # Also find inline commands
                inline_matches = re.finditer(r'`(dockvirt[^`]+)`', content)
                for match in inline_matches:
                    cmd = match.group(1).strip()
                    line_num = content[:match.start()].count('\n') + 1
                    commands.append((cmd, line_num))
                    
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            
        return commands

    def test_command(self, cmd: str, file_path: Path, line_num: int) -> Dict:
        """Test a single dockvirt command using CliRunner."""
        print(f"🧪 Testing: {cmd}")
        print(f"   📁 File: {file_path.relative_to(Path.cwd())}:{line_num}")
        
        # Parse command arguments
        cmd_parts = cmd.split()
        if not cmd_parts or cmd_parts[0] != "dockvirt":
            return {
                "command": cmd,
                "file": str(file_path.relative_to(Path.cwd())),
                "line": line_num,
                "success": False,
                "error": "Invalid command format",
                "duration": 0
            }
        
        args = cmd_parts[1:]  # Remove 'dockvirt' prefix
        
        start_time = time.time()
        try:
            # Test with CliRunner for better error handling
            result = self.runner.invoke(cli_main, args, catch_exceptions=False)
            duration = time.time() - start_time
            
            success = result.exit_code == 0
            error_msg = result.output if result.exit_code != 0 else None
            
            if success:
                print(f"   ✅ SUCCESS ({duration:.2f}s)")
                self.successful_commands.append(cmd)
            else:
                print(f"   ❌ FAILED ({duration:.2f}s): {error_msg}")
                self.failed_commands.append(cmd)
                
            return {
                "command": cmd,
                "file": str(file_path.relative_to(Path.cwd())),
                "line": line_num,
                "success": success,
                "error": error_msg,
                "duration": duration,
                "output": result.output
            }
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"   💥 EXCEPTION ({duration:.2f}s): {str(e)}")
            self.failed_commands.append(cmd)
            
            return {
                "command": cmd,
                "file": str(file_path.relative_to(Path.cwd())),
                "line": line_num,
                "success": False,
                "error": f"Exception: {str(e)}",
                "duration": duration
            }

    def scan_all_readmes(self) -> Dict[str, List[Tuple[str, int]]]:
        """Scan all README files for dockvirt commands."""
        print("📚 Scanning README files for dockvirt commands...")
        
        readme_files = []
        # Look for README files
        for pattern in ["README.md", "readme.md", "README.rst", "*.md"]:
            readme_files.extend(Path.cwd().rglob(pattern))
        
        commands_by_file = {}
        total_commands = 0
        
        for file_path in readme_files:
            if file_path.is_file():
                commands = self.extract_commands_from_file(file_path)
                if commands:
                    commands_by_file[str(file_path)] = commands
                    total_commands += len(commands)
                    print(f"  📄 {file_path.relative_to(Path.cwd())}: {len(commands)} commands")
        
        print(f"\n🔍 Found {total_commands} dockvirt commands in {len(commands_by_file)} files\n")
        return commands_by_file

    def run_all_tests(self) -> bool:
        """Run tests on all found commands."""
        commands_by_file = self.scan_all_readmes()
        
        if not commands_by_file:
            print("❌ No dockvirt commands found in README files")
            return False
        
        print("🚀 Starting command validation tests...\n")
        
        for file_path, commands in commands_by_file.items():
            print(f"📁 Testing commands from: {Path(file_path).relative_to(Path.cwd())}")
            file_results = []
            
            for cmd, line_num in commands:
                result = self.test_command(cmd, Path(file_path), line_num)
                file_results.append(result)
            
            self.test_results[file_path] = file_results
            print()  # Empty line between files
        
        return len(self.failed_commands) == 0

    def generate_report(self) -> str:
        """Generate detailed test report."""
        report = []
        report.append("# Dockvirt Commands Test Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        total_commands = len(self.successful_commands) + len(self.failed_commands)
        success_rate = (len(self.successful_commands) / total_commands * 100) if total_commands > 0 else 0
        
        report.append("## Summary")
        report.append(f"- **Total Commands Tested**: {total_commands}")
        report.append(f"- **Successful**: {len(self.successful_commands)}")
        report.append(f"- **Failed**: {len(self.failed_commands)}")
        report.append(f"- **Success Rate**: {success_rate:.1f}%")
        report.append("")
        
        # Failed commands details
        if self.failed_commands:
            report.append("## ❌ Failed Commands")
            report.append("")
            
            for file_path, results in self.test_results.items():
                failed_in_file = [r for r in results if not r["success"]]
                if failed_in_file:
                    report.append(f"### {Path(file_path).relative_to(Path.cwd())}")
                    report.append("")
                    
                    for result in failed_in_file:
                        report.append(f"**Line {result['line']}**: `{result['command']}`")
                        report.append(f"- **Error**: {result['error']}")
                        report.append(f"- **Duration**: {result['duration']:.2f}s")
                        report.append("")
        
        # Successful commands
        if self.successful_commands:
            report.append("## ✅ Successful Commands")
            report.append("")
            
            for file_path, results in self.test_results.items():
                successful_in_file = [r for r in results if r["success"]]
                if successful_in_file:
                    report.append(f"### {Path(file_path).relative_to(Path.cwd())}")
                    report.append("")
                    
                    for result in successful_in_file:
                        report.append(f"- **Line {result['line']}**: `{result['command']}` ({result['duration']:.2f}s)")
                    report.append("")
        
        # Recommendations
        report.append("## 🔧 Recommendations")
        report.append("")
        
        if self.failed_commands:
            report.append("### Commands to Fix:")
            unique_failures = {}
            for file_path, results in self.test_results.items():
                for result in results:
                    if not result["success"]:
                        error_type = result["error"].split(":")[0] if ":" in result["error"] else result["error"]
                        if error_type not in unique_failures:
                            unique_failures[error_type] = []
                        unique_failures[error_type].append(result["command"])
            
            for error_type, commands in unique_failures.items():
                report.append(f"- **{error_type}**: {len(commands)} commands")
                for cmd in commands[:3]:  # Show first 3 examples
                    report.append(f"  - `{cmd}`")
                if len(commands) > 3:
                    report.append(f"  - ... and {len(commands) - 3} more")
                report.append("")
        else:
            report.append("🎉 All commands are working correctly!")
        
        return "\n".join(report)

    def suggest_fixes(self) -> List[str]:
        """Suggest fixes for common command issues."""
        fixes = []
        
        # Analyze common failure patterns
        error_patterns = {}
        for file_path, results in self.test_results.items():
            for result in results:
                if not result["success"] and result["error"]:
                    error = result["error"].lower()
                    if "no such option" in error:
                        error_patterns["invalid_option"] = error_patterns.get("invalid_option", 0) + 1
                    elif "missing argument" in error:
                        error_patterns["missing_arg"] = error_patterns.get("missing_arg", 0) + 1
                    elif "jinja2" in error:
                        error_patterns["missing_jinja2"] = error_patterns.get("missing_jinja2", 0) + 1
        
        if error_patterns.get("invalid_option", 0) > 0:
            fixes.append("Update CLI option names in README files")
        if error_patterns.get("missing_arg", 0) > 0:
            fixes.append("Add missing required arguments to example commands")
        if error_patterns.get("missing_jinja2", 0) > 0:
            fixes.append("Fix jinja2 dependency issue in development environment")
            
        return fixes


def main():
    """Main test runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_commands.py")
        print("")
        print("Test all dockvirt commands found in README files.")
        print("Generates detailed report with failures and suggestions.")
        return
    
    tester = CommandTester()
    
    print("🔧 Dockvirt Commands Validator")
    print("=" * 40)
    print()
    
    # Run all tests
    success = tester.run_all_tests()
    
    # Generate and save report
    print("📊 GENERATING REPORT")
    print("=" * 40)
    
    report = tester.generate_report()
    print(report)
    
    # Save report to file
    report_file = Path("command_test_results.md")
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Show suggested fixes
    fixes = tester.suggest_fixes()
    if fixes:
        print("\n🔧 Suggested Fixes:")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

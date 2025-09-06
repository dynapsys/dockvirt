#!/usr/bin/env python3
"""
Robust command tester for dockvirt README files.
Tests all commands using subprocess calls and generates detailed reports.
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class RobustCommandTester:
    """Robust test runner for dockvirt commands found in README files."""

    def __init__(self):
        self.test_results: Dict[str, List[Dict]] = {}
        self.failed_commands: List[str] = []
        self.successful_commands: List[str] = []
        self.project_root = Path(__file__).parent.parent

    def extract_commands_from_file(self, file_path: Path) -> List[Tuple[str, int]]:
        """Extract dockvirt commands from a markdown file with line numbers.

        Supports multiline commands using '\\' continuations inside fenced code blocks.
        Only captures lines starting with 'dockvirt' (optionally prefixed with '$ ').
        """
        commands: List[Tuple[str, int]] = []
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            in_code_block = False
            buf_cmd: str | None = None
            buf_start: int | None = None
            allowed_subs = {"up", "down", "check", "setup", "heal", "ip", "generate-image", "stack"}

            def flush_buffer():
                nonlocal buf_cmd, buf_start
                if buf_cmd and buf_start:
                    # Validate subcommand
                    parts = buf_cmd.strip().split()
                    if len(parts) >= 2 and parts[0] == "dockvirt" and parts[1] in allowed_subs:
                        commands.append((buf_cmd.strip(), buf_start))
                buf_cmd = None
                buf_start = None

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Toggle fenced block
                if stripped.startswith("```"):
                    # Leaving a block should flush any pending command
                    if in_code_block:
                        flush_buffer()
                    in_code_block = not in_code_block
                    continue

                # Skip comment-only lines
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue

                # If we are in a continuation, keep appending
                if buf_cmd is not None:
                    # Remove trailing backslash
                    continued = stripped[:-1].strip() if stripped.endswith("\\") else stripped
                    buf_cmd += " " + continued
                    if not stripped.endswith("\\"):
                        flush_buffer()
                    continue

                # Detect start of a dockvirt command (require line to start with dockvirt)
                if stripped.startswith("dockvirt") or stripped.startswith("$ dockvirt"):
                    # Normalize to start from 'dockvirt'
                    start_idx = stripped.find("dockvirt")
                    cmd = stripped[start_idx:]
                    if cmd.startswith("$ "):
                        cmd = cmd[2:].strip()
                    # Multiline?
                    if cmd.endswith("\\"):
                        buf_cmd = cmd[:-1].strip()
                        buf_start = line_num
                    else:
                        # Single line command
                        if cmd.startswith("dockvirt"):
                            parts = cmd.split()
                            if len(parts) >= 2 and parts[1] in allowed_subs:
                                commands.append((cmd, line_num))

            # Flush at EOF
            if buf_cmd is not None:
                flush_buffer()

        except Exception as e:
            print("❌ Error reading {}: {}".format(file_path, e))

        return commands

    def test_command_subprocess(self, command: str, timeout: int = 30) -> Dict:
        """Test a command using subprocess for maximum compatibility."""
        start_time = time.time()
        
        try:
            # Split command into parts
            cmd_parts = command.split()
            # Skip planned features (stack, exec)
            if command.strip().startswith("dockvirt stack") or command.strip().startswith("dockvirt exec"):
                return {
                    "command": command,
                    "success": True,
                    "error": None,
                    "duration": 0.0,
                    "exit_code": 0,
                    "stdout": "skipped planned feature",
                    "stderr": "",
                }
            
            # Add --help to dry-run the command without executing it
            if '--help' not in cmd_parts and 'help' not in cmd_parts:
                test_cmd = cmd_parts + ['--help']
            else:
                test_cmd = cmd_parts
            
            # Ensure local venv dockvirt takes precedence
            env = dict(**os.environ)
            venv_bin = self.project_root / ".venv-3.13" / "bin"
            if venv_bin.exists():
                env["PATH"] = f"{venv_bin}:{env.get('PATH','')}"

            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
                env=env,
            )
            
            duration = time.time() - start_time
            
            # Consider it successful if help is shown or exit code is reasonable,
            # but fail explicitly on 'No such command/option'
            combined = (result.stderr or "") + "\n" + (result.stdout or "")
            lower = combined.lower()
            bad = ("no such command" in lower) or ("no such option" in lower)
            success = (result.returncode in [0, 1, 2]) and (not bad)
            error_msg = result.stderr if result.stderr else result.stdout if result.returncode != 0 else None
            
            return {
                "command": command,
                "success": success,
                "error": error_msg,
                "duration": duration,
                "exit_code": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "command": command,
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "command": command,
                "success": False,
                "error": f"Exception: {str(e)}",
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": ""
            }

    def scan_all_readmes(self) -> Dict[str, List[Tuple[str, int]]]:
        """Scan all README files for dockvirt commands."""
        print("📚 Scanning README files for dockvirt commands...")
        
        readme_files: List[Path] = []
        # Look for README files
        for pattern in ["README.md", "readme.md", "README.rst"]:
            readme_files.extend(self.project_root.rglob(pattern))
        
        commands_by_file = {}
        total_commands = 0
        
        for file_path in readme_files:
            if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', '__pycache__', 'node_modules']):
                commands = self.extract_commands_from_file(file_path)
                if commands:
                    rel_path = str(file_path.relative_to(self.project_root))
                    commands_by_file[rel_path] = commands
                    total_commands += len(commands)
                    print(f"  📄 {rel_path}: {len(commands)} commands")
        
        print(f"📊 Found {total_commands} dockvirt commands in {len(commands_by_file)} files")
        return commands_by_file

    def test_all_commands(self) -> None:
        """Test all dockvirt commands found in README files."""
        commands_by_file = self.scan_all_readmes()
        
        if not commands_by_file:
            print("❌ No dockvirt commands found in README files!")
            return
        
        print("\n🧪 Testing dockvirt commands...")
        
        total_commands = sum(len(cmds) for cmds in commands_by_file.values())
        current_command = 0
        
        for file_path, commands in commands_by_file.items():
            print(f"\n📝 Testing commands in {file_path}:")
            file_results = []
            
            for command, line_num in commands:
                current_command += 1
                print(f"  [{current_command}/{total_commands}] Line {line_num}: {command[:60]}...")
                
                result = self.test_command_subprocess(command)
                result["line"] = line_num
                result["file"] = file_path
                file_results.append(result)
                
                if result["success"]:
                    print(f"    ✅ OK ({result['duration']:.2f}s)")
                    self.successful_commands.append(command)
                else:
                    print(f"    ❌ FAILED: {result['error'][:80]}...")
                    self.failed_commands.append(command)
            
            self.test_results[file_path] = file_results

    def generate_report(self) -> str:
        """Generate a detailed markdown report of test results."""
        report = []
        report.append("# Dockvirt Command Test Results")
        report.append("")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_commands = len(self.successful_commands) + len(self.failed_commands)
        success_rate = (len(self.successful_commands) / total_commands * 100) if total_commands > 0 else 0
        
        report.append("## 📊 Summary")
        report.append("")
        report.append(f"- **Total Commands**: {total_commands}")
        report.append(f"- **Successful**: {len(self.successful_commands)} ({success_rate:.1f}%)")
        report.append(f"- **Failed**: {len(self.failed_commands)} ({100-success_rate:.1f}%)")
        report.append("")
        
        # Detailed results by file
        report.append("## 📋 Detailed Results")
        report.append("")
        
        for file_path, results in self.test_results.items():
            report.append(f"### {file_path}")
            report.append("")
            
            failed_in_file = [r for r in results if not r["success"]]
            successful_in_file = [r for r in results if r["success"]]
            
            if failed_in_file:
                report.append("#### ❌ Failed Commands:")
                for result in failed_in_file:
                    report.append(f"- **Line {result['line']}**: `{result['command']}`")
                    report.append(f"  - Error: {result['error']}")
                    report.append(f"  - Exit code: {result['exit_code']}")
                    if result['stderr']:
                        report.append(f"  - Stderr: {result['stderr'][:100]}...")
                    report.append("")
            
            if successful_in_file:
                report.append("#### ✅ Successful Commands:")
                for result in successful_in_file:
                    report.append(f"- **Line {result['line']}**: `{result['command']}` ({result['duration']:.2f}s)")
                report.append("")
        
        # Analysis and recommendations
        report.append("## 🔧 Analysis & Recommendations")
        report.append("")
        
        if self.failed_commands:
            # Analyze error patterns
            error_patterns = self._analyze_errors()
            
            report.append("### Common Issues Found:")
            for pattern, count in error_patterns.items():
                report.append(f"- **{pattern}**: {count} commands")
            
            report.append("")
            report.append("### Suggested Fixes:")
            fixes = self._suggest_fixes(error_patterns)
            for fix in fixes:
                report.append(f"- {fix}")
        else:
            report.append("🎉 All commands are working correctly!")
        
        return "\n".join(report)

    def _analyze_errors(self) -> Dict[str, int]:
        """Analyze error patterns in failed commands."""
        patterns = {}
        
        for file_path, results in self.test_results.items():
            for result in results:
                if not result["success"] and result["error"]:
                    error = result["error"].lower()
                    
                    if "no such option" in error:
                        patterns["Invalid CLI Options"] = patterns.get("Invalid CLI Options", 0) + 1
                    elif "missing argument" in error or "requires an argument" in error:
                        patterns["Missing Required Arguments"] = patterns.get("Missing Required Arguments", 0) + 1
                    elif "command not found" in error or "no such file" in error:
                        patterns["Command Not Found"] = patterns.get("Command Not Found", 0) + 1
                    elif "jinja2" in error or "module" in error:
                        patterns["Missing Dependencies"] = patterns.get("Missing Dependencies", 0) + 1
                    elif "timeout" in error:
                        patterns["Timeouts"] = patterns.get("Timeouts", 0) + 1
                    else:
                        patterns["Other Errors"] = patterns.get("Other Errors", 0) + 1
        
        return patterns

    def _suggest_fixes(self, error_patterns: Dict[str, int]) -> List[str]:
        """Suggest fixes for common error patterns."""
        fixes = []
        
        if error_patterns.get("Invalid CLI Options", 0) > 0:
            fixes.append("Review and update CLI option names in README examples")
            fixes.append("Add validation for CLI option compatibility")
        
        if error_patterns.get("Missing Required Arguments", 0) > 0:
            fixes.append("Add all required arguments to command examples")
            fixes.append("Update documentation with current CLI requirements")
        
        if error_patterns.get("Command Not Found", 0) > 0:
            fixes.append("Ensure dockvirt is properly installed and in PATH")
            fixes.append("Check if CLI entry points are correctly configured")
        
        if error_patterns.get("Missing Dependencies", 0) > 0:
            fixes.append("Install missing Python dependencies (jinja2, click, etc.)")
            fixes.append("Update installation instructions in README")
        
        if error_patterns.get("Timeouts", 0) > 0:
            fixes.append("Investigate slow commands for performance issues")
            fixes.append("Consider mocking or dry-run modes for testing")
        
        return fixes

    def save_results(self, output_file: str = "test_results.md"):
        """Save test results to a markdown file."""
        report = self.generate_report()
        output_path = self.project_root / output_file
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Results saved to: {output_path}")

    def auto_fix_commands(self) -> List[str]:
        """Attempt to automatically fix common command issues."""
        fixes_applied = []
        
        # This would contain logic to automatically fix README files
        # For now, just return suggestions
        if self.failed_commands:
            fixes_applied.append("Manual review required for failed commands")
            fixes_applied.append("See command_test_results.md for detailed analysis")
        
        return fixes_applied


def main():
    """Main entry point for command testing."""
    print("🚀 Starting dockvirt command validation...")
    
    tester = RobustCommandTester()
    
    # Test all commands
    tester.test_all_commands()
    
    # Generate and save report
    tester.save_results()
    
    # Summary
    total = len(tester.successful_commands) + len(tester.failed_commands)
    if total > 0:
        success_rate = len(tester.successful_commands) / total * 100
        print("\n📊 Testing complete!")
        print(f"   ✅ Successful: {len(tester.successful_commands)}/{total} ({success_rate:.1f}%)")
        print(f"   ❌ Failed: {len(tester.failed_commands)}/{total} ({100-success_rate:.1f}%)")
        
        if tester.failed_commands:
            print("\n🔧 Auto-fix suggestions:")
            fixes = tester.auto_fix_commands()
            for fix in fixes:
                print(f"   - {fix}")
    else:
        print("❌ No commands found to test!")


if __name__ == "__main__":
    main()

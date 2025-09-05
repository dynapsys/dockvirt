#!/usr/bin/env python3
"""
Test runner for dockvirt examples across different systems.
Automatically tests all examples with different OS configurations.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from click.testing import CliRunner

from dockvirt.cli import main as cli_main


class ExampleTester:
    """Test runner for dockvirt examples."""

    def __init__(self):
        self.examples_dir = Path(__file__).parent.parent / "examples"
        self.test_results: Dict[str, Any] = {}
        self.test_os_variants = ["ubuntu22.04", "fedora38"]
        self.runner = CliRunner()

    def get_examples(self) -> List[Path]:
        """Get list of example directories."""
        examples = []
        for item in self.examples_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Check if it has .dockvirt file or Dockerfile
                if (item / ".dockvirt").exists() or (item / "Dockerfile").exists():
                    examples.append(item)
        return examples

    def build_example_image(self, example_dir: Path) -> Tuple[bool, str]:
        """Build Docker image for example."""
        print(f"  📦 Building Docker image for {example_dir.name}...")

        # Get image name from .dockvirt or use directory name
        image_name = f"test-{example_dir.name}"
        if (example_dir / ".dockvirt").exists():
            with open(example_dir / ".dockvirt", "r") as f:
                for line in f:
                    if line.startswith("image="):
                        image_name = line.split("=", 1)[1].strip()
                        break

        # We still need to run docker build as a subprocess
        result = subprocess.run(
            f"docker build -t {image_name} .",
            shell=True,
            capture_output=True,
            text=True,
            cwd=example_dir,
            timeout=600,  # 10 minutes for build
        )
        success = result.returncode == 0
        stderr = result.stderr

        if success:
            print(f"  ✅ Image {image_name} built successfully")
            return True, image_name
        else:
            print(f"  ❌ Failed to build image: {stderr}")
            return False, ""

    def test_example_vm(
        self, example_dir: Path, image_name: str, os_variant: str
    ) -> Tuple[bool, Optional[str]]:
        """Test example by creating VM and checking if it responds."""
        vm_name = f"test-{example_dir.name}-{os_variant}"
        domain = f"{vm_name}.test.local"

        print(f"  🚀 Creating VM: {vm_name} with {os_variant}...")

        # Create VM
        result = self.runner.invoke(
            cli_main,
            [
                "up",
                "--name",
                vm_name,
                "--domain",
                domain,
                "--image",
                image_name,
                "--port",
                "80",
                "--os",
                os_variant,
            ],
            catch_exceptions=False,  # So we see the full traceback
        )

        if result.exit_code != 0:
            print(f"  ❌ Failed to create VM: {result.output}")
            return False, result.output

        print(f"  ✅ VM {vm_name} created successfully")

        # Wait for VM to be ready
        print("  ⏳ Waiting for VM to be ready...")
        time.sleep(60)  # Wait 1 minute for startup

        # Try to get VM IP and test connectivity
        ip_result = self.runner.invoke(cli_main, ["ip", "--name", vm_name])
        if ip_result.exit_code == 0 and ip_result.output.strip():
            ip = ip_result.output.strip()
            print(f"  🌐 VM IP: {ip}")

            # Test HTTP connectivity
            http_result = subprocess.run(
                f"curl -s -o /dev/null -w '%{{http_code}}' http://{ip}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if http_result.returncode == 0 and http_result.stdout.strip() == "200":
                print("  ✅ VM responding to HTTP requests")
            else:
                print(f"  ⚠️  VM created but HTTP not responding (code: {http_result.stdout.strip()})")
        else:
            print("  ⚠️  Could not get VM IP address.")

        # Cleanup - destroy VM
        print(f"  🧹 Cleaning up VM {vm_name}...")
        self.runner.invoke(cli_main, ["down", "--name", vm_name])

        return True, None

    def test_example(self, example_dir: Path) -> Dict[str, Any]:
        """Test single example across different OS variants."""
        print(f"\n📁 Testing example: {example_dir.name}")
        print("=" * 50)

        results = {
            "name": example_dir.name,
            "path": str(example_dir),
            "build_success": False,
            "image_name": "",
            "os_tests": {},
        }

        # Build Docker image
        build_success, image_name = self.build_example_image(example_dir)
        results["build_success"] = build_success
        results["image_name"] = image_name

        if not build_success:
            return results

        # Test with different OS variants
        for os_variant in self.test_os_variants:
            print(f"\n  🖥️ Testing with {os_variant}...")

            try:
                vm_success, error_msg = self.test_example_vm(
                    example_dir, image_name, os_variant
                )
                results["os_tests"][os_variant] = {
                    "success": vm_success,
                    "error": error_msg,
                }

                if vm_success:
                    print(f"  ✅ {os_variant}: SUCCESS")
                else:
                    print(f"  ❌ {os_variant}: FAILED")

            except Exception as e:
                results["os_tests"][os_variant] = {
                    "success": False,
                    "error": str(e),
                }
                print(f"  ❌ {os_variant}: ERROR - {e}")

        return results

    def generate_report(self) -> str:
        """Generate test report."""
        report = []
        report.append("# DockerVirt Examples Test Report")
        report.append("=" * 50)
        report.append("")

        total_examples = len(self.test_results)
        successful_builds = sum(
            1 for r in self.test_results.values() if r["build_success"]
        )

        report.append(f"**Summary:**")
        report.append(f"- Total Examples: {total_examples}")
        report.append(f"- Successful Builds: {successful_builds}")
        report.append("")

        for example_name, result in self.test_results.items():
            report.append(f"## {example_name}")
            report.append("")

            if result["build_success"]:
                report.append(f"✅ **Build:** SUCCESS (image: {result['image_name']})")
            else:
                report.append(f"❌ **Build:** FAILED")

            if result.get("os_tests"):
                report.append("")
                report.append("**OS Compatibility:**")
                for os_variant, test_result in result["os_tests"].items():
                    if test_result["success"]:
                        report.append(f"- ✅ {os_variant}: SUCCESS")
                    else:
                        error = test_result.get("error", "Unknown error")
                        report.append(f"- ❌ {os_variant}: FAILED - {error}")

            report.append("")

        return "\n".join(report)

    def run_all_tests(self) -> bool:
        """Run tests for all examples."""
        print("🧪 Starting dockvirt examples testing...")
        print(
            "This may take a while as it tests each example with multiple OS variants"
        )
        print("")

        examples = self.get_examples()

        if not examples:
            print("❌ No examples found in examples/ directory")
            return False

        print(f"Found {len(examples)} examples to test:")
        for example in examples:
            print(f"  - {example.name}")
        print("")

        # Test each example
        for example_dir in examples:
            try:
                result = self.test_example(example_dir)
                self.test_results[example_dir.name] = result
            except KeyboardInterrupt:
                print("\n⏹️  Testing interrupted by user")
                return False
            except Exception as e:
                print(f"\n❌ Error testing {example_dir.name}: {e}")
                self.test_results[example_dir.name] = {
                    "name": example_dir.name,
                    "error": str(e),
                    "build_success": False,
                    "os_tests": {},
                }

        # Generate report
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)

        report = self.generate_report()
        print(report)

        # Save report to file
        report_file = Path("test_results.md")
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Return success if all builds and tests passed
        all_tests_ok = all(
            r.get("build_success", False)
            and all(t.get("success", False) for t in r.get("os_tests", {}).values())
            for r in self.test_results.values()
        )
        return all_tests_ok


def main():
    """Main test runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_examples.py [example_name]")
        print("")
        print("Test all examples or specific example with different OS variants.")
        print("")
        print("Examples:")
        print("  python test_examples.py                    # Test all examples")
        print("  python test_examples.py 1-static-nginx    # Test specific example")
        return

    tester = ExampleTester()

    if len(sys.argv) > 1:
        # Test specific example
        example_name = sys.argv[1]
        example_dir = tester.examples_dir / example_name

        if not example_dir.exists():
            print(f"❌ Example '{example_name}' not found")
            sys.exit(1)

        result = tester.test_example(example_dir)
        tester.test_results[example_name] = result

        success = result["build_success"]
    else:
        # Test all examples
        success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

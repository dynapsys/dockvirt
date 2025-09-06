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
import re
import os

from dockvirt.cli import main as cli_main


class ExampleTester:
    """Test runner for dockvirt examples."""

    def __init__(self):
        self.examples_dir = Path(__file__).parent.parent / "examples"
        self.test_results: Dict[str, Any] = {}
        self.test_os_variants = ["ubuntu22.04", "fedora38"]
        self.runner = CliRunner()
        # Ensure CLI uses system libvirt unless overridden
        self.env = os.environ.copy()
        self.env.setdefault("LIBVIRT_DEFAULT_URI", "qemu:///system")

    def parse_dockvirt(self, example_dir: Path) -> Dict[str, str]:
        """Parse .dockvirt key=value pairs into a dict."""
        cfg: Dict[str, str] = {}
        fpath = example_dir / ".dockvirt"
        if not fpath.exists():
            return cfg
        try:
            with fpath.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        cfg[k.strip()] = v.strip()
        except Exception as e:
            print(f"  ⚠️  Failed to parse {fpath}: {e}")
        return cfg

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
        settings = self.parse_dockvirt(example_dir)
        image_name = settings.get("image", f"test-{example_dir.name}")

        # Host-side Docker build is optional now.
        # Skip if instructed or if Docker is unavailable; VM will build using cloud-init.
        if os.environ.get("SKIP_HOST_BUILD") == "1":
            print("  ⏭️  Skipping host Docker build (SKIP_HOST_BUILD=1). VM will build.")
            return True, image_name

        if not (example_dir / "Dockerfile").exists():
            print("  ⏭️  No Dockerfile in example; skipping host build.")
            return True, image_name

        docker_ok = subprocess.run(
            "docker --version", shell=True, capture_output=True, text=True
        ).returncode == 0
        if not docker_ok:
            print("  ⏭️  Docker not found on host; skipping host build. VM will build.")
            return True, image_name

        # Attempt host build; if it fails, continue (VM will build).
        result = subprocess.run(
            f"docker build -t {image_name} .",
            shell=True,
            capture_output=True,
            text=True,
            cwd=example_dir,
            timeout=600,  # 10 minutes for build
        )
        if result.returncode == 0:
            print(f"  ✅ Image {image_name} built successfully")
            return True, image_name
        else:
            print("  ⚠️  Host build failed; proceeding (VM will build image).")
            return True, image_name

    def test_example_vm(
        self, example_dir: Path, image_name: str, os_variant: str
    ) -> Tuple[bool, Optional[str]]:
        """Test example by creating VM and checking if it responds."""
        vm_name = f"test-{example_dir.name}-{os_variant}"
        settings = self.parse_dockvirt(example_dir)
        domain = settings.get("domain", f"{vm_name}.test.local")
        port = settings.get("port", "80")

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
                str(port),
                "--os",
                os_variant,
            ],
            catch_exceptions=False,  # So we see the full traceback
            env=self.env,
        )

        if result.exit_code != 0:
            print(f"  ❌ Failed to create VM: {result.output}")
            return False, result.output

        print(f"  ✅ VM {vm_name} created successfully")

        # Wait for VM to be ready
        print("  ⏳ Waiting for VM to be ready...")
        time.sleep(60)  # Wait 1 minute for startup

        # Try to get VM IP and test connectivity
        ip_result = self.runner.invoke(
            cli_main, ["ip", "--name", vm_name], env=self.env
        )
        ip_ok = False
        ip_http_ok = False
        domain_resolves = False
        domain_http_ok = False

        if ip_result.exit_code == 0 and ip_result.output.strip():
            # Extract bare IPv4 address from CLI output
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", ip_result.output)
            ip = m.group(1) if m else ""
            if ip:
                print(f"  🌐 VM IP: {ip}")
                ip_ok = True
            else:
                print("  ⚠️  Could not parse IP from CLI output")

            # Test HTTP connectivity (IP)
            ip_url = f"http://{ip}/" if str(port) == "80" else f"http://{ip}:{port}/"
            http_result = subprocess.run(
                f"curl -s -o /dev/null -w '%{{http_code}}' {ip_url}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if http_result.returncode == 0 and http_result.stdout.strip() == "200":
                print("  ✅ VM responding to HTTP requests")
                ip_http_ok = True
            else:
                print(f"  ⚠️  VM created but HTTP not responding (code: {http_result.stdout.strip()})")

            # Check domain DNS resolution
            try:
                dns = subprocess.run(
                    f"getent hosts {domain}", shell=True,
                    capture_output=True, text=True, timeout=5
                )
                domain_resolves = dns.returncode == 0 and dns.stdout.strip() != ""
            except Exception:
                domain_resolves = False
            if domain_resolves:
                print(f"  🧭 Domain resolves: {domain}")
            else:
                print(f"  ❌ Domain does not resolve locally: {domain}")
                print(f"     Tip: sudo sh -c 'echo \"{ip} {domain}\" >> /etc/hosts'")

            # HTTP check via domain URL (respect port)
            dom_url = (
                f"http://{domain}/" if str(port) == "80" else f"http://{domain}:{port}/"
            )
            http_dom = subprocess.run(
                f"curl -s -o /dev/null -w '%{{http_code}}' {dom_url}",
                shell=True, capture_output=True, text=True, timeout=15
            )
            if http_dom.returncode == 0 and http_dom.stdout.strip() == "200":
                print(f"  ✅ HTTP via domain OK: {dom_url}")
                domain_http_ok = True
            else:
                print(f"  ⚠️  HTTP via domain failed (code: {http_dom.stdout.strip()}): {dom_url}")
        else:
            print("  ⚠️  Could not get VM IP address.")

        # Cleanup - destroy VM
        print(f"  🧹 Cleaning up VM {vm_name}...")
        self.runner.invoke(cli_main, ["down", "--name", vm_name], env=self.env)

        # Require domain resolution and HTTP success via domain
        success = domain_resolves and domain_http_ok
        error = None
        if not success:
            reasons = []
            if not ip_ok:
                reasons.append("no IP")
            if ip_ok and not ip_http_ok:
                reasons.append("HTTP on IP failed")
            if not domain_resolves:
                reasons.append("domain not resolving locally")
            if domain_resolves and not domain_http_ok:
                reasons.append("HTTP via domain failed")
            error = ", ".join(reasons) if reasons else "unknown"
        return success, error

    def test_example(self, example_dir: Path) -> Dict[str, Any]:
        """Test single example across different OS variants."""
        print(f"\n📁 Testing example: {example_dir.name}")
        print("=" * 50)

        results = {
            "name": example_dir.name,
            "path": str(example_dir),
            "build_success": False,
            "image_name": "",
            "domain": self.parse_dockvirt(example_dir).get("domain", ""),
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
                    "domain": results["domain"],
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

        report.append("**Summary:**")
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
                    dom = test_result.get("domain", "")
                    if test_result["success"]:
                        report.append(f"- ✅ {os_variant}: SUCCESS (domain: {dom})")
                    else:
                        error = test_result.get("error", "Unknown error")
                        report.append(f"- ❌ {os_variant}: FAILED - {error} (domain: {dom})")

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

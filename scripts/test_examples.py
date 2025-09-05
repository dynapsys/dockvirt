#!/usr/bin/env python3
"""
Test runner for dockvirt examples across different systems.
Automatically tests all examples with different OS configurations.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


class ExampleTester:
    """Test runner for dockvirt examples."""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent.parent / "examples"
        self.test_results = {}
        self.test_os_variants = ["ubuntu22.04", "fedora38"]
        
    def run_command(
        self, cmd: str, cwd: Path = None, timeout: int = 300
    ) -> Tuple[bool, str, str]:
        """Run shell command with timeout."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=cwd
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def get_examples(self) -> List[Path]:
        """Get list of example directories."""
        examples = []
        for item in self.examples_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has .dockvirt file or Dockerfile
                if (item / ".dockvirt").exists() or (item / "Dockerfile").exists():
                    examples.append(item)
        return examples
    
    def build_example_image(self, example_dir: Path) -> Tuple[bool, str]:
        """Build Docker image for example."""
        print("  📦 Building Docker image...")
        
        # Get image name from .dockvirt or use directory name
        image_name = example_dir.name
        if (example_dir / '.dockvirt').exists():
            with open(example_dir / '.dockvirt', 'r') as f:
                for line in f:
                    if line.startswith('image='):
                        image_name = line.split('=', 1)[1].strip()
                        break
        
        success, stdout, stderr = self.run_command(
            f"docker build -t {image_name} .", 
            cwd=example_dir,
            timeout=600  # 10 minutes for build
        )
        
        if success:
            print(f"  ✅ Image {image_name} built successfully")
            return True, image_name
        else:
            print(f"  ❌ Failed to build image: {stderr}")
            return False, ""
    
    def test_example_vm(self, example_dir: Path, image_name: str, os_variant: str) -> bool:
        """Test example by creating VM and checking if it responds."""
        vm_name = f"test-{example_dir.name}-{os_variant}"
        domain = f"{vm_name}.test.local"
        
        print(f"  🚀 Creating VM: {vm_name} with {os_variant}...")
        
        # Create VM
        cmd = (f"python3 -m dockvirt.cli up --name {vm_name} --domain {domain} "
               f"--image {image_name} --port 80 --os {os_variant}")
        
        success, stdout, stderr = self.run_command(cmd, timeout=600)  # 10 minutes
        
        if not success:
            print(f"  ❌ Failed to create VM: {stderr}")
            return False
        
        print(f"  ✅ VM {vm_name} created successfully")
        
        # Wait for VM to be ready
        print("  ⏳ Waiting for VM to be ready...")
        time.sleep(60)  # Wait 1 minute for startup
        
        # Try to get VM IP and test connectivity
        success, ip_output, _ = self.run_command(f"python3 -m dockvirt.cli ip {vm_name}")
        if success and ip_output:
            ip = ip_output.strip()
            print(f"  🌐 VM IP: {ip}")
            
            # Test HTTP connectivity
            success, _, _ = self.run_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{ip}", timeout=30)
            if success:
                print("  ✅ VM responding to HTTP requests")
            else:
                print("  ⚠️  VM created but HTTP not responding")
        
        # Cleanup - destroy VM
        print(f"  🧹 Cleaning up VM {vm_name}...")
        self.run_command(f"python3 -m dockvirt.cli down --name {vm_name}")
        
        return True
    
    def test_example(self, example_dir: Path) -> Dict:
        """Test single example across different OS variants."""
        print(f"\n📁 Testing example: {example_dir.name}")
        print("=" * 50)
        
        results = {
            "name": example_dir.name,
            "path": str(example_dir),
            "build_success": False,
            "image_name": "",
            "os_tests": {}
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
                vm_success = self.test_example_vm(example_dir, image_name, os_variant)
                results["os_tests"][os_variant] = {
                    "success": vm_success,
                    "error": None
                }
                
                if vm_success:
                    print(f"  ✅ {os_variant}: SUCCESS")
                else:
                    print(f"  ❌ {os_variant}: FAILED")
                    
            except Exception as e:
                results["os_tests"][os_variant] = {
                    "success": False,
                    "error": str(e)
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
        successful_builds = sum(1 for r in self.test_results.values() if r["build_success"])
        
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
            
            if result["os_tests"]:
                report.append("")
                report.append("**OS Compatibility:**")
                for os_variant, test_result in result["os_tests"].items():
                    if test_result["success"]:
                        report.append(f"- ✅ {os_variant}: SUCCESS")
                    else:
                        error = test_result.get("error", "Unknown error")
                        report.append(f"- ❌ {os_variant}: FAILED - {error}")
            
            report.append("")
        
        return "\\n".join(report)
    
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
        # Generate report
        print("\\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        
        report = self.generate_report()
        print(report)
        


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

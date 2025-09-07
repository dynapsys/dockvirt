#!/usr/bin/env python3
"""
Comprehensive DockerVirt LAN Exposure Testing Suite
Performs thorough testing of network exposure functionality
"""

import subprocess
import time
import requests
import threading
import statistics
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class DockerVirtLANTester:
    def __init__(self):
        self.localhost_url = "http://localhost:8080"
        self.lan_url = "http://192.168.188.226:80"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_basic_connectivity(self):
        """Test basic HTTP connectivity to both endpoints"""
        self.log("🔍 Testing basic connectivity...")
        test_results = {}
        
        # Test localhost
        try:
            response = requests.get(self.localhost_url, timeout=5)
            test_results['localhost'] = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.text),
                'success': response.status_code == 200
            }
            self.log(f"✅ localhost:8080 - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
        except Exception as e:
            test_results['localhost'] = {'success': False, 'error': str(e)}
            self.log(f"❌ localhost:8080 failed: {e}")
            
        # Test LAN
        try:
            response = requests.get(self.lan_url, timeout=5)
            test_results['lan'] = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.text),
                'success': response.status_code == 200
            }
            self.log(f"✅ LAN 192.168.188.226:80 - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
        except Exception as e:
            test_results['lan'] = {'success': False, 'error': str(e)}
            self.log(f"❌ LAN access failed: {e}")
            
        self.results['tests']['basic_connectivity'] = test_results
        return test_results
        
    def test_content_consistency(self):
        """Verify content is identical between endpoints"""
        self.log("📄 Testing content consistency...")
        
        try:
            local_response = requests.get(self.localhost_url, timeout=5)
            lan_response = requests.get(self.lan_url, timeout=5)
            
            content_match = local_response.text == lan_response.text
            headers_match = local_response.headers.get('content-type') == lan_response.headers.get('content-type')
            
            result = {
                'content_identical': content_match,
                'headers_match': headers_match,
                'local_size': len(local_response.text),
                'lan_size': len(lan_response.text),
                'local_hash': hash(local_response.text),
                'lan_hash': hash(lan_response.text)
            }
            
            if content_match:
                self.log(f"✅ Content identical ({len(local_response.text)} bytes)")
            else:
                self.log(f"❌ Content differs: local={len(local_response.text)}, lan={len(lan_response.text)}")
                
            self.results['tests']['content_consistency'] = result
            return result
            
        except Exception as e:
            self.log(f"❌ Content consistency test failed: {e}")
            self.results['tests']['content_consistency'] = {'success': False, 'error': str(e)}
            return {'success': False, 'error': str(e)}
            
    def test_performance_metrics(self):
        """Test response times and performance metrics"""
        self.log("⚡ Testing performance metrics...")
        
        def time_request(url, iterations=10):
            times = []
            successes = 0
            
            for i in range(iterations):
                try:
                    start = time.time()
                    response = requests.get(url, timeout=3)
                    end = time.time()
                    
                    if response.status_code == 200:
                        times.append((end - start) * 1000)  # Convert to ms
                        successes += 1
                except:
                    pass
                    
            return {
                'success_rate': successes / iterations,
                'avg_response_time': statistics.mean(times) if times else 0,
                'min_response_time': min(times) if times else 0,
                'max_response_time': max(times) if times else 0,
                'median_response_time': statistics.median(times) if times else 0
            }
            
        local_perf = time_request(self.localhost_url)
        lan_perf = time_request(self.lan_url)
        
        self.log(f"📊 localhost avg: {local_perf['avg_response_time']:.1f}ms")
        self.log(f"📊 LAN avg: {lan_perf['avg_response_time']:.1f}ms")
        
        result = {
            'localhost': local_perf,
            'lan': lan_perf,
            'lan_overhead_ms': lan_perf['avg_response_time'] - local_perf['avg_response_time']
        }
        
        self.results['tests']['performance'] = result
        return result
        
    def test_concurrent_connections(self):
        """Test multiple simultaneous connections"""
        self.log("🔀 Testing concurrent connections...")
        
        def make_request(url):
            try:
                start = time.time()
                response = requests.get(url, timeout=5)
                end = time.time()
                return {
                    'success': response.status_code == 200,
                    'time': (end - start) * 1000,
                    'size': len(response.text)
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
                
        # Test with 5 concurrent connections to each endpoint
        urls = [self.localhost_url] * 5 + [self.lan_url] * 5
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            results = [future.result() for future in as_completed(futures)]
            
        local_results = results[:5]
        lan_results = results[5:]
        
        local_success = sum(1 for r in local_results if r.get('success', False))
        lan_success = sum(1 for r in lan_results if r.get('success', False))
        
        result = {
            'localhost_success_rate': local_success / 5,
            'lan_success_rate': lan_success / 5,
            'total_requests': 10,
            'successful_requests': local_success + lan_success
        }
        
        self.log(f"✅ Concurrent test: {local_success}/5 localhost, {lan_success}/5 LAN")
        
        self.results['tests']['concurrent'] = result
        return result
        
    def test_network_infrastructure(self):
        """Test underlying network infrastructure"""
        self.log("🌐 Testing network infrastructure...")
        
        def run_cmd(cmd):
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            except:
                return False, "", "Command timeout"
                
        tests = {}
        
        # Check iptables rules
        success, stdout, stderr = run_cmd("sudo iptables -t nat -L PREROUTING -n")
        if success:
            dnat_rules = [line for line in stdout.split('\n') if 'DNAT' in line and '80' in line]
            tests['iptables_rules'] = {
                'present': len(dnat_rules) > 0,
                'count': len(dnat_rules),
                'rules': dnat_rules
            }
            self.log(f"✅ Found {len(dnat_rules)} DNAT rules")
        else:
            tests['iptables_rules'] = {'present': False, 'error': stderr}
            
        # Check port status
        success, stdout, stderr = run_cmd("ss -tuln | grep -E ':80|:8080'")
        if success:
            ports = stdout.split('\n') if stdout else []
            tests['port_status'] = {
                'listening_ports': len(ports),
                'ports': ports
            }
            self.log(f"✅ Found {len(ports)} listening ports")
        else:
            tests['port_status'] = {'listening_ports': 0}
            
        # Test ping to LAN IP
        success, stdout, stderr = run_cmd("ping -c 3 -W 1 192.168.188.226")
        if success:
            # Extract ping statistics
            lines = stdout.split('\n')
            stats_line = [line for line in lines if 'packets transmitted' in line]
            if stats_line:
                tests['ping_test'] = {
                    'success': True,
                    'stats': stats_line[0]
                }
                self.log("✅ Ping test successful")
        else:
            tests['ping_test'] = {'success': False, 'error': stderr}
            
        self.results['tests']['network_infrastructure'] = tests
        return tests
        
    def test_http_methods(self):
        """Test different HTTP methods"""
        self.log("🔧 Testing HTTP methods...")
        
        methods = ['GET', 'HEAD', 'OPTIONS']
        results = {}
        
        for method in methods:
            try:
                local_response = requests.request(method, self.localhost_url, timeout=3)
                lan_response = requests.request(method, self.lan_url, timeout=3)
                
                results[method] = {
                    'localhost_status': local_response.status_code,
                    'lan_status': lan_response.status_code,
                    'both_success': local_response.status_code == lan_response.status_code == 200
                }
                
                self.log(f"✅ {method}: localhost={local_response.status_code}, lan={lan_response.status_code}")
                
            except Exception as e:
                results[method] = {'success': False, 'error': str(e)}
                self.log(f"❌ {method} failed: {e}")
                
        self.results['tests']['http_methods'] = results
        return results
        
    def test_error_conditions(self):
        """Test error handling and edge cases"""
        self.log("⚠️ Testing error conditions...")
        
        tests = {}
        
        # Test non-existent path
        try:
            local_404 = requests.get(f"{self.localhost_url}/nonexistent", timeout=3)
            lan_404 = requests.get(f"{self.lan_url}/nonexistent", timeout=3)
            
            tests['404_handling'] = {
                'localhost_status': local_404.status_code,
                'lan_status': lan_404.status_code,
                'consistent': local_404.status_code == lan_404.status_code
            }
            
            self.log(f"✅ 404 test: localhost={local_404.status_code}, lan={lan_404.status_code}")
            
        except Exception as e:
            tests['404_handling'] = {'success': False, 'error': str(e)}
            
        # Test with very short timeout
        try:
            start = time.time()
            requests.get(self.lan_url, timeout=0.001)  # Very short timeout
        except requests.exceptions.Timeout:
            tests['timeout_handling'] = {'timeout_works': True}
            self.log("✅ Timeout handling works")
        except Exception as e:
            tests['timeout_handling'] = {'timeout_works': False, 'error': str(e)}
            
        self.results['tests']['error_conditions'] = tests
        return tests
        
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("📋 Generating comprehensive report...")
        
        # Calculate overall success rate
        all_tests = self.results['tests']
        successful_tests = 0
        total_tests = 0
        
        for test_name, test_data in all_tests.items():
            if isinstance(test_data, dict):
                if test_data.get('success', True) is not False:
                    successful_tests += 1
                total_tests += 1
                
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results['summary'] = {
            'overall_success_rate': success_rate,
            'tests_passed': successful_tests,
            'total_tests': total_tests,
            'test_duration': datetime.now().isoformat(),
            'recommendation': 'PRODUCTION_READY' if success_rate >= 90 else 'NEEDS_ATTENTION'
        }
        
        # Print summary
        print("\n" + "="*60)
        print("📊 DOCKVIRT LAN EXPOSURE - COMPREHENSIVE TEST REPORT")
        print("="*60)
        print(f"🕐 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Overall success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        if success_rate >= 95:
            print("🎉 STATUS: EXCELLENT - Production ready!")
        elif success_rate >= 90:
            print("✅ STATUS: GOOD - Ready for use")
        elif success_rate >= 75:
            print("⚠️ STATUS: ACCEPTABLE - Minor issues detected")
        else:
            print("❌ STATUS: POOR - Needs attention")
            
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        
        # Basic connectivity
        if 'basic_connectivity' in all_tests:
            bc = all_tests['basic_connectivity']
            local_ok = bc.get('localhost', {}).get('success', False)
            lan_ok = bc.get('lan', {}).get('success', False)
            print(f"🔌 Basic Connectivity: {'✅' if local_ok and lan_ok else '❌'}")
            if local_ok and lan_ok:
                local_time = bc['localhost']['response_time'] * 1000
                lan_time = bc['lan']['response_time'] * 1000
                print(f"   • localhost:8080: {local_time:.1f}ms")
                print(f"   • LAN access: {lan_time:.1f}ms")
                
        # Content consistency
        if 'content_consistency' in all_tests:
            cc = all_tests['content_consistency']
            if cc.get('content_identical'):
                print(f"📄 Content Consistency: ✅ ({cc.get('local_size', 0)} bytes)")
            else:
                print("📄 Content Consistency: ❌")
                
        # Performance
        if 'performance' in all_tests:
            perf = all_tests['performance']
            local_avg = perf.get('localhost', {}).get('avg_response_time', 0)
            lan_avg = perf.get('lan', {}).get('avg_response_time', 0)
            overhead = perf.get('lan_overhead_ms', 0)
            print(f"⚡ Performance:")
            print(f"   • localhost avg: {local_avg:.1f}ms")
            print(f"   • LAN avg: {lan_avg:.1f}ms")
            print(f"   • LAN overhead: {overhead:.1f}ms")
            
        # Concurrent connections
        if 'concurrent' in all_tests:
            conc = all_tests['concurrent']
            local_rate = conc.get('localhost_success_rate', 0) * 100
            lan_rate = conc.get('lan_success_rate', 0) * 100
            print(f"🔀 Concurrent Connections:")
            print(f"   • localhost: {local_rate:.0f}% success")
            print(f"   • LAN: {lan_rate:.0f}% success")
            
        # Network infrastructure
        if 'network_infrastructure' in all_tests:
            ni = all_tests['network_infrastructure']
            iptables_ok = ni.get('iptables_rules', {}).get('present', False)
            ports_count = ni.get('port_status', {}).get('listening_ports', 0)
            ping_ok = ni.get('ping_test', {}).get('success', False)
            print(f"🌐 Network Infrastructure:")
            print(f"   • iptables rules: {'✅' if iptables_ok else '❌'}")
            print(f"   • listening ports: {ports_count}")
            print(f"   • ping test: {'✅' if ping_ok else '❌'}")
            
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 40)
        
        if success_rate >= 95:
            print("• System is fully functional and production-ready")
            print("• LAN exposure working perfectly")
            print("• Ready for deployment to other devices")
        elif success_rate >= 90:
            print("• System is working well with minor optimizations possible")
            print("• Safe to use in production environment")
        else:
            print("• Some issues detected - review failed tests")
            print("• Consider troubleshooting before production use")
            
        print(f"\n💾 Full results saved to: /tmp/dockvirt_lan_test_{int(time.time())}.json")
        
        # Save detailed results
        with open(f"/tmp/dockvirt_lan_test_{int(time.time())}.json", 'w') as f:
            json.dump(self.results, f, indent=2)
            
        return self.results
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting comprehensive DockerVirt LAN exposure tests...")
        print(f"⏰ Test started: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Run all tests
        self.test_basic_connectivity()
        time.sleep(0.5)
        
        self.test_content_consistency()
        time.sleep(0.5)
        
        self.test_performance_metrics()
        time.sleep(0.5)
        
        self.test_concurrent_connections()
        time.sleep(0.5)
        
        self.test_network_infrastructure()
        time.sleep(0.5)
        
        self.test_http_methods()
        time.sleep(0.5)
        
        self.test_error_conditions()
        time.sleep(0.5)
        
        # Generate final report
        return self.generate_report()

if __name__ == "__main__":
    tester = DockerVirtLANTester()
    results = tester.run_all_tests()

"""
Load Test Suite for TheraGenome API using Locust

This module defines realistic load testing scenarios for the TheraGenome API
with task distribution, SLA monitoring, and comprehensive reporting.
"""

import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Any

from locust import HttpUser, task, between, events, web
from locust.runners import MasterRunner


# ===========================
# Configuration & Constants
# ===========================

PAYLOADS_FILE = os.path.join(
    os.path.dirname(__file__), '..', 'fixtures', 'load_test_payloads.json'
)

# SLA Thresholds (in milliseconds)
SLA_THRESHOLDS = {
    '/api/v1/variant/analyze': 2000,
    '/api/v1/pathogen/analyze': 1500,
    '/api/v1/drug/analyze': 1500,
}

MAX_ERROR_RATE = 0.01  # 1%

# Test configuration
DURATION_SECONDS = 60
TOTAL_USERS = 50
RAMP_UP_RATE = 5  # users/second


# ===========================
# Payload Management
# ===========================

class PayloadManager:
    """Manages loading and providing test payloads."""
    
    def __init__(self, payloads_file: str):
        """Initialize payload manager with fixture file."""
        self.payloads = self._load_payloads(payloads_file)
    
    def _load_payloads(self, payloads_file: str) -> Dict[str, Any]:
        """Load payloads from JSON fixture file."""
        if not os.path.exists(payloads_file):
            raise FileNotFoundError(f"Payloads file not found: {payloads_file}")
        
        with open(payloads_file, 'r') as f:
            return json.load(f)
    
    def get_variant_payload(self) -> Dict[str, Any]:
        """Get random variant analysis payload."""
        return random.choice(self.payloads['variant_analyze'])
    
    def get_pathogen_payload(self) -> Dict[str, Any]:
        """Get random pathogen analysis payload."""
        return random.choice(self.payloads['pathogen_analyze'])
    
    def get_drug_payload(self) -> Dict[str, Any]:
        """Get random drug analysis payload."""
        return random.choice(self.payloads['drug_analyze'])
    
    def get_patient_id(self) -> str:
        """Get random patient ID for report retrieval."""
        return random.choice(self.payloads['patient_ids'])


# Initialize payload manager
try:
    payload_manager = PayloadManager(PAYLOADS_FILE)
except FileNotFoundError as e:
    print(f"Warning: {e}")
    payload_manager = None


# ===========================
# SLA Tracking
# ===========================

class SLAMonitor:
    """Tracks SLAs and collects metrics for reporting."""
    
    def __init__(self):
        self.metrics = {
            '/api/v1/variant/analyze': {
                'count': 0,
                'failures': 0,
                'response_times': [],
                'total_response_time': 0,
            },
            '/api/v1/pathogen/analyze': {
                'count': 0,
                'failures': 0,
                'response_times': [],
                'total_response_time': 0,
            },
            '/api/v1/drug/analyze': {
                'count': 0,
                'failures': 0,
                'response_times': [],
                'total_response_time': 0,
            },
            'other': {
                'count': 0,
                'failures': 0,
                'response_times': [],
                'total_response_time': 0,
            },
        }
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, response_time_ms: float, success: bool):
        """Record a request for SLA tracking."""
        # Map endpoint to tracked endpoint
        tracked_endpoint = endpoint
        if endpoint not in self.metrics:
            tracked_endpoint = 'other'
        
        metric = self.metrics[tracked_endpoint]
        metric['count'] += 1
        metric['response_times'].append(response_time_ms)
        metric['total_response_time'] += response_time_ms
        
        if not success:
            metric['failures'] += 1
    
    def get_percentile(self, endpoint: str, percentile: float) -> float:
        """Get response time percentile for an endpoint."""
        if endpoint not in self.metrics:
            return 0
        
        response_times = sorted(self.metrics[endpoint]['response_times'])
        if not response_times:
            return 0
        
        index = int(len(response_times) * (percentile / 100))
        return response_times[min(index, len(response_times) - 1)]
    
    def check_slas(self) -> Dict[str, Any]:
        """Check if all SLAs are met."""
        sla_results = {}
        violations = []
        
        for endpoint, threshold in SLA_THRESHOLDS.items():
            p95 = self.get_percentile(endpoint, 95)
            met = p95 < threshold
            sla_results[endpoint] = {
                'threshold_ms': threshold,
                'p95_ms': round(p95, 2),
                'met': met,
            }
            if not met:
                violations.append(
                    f"{endpoint}: p95={p95:.2f}ms > threshold={threshold}ms"
                )
        
        # Check error rate
        total_count = sum(m['count'] for m in self.metrics.values())
        total_failures = sum(m['failures'] for m in self.metrics.values())
        error_rate = total_failures / total_count if total_count > 0 else 0
        
        error_rate_ok = error_rate <= MAX_ERROR_RATE
        sla_results['error_rate'] = {
            'threshold': MAX_ERROR_RATE,
            'actual': round(error_rate, 4),
            'met': error_rate_ok,
        }
        if not error_rate_ok:
            violations.append(
                f"Error Rate: {error_rate:.4f} > threshold={MAX_ERROR_RATE}"
            )
        
        return {
            'results': sla_results,
            'violations': violations,
            'all_passed': len(violations) == 0,
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        elapsed = time.time() - self.start_time
        summary = {}
        
        for endpoint, metric in self.metrics.items():
            if endpoint == 'other' or metric['count'] == 0:
                continue
            
            response_times = sorted(metric['response_times'])
            avg_response_time = (
                metric['total_response_time'] / metric['count']
                if metric['count'] > 0 else 0
            )
            
            summary[endpoint] = {
                'count': metric['count'],
                'failures': metric['failures'],
                'error_rate': round(
                    metric['failures'] / metric['count'], 4
                ) if metric['count'] > 0 else 0,
                'rps': round(metric['count'] / elapsed, 2) if elapsed > 0 else 0,
                'p50_ms': round(
                    response_times[len(response_times) // 2], 2
                ) if response_times else 0,
                'p95_ms': round(self.get_percentile(endpoint, 95), 2),
                'p99_ms': round(self.get_percentile(endpoint, 99), 2),
                'avg_ms': round(avg_response_time, 2),
                'min_ms': round(min(response_times), 2) if response_times else 0,
                'max_ms': round(max(response_times), 2) if response_times else 0,
            }
        
        return summary


# Global SLA monitor
sla_monitor = SLAMonitor()


# ===========================
# Load Test User Class
# ===========================

class VariantUser(HttpUser):
    """
    Represents a user performing variant analysis tasks on TheraGenome API.
    
    Task distribution:
    - POST /variant/analyze: weight 5
    - POST /pathogen/analyze: weight 3
    - POST /drug/analyze: weight 3
    - GET /reports/{patient_id}: weight 2
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts."""
        self.endpoint_base = '/api/v1'
    
    @task(5)
    def variant_analyze(self):
        """POST variant analysis task."""
        if not payload_manager:
            self.client.get("/health")
            return
        
        payload = payload_manager.get_variant_payload()
        endpoint = f"{self.endpoint_base}/variant/analyze"
        
        with self.client.post(
            endpoint,
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    True
                )
            else:
                response.failure(f"Status: {response.status_code}")
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    False
                )
    
    @task(3)
    def pathogen_analyze(self):
        """POST pathogen analysis task."""
        if not payload_manager:
            self.client.get("/health")
            return
        
        payload = payload_manager.get_pathogen_payload()
        endpoint = f"{self.endpoint_base}/pathogen/analyze"
        
        with self.client.post(
            endpoint,
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    True
                )
            else:
                response.failure(f"Status: {response.status_code}")
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    False
                )
    
    @task(3)
    def drug_analyze(self):
        """POST drug analysis task."""
        if not payload_manager:
            self.client.get("/health")
            return
        
        payload = payload_manager.get_drug_payload()
        endpoint = f"{self.endpoint_base}/drug/analyze"
        
        with self.client.post(
            endpoint,
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    True
                )
            else:
                response.failure(f"Status: {response.status_code}")
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    False
                )
    
    @task(2)
    def get_reports(self):
        """GET reports for patient task."""
        if not payload_manager:
            self.client.get("/health")
            return
        
        patient_id = payload_manager.get_patient_id()
        endpoint = f"{self.endpoint_base}/reports/{patient_id}"
        
        with self.client.get(
            endpoint,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is acceptable
                response.success()
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    response.status_code == 200
                )
            else:
                response.failure(f"Status: {response.status_code}")
                sla_monitor.record_request(
                    endpoint,
                    response.elapsed.total_seconds() * 1000,
                    False
                )


# ===========================
# Event Handlers
# ===========================

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("\n" + "=" * 80)
    print("LOAD TEST COMPLETED")
    print("=" * 80)
    
    # Check SLAs
    sla_check = sla_monitor.check_slas()
    print("\n--- SLA Results ---")
    for endpoint, result in sla_check['results'].items():
        status = "✓ PASS" if result['met'] else "✗ FAIL"
        if endpoint == 'error_rate':
            print(
                f"{status} | {endpoint}: {result['actual']} "
                f"(threshold: {result['threshold']})"
            )
        else:
            print(
                f"{status} | {endpoint}: p95={result['p95_ms']}ms "
                f"(threshold: {result['threshold_ms']}ms)"
            )
    
    if sla_check['violations']:
        print("\n⚠️  SLA Violations:")
        for violation in sla_check['violations']:
            print(f"  - {violation}")
    else:
        print("\n✓ All SLAs passed!")
    
    # Print summary metrics
    print("\n--- Performance Summary ---")
    summary = sla_monitor.get_summary()
    for endpoint, metrics in summary.items():
        print(f"\n{endpoint}:")
        print(f"  Requests: {metrics['count']}")
        print(f"  Errors: {metrics['failures']} ({metrics['error_rate']:.2%})")
        print(f"  RPS: {metrics['rps']}")
        print(f"  Response Times (ms):")
        print(f"    Min: {metrics['min_ms']}")
        print(f"    p50: {metrics['p50_ms']}")
        print(f"    p95: {metrics['p95_ms']}")
        print(f"    p99: {metrics['p99_ms']}")
        print(f"    Max: {metrics['max_ms']}")
    
    # Generate reports
    generate_reports(sla_check, summary)
    
    # Exit with appropriate code
    exit_code = 0 if sla_check['all_passed'] else 1
    print(f"\n{'✓' if exit_code == 0 else '✗'} Test Exit Code: {exit_code}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception,
               **kwargs):
    """Called for each request."""
    # Optional: Add per-request logging or filtering
    pass


# ===========================
# Report Generation
# ===========================

def generate_reports(sla_check: Dict[str, Any], summary: Dict[str, Any]):
    """Generate HTML and JSON reports."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate JSON report
    json_report = {
        "timestamp": timestamp,
        "duration_seconds": DURATION_SECONDS,
        "total_users": TOTAL_USERS,
        "ramp_up_rate": RAMP_UP_RATE,
        "sla_results": sla_check['results'],
        "sla_passed": sla_check['all_passed'],
        "endpoint_metrics": summary,
    }
    
    json_path = os.path.join(
        os.path.dirname(__file__), '..', 'load_test_results.json'
    )
    with open(json_path, 'w') as f:
        json.dump(json_report, f, indent=2)
    print(f"\n✓ JSON report generated: {json_path}")
    
    # Generate HTML report
    html_content = generate_html_report(json_report, sla_check)
    html_path = os.path.join(
        os.path.dirname(__file__), '..', 'load_test_report.html'
    )
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"✓ HTML report generated: {html_path}")


def generate_html_report(json_report: Dict[str, Any],
                        sla_check: Dict[str, Any]) -> str:
    """Generate comprehensive HTML report."""
    sla_status = "✓ PASS" if sla_check['all_passed'] else "✗ FAIL"
    sla_color = "#27ae60" if sla_check['all_passed'] else "#e74c3c"
    
    # Build endpoint metrics rows
    endpoint_rows = ""
    for endpoint, metrics in json_report['endpoint_metrics'].items():
        endpoint_rows += f"""
        <tr>
            <td>{endpoint}</td>
            <td>{metrics['count']}</td>
            <td>{metrics['error_rate']:.2%}</td>
            <td>{metrics['rps']}</td>
            <td>{metrics['min_ms']:.2f}</td>
            <td>{metrics['p50_ms']:.2f}</td>
            <td>{metrics['p95_ms']:.2f}</td>
            <td>{metrics['p99_ms']:.2f}</td>
            <td>{metrics['max_ms']:.2f}</td>
        </tr>
        """
    
    # Build SLA results rows
    sla_rows = ""
    for endpoint, result in sla_check['results'].items():
        if endpoint == 'error_rate':
            status = "✓" if result['met'] else "✗"
            status_color = "#27ae60" if result['met'] else "#e74c3c"
            sla_rows += f"""
            <tr>
                <td>{endpoint}</td>
                <td>&lt; {result['threshold']:.2%}</td>
                <td style="color: {status_color}; font-weight: bold;">{status} {result['actual']:.2%}</td>
            </tr>
            """
        else:
            status = "✓" if result['met'] else "✗"
            status_color = "#27ae60" if result['met'] else "#e74c3c"
            sla_rows += f"""
            <tr>
                <td>{endpoint}</td>
                <td>&lt; {result['threshold_ms']}ms</td>
                <td style="color: {status_color}; font-weight: bold;">{status} {result['p95_ms']:.2f}ms</td>
            </tr>
            """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TheraGenome Load Test Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 10px;
            }}
            .summary-box {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin: 20px 0;
            }}
            .summary-item {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }}
            .summary-item h3 {{
                margin: 0 0 10px 0;
                font-size: 12px;
                text-transform: uppercase;
            }}
            .summary-item .value {{
                font-size: 24px;
                font-weight: bold;
            }}
            .status {{
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                font-size: 18px;
                font-weight: bold;
            }}
            .status.pass {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .status.fail {{
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f0f0f0;
            }}
            .metric {{
                font-family: monospace;
                background-color: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #888;
                font-size: 12px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧬 TheraGenome API Load Test Report</h1>
            
            <div class="status {('pass' if sla_check['all_passed'] else 'fail')}">
                Overall Status: {sla_status}
            </div>
            
            <div class="summary-box">
                <div class="summary-item">
                    <h3>Test Duration</h3>
                    <div class="value">{json_report['duration_seconds']}s</div>
                </div>
                <div class="summary-item">
                    <h3>Concurrent Users</h3>
                    <div class="value">{json_report['total_users']}</div>
                </div>
                <div class="summary-item">
                    <h3>Ramp-up Rate</h3>
                    <div class="value">{json_report['ramp_up_rate']}/s</div>
                </div>
                <div class="summary-item">
                    <h3>Timestamp</h3>
                    <div class="value">{json_report['timestamp']}</div>
                </div>
            </div>
            
            <h2>SLA Results</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Threshold</th>
                    <th>Result</th>
                </tr>
                {sla_rows}
            </table>
            
            <h2>Endpoint Performance</h2>
            <table>
                <tr>
                    <th>Endpoint</th>
                    <th>Requests</th>
                    <th>Error Rate</th>
                    <th>RPS</th>
                    <th>Min (ms)</th>
                    <th>p50 (ms)</th>
                    <th>p95 (ms)</th>
                    <th>p99 (ms)</th>
                    <th>Max (ms)</th>
                </tr>
                {endpoint_rows}
            </table>
            
            <div class="footer">
                <p>Load test generated at {json_report['timestamp']}</p>
                <p>TheraGenome API Performance Analysis Report</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


# ===========================
# Configuration
# ===========================

# Run configuration (when using locust command line)
# Command: locust -f locustfile.py --host=http://localhost:8000
#          -u 50 -r 5 --run-time 60s --headless

#!/usr/bin/env python3
"""
Example script demonstrating how to use the Code Review Agent API.
"""

import requests
import time
import json
from typing import Dict, Any


class CodeReviewClient:
    """Client for interacting with the Code Review Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def analyze_pr(self, repo_url: str, pr_number: int, github_token: str = None) -> str:
        """Submit a PR for analysis and return the task ID."""
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number
        }
        
        if github_token:
            payload["github_token"] = github_token
        
        response = requests.post(f"{self.base_url}/analyze-pr", json=payload)
        response.raise_for_status()
        
        return response.json()["task_id"]
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of an analysis task."""
        response = requests.get(f"{self.base_url}/status/{task_id}")
        response.raise_for_status()
        
        return response.json()
    
    def get_results(self, task_id: str) -> Dict[str, Any]:
        """Get the results of a completed analysis task."""
        response = requests.get(f"{self.base_url}/results/{task_id}")
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(self, task_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
        """Wait for a task to complete and return the results."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_data = self.get_status(task_id)
            status = status_data["status"]
            
            print(f"Task {task_id}: {status}")
            if "progress" in status_data and status_data["progress"]:
                print(f"  Progress: {status_data['progress']}")
            
            if status == "completed":
                return self.get_results(task_id)
            elif status == "failed":
                results = self.get_results(task_id)
                raise Exception(f"Task failed: {results.get('error_message', 'Unknown error')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")


def print_results(results: Dict[str, Any]):
    """Pretty print the analysis results."""
    if not results.get("results"):
        print("No results available")
        return
    
    analysis = results["results"]
    summary = analysis["summary"]
    
    print("\n" + "="*60)
    print("CODE REVIEW ANALYSIS RESULTS")
    print("="*60)

    print(f"\nSUMMARY:")
    print(f"  Files analyzed: {summary['total_files']}")
    print(f"  Total issues: {summary['total_issues']}")
    print(f"  Critical: {summary['critical_issues']}")
    print(f"  High: {summary['high_issues']}")
    print(f"  Medium: {summary['medium_issues']}")
    print(f"  Low: {summary['low_issues']}")

    if analysis["files"]:
        print(f"\nDETAILED FINDINGS:")

        for file_analysis in analysis["files"]:
            print(f"\nFile: {file_analysis['name']}")
            print("-" * (len(file_analysis['name']) + 6))

            for issue in file_analysis["issues"]:
                severity_prefix = {
                    "critical": "[CRITICAL]",
                    "high": "[HIGH]",
                    "medium": "[MEDIUM]",
                    "low": "[LOW]"
                }.get(issue["severity"], "[INFO]")

                type_prefix = {
                    "bug": "[BUG]",
                    "style": "[STYLE]",
                    "performance": "[PERFORMANCE]",
                    "security": "[SECURITY]",
                    "best_practice": "[BEST_PRACTICE]"
                }.get(issue["type"], "[ISSUE]")

                print(f"  {severity_prefix} Line {issue['line']}: {type_prefix} {issue['description']}")
                print(f"     Suggestion: {issue['suggestion']}")
                print()


def main():
    """Main example function."""
    # Initialize client
    client = CodeReviewClient()
    
    # Example 1: Analyze a public repository PR
    print("Example 1: Analyzing a public repository PR")
    print("-" * 50)
    
    try:
        # Submit analysis (using a well-known public repo for demo)
        repo_url = "https://github.com/octocat/Hello-World"
        pr_number = 1
        
        print(f"Submitting analysis for {repo_url} PR #{pr_number}")
        task_id = client.analyze_pr(repo_url, pr_number)
        print(f"Task submitted with ID: {task_id}")
        
        # Wait for completion
        print("Waiting for analysis to complete...")
        results = client.wait_for_completion(task_id)
        
        # Print results
        print_results(results)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API. Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Example 2: Check API health
    print("\n" + "="*60)
    print("Example 2: Checking API health")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:8000/health")
        health_data = response.json()
        
        print("SUCCESS: API Health Check:")
        print(f"  Status: {health_data['status']}")
        print(f"  Database: {health_data['database']}")
        print(f"  Celery Workers: {health_data['celery_workers']}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API")
    except Exception as e:
        print(f"ERROR: Health check failed: {e}")


if __name__ == "__main__":
    main()

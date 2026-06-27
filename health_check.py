#!/usr/bin/env python3
import sys
import urllib.request
import urllib.error
import json

BASE = "http://localhost"
CHECKS = [
    ("/health", "Backend health"),
    ("/api/health", "Backend API health"),
    ("/api/auth/demo-users", "Demo users endpoint"),
]

def check(path, label):
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            print(f"  [OK] {label}: {url}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] {label}: HTTP {e.code} at {url}")
        return False
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        return False

def main():
    print("\nLogiSense 360 Health Check")
    print("=" * 40)
    results = [check(path, label) for path, label in CHECKS]
    print("=" * 40)
    if all(results):
        print("All checks passed. Platform is ready!")
        print("Open: http://localhost")
        sys.exit(0)
    else:
        failed = sum(1 for r in results if not r)
        print(f"{failed}/{len(results)} checks failed.")
        print("Run: make logs-backend   to diagnose")
        sys.exit(1)

if __name__ == "__main__":
    main()

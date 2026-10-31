#!/usr/bin/env python3
"""Stand-in for the proxy check (backend services/proxies/check_script.py) in tests.

Reads the proxy address on stdin like the real one. Addresses containing "dead" fail,
"garbage" prints something that isn't JSON; any other address works."""

import json
import sys

proxy = sys.stdin.read().strip()
if "garbage" in proxy:
    print("not json")
elif "dead" in proxy:
    json.dump({"ok": False, "exit_ip": None, "error": f"Unable to connect to proxy {proxy}"}, sys.stdout)
else:
    json.dump({"ok": True, "exit_ip": "203.0.113.7 (ZZ)", "error": None}, sys.stdout)

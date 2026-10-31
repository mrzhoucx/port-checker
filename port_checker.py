#!/usr/bin/env python3
"""port-checker: check TCP reachability and connect latency for host:port targets.

Zero dependencies, standard library only.

Usage:
    python3 port_checker.py example.com:443 8.8.8.8:53
    python3 port_checker.py --timeout 2 --file targets.txt
    python3 port_checker.py --json example.com:443

Exit code is 0 when every target is reachable, 1 otherwise, so it can
be used directly in cron jobs and deploy health checks.
"""

import argparse
import concurrent.futures
import json
import socket
import sys
import time


def parse_target(text):
    """Parse 'host:port' into (host, port). Raises ValueError on bad input."""
    text = text.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith("["):  # [ipv6]:port
        host, _, rest = text[1:].partition("]:")
        if not rest:
            raise ValueError(f"bad target (expected [ipv6]:port): {text!r}")
        return host, int(rest)
    host, sep, port = text.rpartition(":")
    if not sep or not host or not port.isdigit():
        raise ValueError(f"bad target (expected host:port): {text!r}")
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError(f"port out of range: {port}")
    return host, port


def check_one(target, timeout):
    """Attempt one TCP connect; return a result dict (never raises)."""
    host, port = target
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {"target": f"{host}:{port}", "ok": True,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
                "error": None}
    except (socket.timeout, TimeoutError):
        return {"target": f"{host}:{port}", "ok": False,
                "latency_ms": None, "error": "timeout"}
    except OSError as exc:
        return {"target": f"{host}:{port}", "ok": False,
                "latency_ms": None, "error": str(exc) or exc.__class__.__name__}


def load_targets(args):
    targets = []
    for raw in args.targets:
        parsed = parse_target(raw)
        if parsed:
            targets.append(parsed)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            for line in fh:
                parsed = parse_target(line)
                if parsed:
                    targets.append(parsed)
    if not targets:
        raise SystemExit("no targets given: pass host:port arguments or --file")
    return targets


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check TCP reachability of host:port targets.")
    parser.add_argument("targets", nargs="*", help="host:port targets, e.g. example.com:443")
    parser.add_argument("--file", "-f", help="file with one host:port per line (# comments allowed)")
    parser.add_argument("--timeout", "-t", type=float, default=3.0, help="connect timeout in seconds (default 3)")
    parser.add_argument("--workers", "-w", type=int, default=20, help="parallel workers (default 20)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args(argv)

    targets = load_targets(args)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(lambda t: check_one(t, args.timeout), targets))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        width = max(len(r["target"]) for r in results)
        for r in results:
            status = "OK  " if r["ok"] else "FAIL"
            detail = f"{r['latency_ms']} ms" if r["ok"] else r["error"]
            print(f"{status} {r['target']:<{width}}  {detail}")
        ok = sum(r["ok"] for r in results)
        print(f"\n{ok}/{len(results)} reachable")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

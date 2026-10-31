# port-checker

Check TCP reachability and connect latency for a list of `host:port` targets, in parallel, with zero dependencies (Python 3 standard library only).

Useful for quickly verifying that services on a VPS or remote host are actually listening — e.g. after a deploy, a firewall change, or a reboot — and for wiring a simple up/down check into cron.

## Install

Requires Python 3.8+. No packages to install:

```sh
git clone https://github.com/mrzhoucx/port-checker.git
cd port-checker
```

## Usage

```sh
# Check a few targets directly
python3 port_checker.py example.com:443 8.8.8.8:53

# Read targets from a file (one host:port per line, # comments allowed)
python3 port_checker.py --file targets.txt

# Shorter timeout, JSON output for scripting
python3 port_checker.py --timeout 2 --json example.com:443 localhost:22
```

Example output:

```
OK   example.com:443  42.3 ms
FAIL localhost:9999   [Errno 111] Connection refused

1/2 reachable
```

## Exit code

- `0` — every target reachable
- `1` — at least one target failed

So it can be used directly in a cron health check:

```sh
python3 port_checker.py --file targets.txt || echo "a service is down"
```

## Options

| Flag | Meaning | Default |
| ---- | ------- | ------- |
| `--file`, `-f` | File with one `host:port` per line | — |
| `--timeout`, `-t` | Connect timeout in seconds | 3 |
| `--workers`, `-w` | Parallel workers | 20 |
| `--json` | Emit JSON instead of a table | off |

IPv6 works with bracket notation: `[2001:db8::1]:443`.

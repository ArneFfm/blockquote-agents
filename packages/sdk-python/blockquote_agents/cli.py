"""Command-line access to the Blockquote client."""
import argparse
import json
import os
import sys

from . import Blockquote, BlockquoteError


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="blockquote",
        description="Read and start Blockquote AI visibility scans.",
        epilog=("Set BLOCKQUOTE_API_KEY for account access. Public reads need no key. "
                "Scan creation can require a paid key or human verification. "
                "Set BLOCKQUOTE_TURNSTILE_TOKEN for a human verification token. "
                "Scans are asynchronous. Wait for Retry-After before reading the returned id. "
                "No automatic retries are made."),
    )
    commands = parser.add_subparsers(dest="command")
    scan = commands.add_parser("scan", help="Start a scan")
    scan.add_argument("url")
    scan.add_argument("--refresh", action="store_true", default=None)
    scan.add_argument("--idempotency-key")
    read = commands.add_parser("read", help="Read a report or pending status")
    read.add_argument("scan_id")
    compare = commands.add_parser("compare", help="Compare two scans")
    compare.add_argument("from_id")
    compare.add_argument("to_id")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        client = Blockquote(api_key=os.getenv("BLOCKQUOTE_API_KEY"))
        if args.command == "scan":
            result = client.start_scan(
                args.url, refresh=args.refresh,
                idempotency_key=args.idempotency_key,
                turnstile_token=os.getenv("BLOCKQUOTE_TURNSTILE_TOKEN"),
            )
        elif args.command == "read":
            result = client.get_scan(args.scan_id)
        else:
            result = client.compare_scans(from_id=args.from_id, to_id=args.to_id)
        print(json.dumps({"data": result.data, "status": result.status,
                          "headers": dict(result.headers.items())}, indent=2))
        return 0
    except BlockquoteError as error:
        print(json.dumps({"error": str(error), "status": error.status, "data": error.data,
                          "headers": dict(error.headers.items()),
                          "retryAfter": error.retry_after}), file=sys.stderr)
        return 1
    except Exception as error:
        # Header validation errors can contain credentials; print the error type only.
        print(json.dumps({"error": f"Request failed ({type(error).__name__})."}), file=sys.stderr)
        return 1

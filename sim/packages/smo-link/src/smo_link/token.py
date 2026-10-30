"""``python -m smo_link.token new|sign``: issue a session secret, or sign a
link credential for testing (e.g. with curl).

    python -m smo_link.token new [--session ID]
        prints SMO_LINK_SESSION=... and SMO_LINK_SECRET=... (env-file lines)
    python -m smo_link.token sign [--session ID] [--secret HEX | --secret-file F]
        prints an "Authorization: SMO-Link ..." header valid for 120 s, once
"""
from __future__ import annotations

import argparse
import os
import sys

from .auth import AuthError, load_secret, make_header, new_secret, new_session_id


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="smo-link-token")
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="issue a new session id and 32-byte secret")
    n.add_argument("--session", default=None)
    s = sub.add_parser("sign", help="print an Authorization header for /link")
    s.add_argument("--session", default=os.environ.get("SMO_LINK_SESSION"))
    s.add_argument("--secret", default=None)
    s.add_argument("--secret-file", default=None)
    args = p.parse_args(argv)
    if args.cmd == "new":
        print(f"SMO_LINK_SESSION={args.session or new_session_id()}")
        print(f"SMO_LINK_SECRET={new_secret()}")
        return 0
    if not args.session:
        print("smo-link-token: --session or SMO_LINK_SESSION required", file=sys.stderr)
        return 2
    try:
        secret = load_secret(args.secret, args.secret_file)
    except (AuthError, OSError) as e:
        print(f"smo-link-token: {e}", file=sys.stderr)
        return 2
    print("Authorization: " + make_header(secret, args.session))
    return 0


if __name__ == "__main__":
    sys.exit(main())

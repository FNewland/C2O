"""``python -m smo_link agent|gateway|token ...``"""
import sys


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    rest = sys.argv[2:]
    if cmd == "agent":
        from .agent import main as m
        m(rest)
    elif cmd in ("gateway", "gsg"):
        from .gateway import main as m
        m(rest)
    elif cmd == "token":
        from .token import main as m
        sys.exit(m(rest))
    else:
        print("usage: python -m smo_link {agent|gateway|token} [args]\n"
              "   or: python -m smo_link.agent | smo_link.gateway | smo_link.token",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

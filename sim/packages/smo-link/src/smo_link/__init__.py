"""SMO space link (smo-link, wire protocol v2).

One outbound WebSocket carries TM, TC, simulator state, dumps and proxied
instructor HTTP/WS between the space-link agent (next to the simulator) and
the ground-station gateway (GSG, which impersonates the simulator's TM 8002,
TC 8001 and HTTP 8080 on the ground host). See
docs/web_2026-10/LINK_DESIGN.md for the binding specification.
"""

__version__ = "0.2.0"

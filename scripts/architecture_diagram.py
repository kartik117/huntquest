"""Regenerates .github/assets/architecture.png.

Not part of the app -- a one-off documentation tool. Run with:
    pip install diagrams && python3 scripts/architecture_diagram.py
(requires graphviz: `brew install graphviz` / `apt install graphviz`)
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.client import Client
from diagrams.onprem.database import Postgresql
from diagrams.onprem.inmemory import Redis
from diagrams.programming.framework import React
from diagrams.programming.language import Python

graph_attr = {"fontsize": "14", "bgcolor": "white", "pad": "0.4", "nodesep": "0.7", "ranksep": "1.0"}

with Diagram(
    "HuntQuest Architecture",
    filename=".github/assets/architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    phone = Client("player's phone\n(real GPS via\nbrowser geolocation)")

    with Cluster("frontend (nginx)"):
        spa = React("React + Leaflet\nmap SPA")

    with Cluster("backend (FastAPI, one process per replica)"):
        api = Python("REST: join,\nhunt, leaderboard")
        ws = Python("WebSocket:\nlocation pings")
        checkpoints = Python("checkpoint\ngeofence check")
        ws >> checkpoints

    redis = Redis("Redis\nGEOADD/GEOSEARCH\n(live positions)\n+ pub/sub fan-out")
    postgres = Postgresql("Postgres\n(hunts, teams,\nplayers, history)")
    simulator = Python("simulator\n(walks real Seattle\nwaypoints over WS)")

    phone >> Edge(label="watchPosition()") >> spa
    spa >> Edge(label="fetch()") >> api
    spa >> Edge(label="WebSocket") >> ws

    ws >> Edge(label="GEOADD") >> redis
    checkpoints >> Edge(label="GEOSEARCH") >> redis
    checkpoints >> Edge(label="record find") >> postgres
    api >> postgres

    ws >> Edge(style="dashed", label="publish") >> redis
    redis >> Edge(style="dashed", label="psubscribe\n(fans out to every\nreplica's local sockets)") >> ws

    simulator >> Edge(label="WebSocket (same API\nas a real client)") >> ws

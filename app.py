"""Foundry demo app: version page, health check and a visit counter in Postgres."""
import os
import socket

import psycopg
from flask import Flask, jsonify

# To show a deploy or a preview, change one of these two lines and push.
APP_VERSION = "v4"
BG_COLOR = "#1e40af"

app = Flask(__name__)


@app.get("/")
def index():
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Foundry demo</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
           background: {BG_COLOR}; color: #fff; font-family: system-ui, sans-serif; }}
    main {{ text-align: center; }}
    h1 {{ font-size: 4rem; margin: 0; }}
    p {{ opacity: .8; }}
  </style>
</head>
<body>
  <main>
    <h1>{APP_VERSION}</h1>
    <p>Foundry demo app, served by container {socket.gethostname()}</p>
  </main>
</body>
</html>"""


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION)


@app.get("/visits")
def visits():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return jsonify(
            error="DATABASE_URL is not set",
            hint="Create a Postgres database, set DATABASE_URL on this app and redeploy.",
        ), 503
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS visits (id INT PRIMARY KEY, n BIGINT NOT NULL)"
            )
            row = conn.execute(
                "INSERT INTO visits (id, n) VALUES (1, 1) "
                "ON CONFLICT (id) DO UPDATE SET n = visits.n + 1 RETURNING n"
            ).fetchone()
        return jsonify(visits=row[0])
    except psycopg.Error as exc:
        # The real error goes to the app log; the public answer stays generic.
        app.logger.error("database error: %s", str(exc).strip())
        return jsonify(
            error="database unavailable",
            hint="Check DATABASE_URL and the database service. The details are in the app log.",
        ), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))

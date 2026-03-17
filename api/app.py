from __future__ import annotations

import os
from flask import Flask
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from flask_cors import CORS
from api.actions.documents import init_handlers as init_documents_handlers


def create_app() -> Flask:
    app: Flask = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    init_documents_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)


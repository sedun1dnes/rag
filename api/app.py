from __future__ import annotations

import os
from flask import Flask
from flask_cors import CORS

from shared.db import create_tables
from api.actions.knowledge_bases import init_handlers as init_knowledge_bases_handlers
from api.actions.documents import init_handlers as init_documents_handlers
from api.actions.chats import init_handlers as init_chats_handlers


def create_app() -> Flask:
    app: Flask = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    create_tables()

    init_knowledge_bases_handlers(app)
    init_documents_handlers(app)
    init_chats_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)

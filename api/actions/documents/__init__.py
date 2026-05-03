from flask import Flask, Blueprint
from api.actions.documents.handlers import delete_document


def init_handlers(app: Flask):
    documents_bp = Blueprint("documents", __name__, url_prefix="/documents")
    documents_bp.add_url_rule("/<doc_id>", view_func=delete_document, methods=["DELETE"])
    app.register_blueprint(documents_bp)

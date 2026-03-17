from flask import Flask, Blueprint
from api.actions.documents.handlers import get_documents, upload_documents

def init_handlers(app: Flask):
    documents_bp = Blueprint("documents", __name__, url_prefix="/documents")

    documents_bp.add_url_rule(
        "",
        view_func=get_documents,
        methods=['GET'],
    )
    documents_bp.add_url_rule(
        "/upload",
        view_func=upload_documents,
        methods=['POST']
    )
    app.register_blueprint(documents_bp)
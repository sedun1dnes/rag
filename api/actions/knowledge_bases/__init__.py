from flask import Flask, Blueprint
from api.actions.knowledge_bases.handlers import (
    list_knowledge_bases,
    create_knowledge_base,
    get_knowledge_base,
    delete_knowledge_base,
    upload_documents_to_kb,
)


def init_handlers(app: Flask):
    kb_bp = Blueprint("knowledge_bases", __name__, url_prefix="/knowledge-bases")

    kb_bp.add_url_rule("", view_func=list_knowledge_bases, methods=["GET"])
    kb_bp.add_url_rule("", view_func=create_knowledge_base, methods=["POST"])
    kb_bp.add_url_rule("/<kb_id>", view_func=get_knowledge_base, methods=["GET"])
    kb_bp.add_url_rule("/<kb_id>", view_func=delete_knowledge_base, methods=["DELETE"])
    kb_bp.add_url_rule("/<kb_id>/documents", view_func=upload_documents_to_kb, methods=["POST"])

    app.register_blueprint(kb_bp)

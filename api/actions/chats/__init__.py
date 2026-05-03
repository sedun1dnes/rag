from flask import Flask, Blueprint
from api.actions.chats.handlers import (
    list_chats,
    create_chat,
    delete_chat,
    send_message,
    get_messages,
)


def init_handlers(app: Flask):
    chats_bp = Blueprint("chats", __name__, url_prefix="/chats")

    chats_bp.add_url_rule("", view_func=list_chats, methods=["GET"])
    chats_bp.add_url_rule("", view_func=create_chat, methods=["POST"])
    chats_bp.add_url_rule("/<chat_id>", view_func=delete_chat, methods=["DELETE"])
    chats_bp.add_url_rule("/<chat_id>/messages", view_func=get_messages, methods=["GET"])
    chats_bp.add_url_rule("/<chat_id>/messages", view_func=send_message, methods=["POST"])

    app.register_blueprint(chats_bp)

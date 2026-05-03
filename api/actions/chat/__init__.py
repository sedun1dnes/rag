from flask import Flask, Blueprint
from api.actions.chat.handlers import post_message

def init_handlers(app: Flask):
    chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

    chat_bp.add_url_rule(
        "/new-message",
        view_func=post_message,
        methods=['POST']
    )
    app.register_blueprint(chat_bp)
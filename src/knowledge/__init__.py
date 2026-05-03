from .routes import knowledge_bp


def init_app(app):
    app.register_blueprint(knowledge_bp)


__all__ = ["knowledge_bp", "init_app"]
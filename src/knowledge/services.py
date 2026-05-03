from __future__ import annotations

from functools import lru_cache

from .models import ContentItem
from .repository import KnowledgeRepository


@lru_cache(maxsize=1)
def get_knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository()


def list_content_items() -> list[ContentItem]:
    return get_knowledge_repository().list_items()


def get_content_item(item_id: str) -> ContentItem | None:
    return get_knowledge_repository().get_item(item_id)


def create_content_item(
    *,
    title: str,
    body: str,
    category: str = "",
    visibility: str = "private",
    workspace_id: str | None = None,
    author_user_id: str | None = None,
) -> ContentItem:
    clean_title = (title or "").strip()
    clean_body = (body or "").strip()
    clean_category = (category or "").strip()

    if not clean_title:
        raise ValueError("Заголовок обязателен.")

    item = ContentItem(
        title=clean_title,
        body=clean_body,
        category=clean_category,
        visibility=visibility,
        workspace_id=workspace_id,
        author_user_id=author_user_id,
    )
    return get_knowledge_repository().add_item(item)
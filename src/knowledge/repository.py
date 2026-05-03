from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import ContentItem


class KnowledgeRepository:
    def __init__(self, storage_path: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self.storage_path = storage_path or base_dir / "data" / "knowledge_items.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def list_items(self) -> list[ContentItem]:
        data = self._load()
        return [ContentItem(**item) for item in data]

    def get_item(self, item_id: str) -> ContentItem | None:
        for item in self.list_items():
            if item.id == item_id:
                return item
        return None

    def add_item(self, item: ContentItem) -> ContentItem:
        items = self._load()
        items.append(asdict(item))
        self._save(items)
        return item

    def _load(self) -> list[dict]:
        if not self.storage_path.exists():
            return []

        try:
            raw = self.storage_path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            broken_path = self.storage_path.with_suffix(".broken.json")
            try:
                self.storage_path.replace(broken_path)
            except Exception:
                pass
            return []

    def _save(self, items: list[dict]) -> None:
        self.storage_path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
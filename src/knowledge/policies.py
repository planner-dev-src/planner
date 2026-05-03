from .models import ContentVisibility

class KnowledgePolicies:
    def ensure_can_create(self, actor_id, workspace_id, visibility):
        if visibility == ContentVisibility.SYSTEM:
            # здесь можно проверить глобальную роль пользователя (admin платформы)
            raise ValueError("Создание system-контента пока не поддержано")

        if visibility == ContentVisibility.WORKSPACE and not workspace_id:
            raise ValueError("workspace_id обязателен для workspace-контента")

        if visibility == ContentVisibility.PRIVATE and not actor_id:
            raise ValueError("Нельзя создать private-контент без пользователя")

        # здесь потом можно подтянуть Membership и проверить роль
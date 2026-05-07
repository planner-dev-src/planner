-- goals: цели верхнего уровня
CREATE TABLE IF NOT EXISTS goals (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    description       TEXT,
    owner_id          TEXT NOT NULL,
    visibility        TEXT NOT NULL DEFAULT 'private',   -- private / group / public
    moderation_status TEXT NOT NULL DEFAULT 'draft',     -- draft / pending / approved / rejected
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

-- programs: программы, связанные с целями
CREATE TABLE IF NOT EXISTS programs (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    note_html         TEXT,           -- пояснительная записка в HTML
    note_raw          TEXT,           -- исходный текст (по желанию)
    goal_id           TEXT,           -- ссылка на цель, если есть
    owner_id          TEXT NOT NULL,  -- автор
    visibility        TEXT NOT NULL DEFAULT 'private',
    moderation_status TEXT NOT NULL DEFAULT 'draft',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    FOREIGN KEY (goal_id) REFERENCES goals (id)
);

-- projects: проекты, связанные с программами
CREATE TABLE IF NOT EXISTS projects (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    description       TEXT,
    program_id        TEXT,           -- ссылка на программу
    owner_id          TEXT NOT NULL,
    visibility        TEXT NOT NULL DEFAULT 'private',
    moderation_status TEXT NOT NULL DEFAULT 'draft',
    status            TEXT NOT NULL DEFAULT 'planned',  -- planned / in_progress / completed / on_hold
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs (id)
);

-- program_attachments: приложения к программам
CREATE TABLE IF NOT EXISTS program_attachments (
    id           TEXT PRIMARY KEY,
    program_id   TEXT NOT NULL,
    kind         TEXT NOT NULL,      -- 'note' / 'appendix' и т.п.
    filename     TEXT NOT NULL,
    stored_path  TEXT NOT NULL,      -- путь в файловой системе / хранилище
    content_type TEXT,
    uploaded_by  TEXT NOT NULL,
    uploaded_at  TEXT NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs (id)
);

-- при необходимости можно добавить индексы:
CREATE INDEX IF NOT EXISTS idx_programs_goal_id ON programs (goal_id);
CREATE INDEX IF NOT EXISTS idx_programs_owner_visibility ON programs (owner_id, visibility);
CREATE INDEX IF NOT EXISTS idx_projects_program_id ON projects (program_id);
CREATE INDEX IF NOT EXISTS idx_projects_owner_visibility ON projects (owner_id, visibility);
CREATE INDEX IF NOT EXISTS idx_program_attachments_program_id ON program_attachments (program_id);
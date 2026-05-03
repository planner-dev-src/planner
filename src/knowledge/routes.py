from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template_string, request, url_for

from .services import create_content_item, list_content_items


knowledge_bp = Blueprint(
    "knowledge",
    __name__,
    url_prefix="/knowledge",
)


INDEX_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Knowledge</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 32px auto;
            padding: 0 16px;
            line-height: 1.5;
        }
        h1, h2 {
            margin-bottom: 12px;
        }
        form {
            margin-bottom: 32px;
            padding: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        input, textarea, select, button {
            width: 100%;
            margin-top: 6px;
            margin-bottom: 14px;
            padding: 8px;
            box-sizing: border-box;
        }
        button {
            width: auto;
            cursor: pointer;
        }
        .flash {
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        .flash.success {
            background: #e8f7e8;
            color: #1f6b1f;
        }
        .flash.error {
            background: #fdeaea;
            color: #9b1c1c;
        }
        .item {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 12px;
        }
        .meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }
        textarea {
            min-height: 120px;
        }
    </style>
</head>
<body>
    <h1>Knowledge</h1>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" action="{{ url_for('knowledge.add_item') }}">
        <h2>Новый материал</h2>

        <label for="title">Заголовок</label>
        <input id="title" name="title" required>

        <label for="category">Категория</label>
        <input id="category" name="category">

        <label for="visibility">Видимость</label>
        <select id="visibility" name="visibility">
            <option value="private">private</option>
            <option value="workspace">workspace</option>
        </select>

        <label for="body">Текст</label>
        <textarea id="body" name="body"></textarea>

        <button type="submit">Сохранить</button>
    </form>

    <h2>Материалы</h2>

    {% if items %}
        {% for item in items %}
            <div class="item">
                <h3>{{ item.title }}</h3>
                <div class="meta">
                    category={{ item.category or "-" }},
                    visibility={{ item.visibility }},
                    version={{ item.version }},
                    created_at={{ item.created_at }}
                </div>
                <div>{{ item.body or "—" }}</div>
            </div>
        {% endfor %}
    {% else %}
        <p>Пока материалов нет.</p>
    {% endif %}
</body>
</html>
"""


@knowledge_bp.route("/", methods=["GET"])
def index():
    items = list_content_items()
    return render_template_string(INDEX_TEMPLATE, items=items)


@knowledge_bp.route("/add", methods=["POST"])
def add_item():
    try:
        create_content_item(
            title=request.form.get("title", ""),
            body=request.form.get("body", ""),
            category=request.form.get("category", ""),
            visibility=request.form.get("visibility", "private"),
        )
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("knowledge.index"))
    except Exception:
        flash("Не удалось сохранить материал.", "error")
        return redirect(url_for("knowledge.index"))

    flash("Материал сохранён.", "success")
    return redirect(url_for("knowledge.index"))
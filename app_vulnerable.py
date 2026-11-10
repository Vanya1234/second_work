import sqlite3
from html import escape
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server


def find_students(name):
    database = sqlite3.connect(":memory:")
    try:
        database.execute("CREATE TABLE students (name TEXT, group_name TEXT)")
        database.executemany(
            "INSERT INTO students VALUES (?, ?)",
            [("alice", "DEMO-101"), ("bob", "DEMO-102"), ("carol", "DEMO-103")],
        )
        # Имя подставляется прямо в SQL-запрос.
        query = f"SELECT name, group_name FROM students WHERE name = '{name}'"
        return database.execute(query).fetchall()
    finally:
        database.close()


def respond(start_response, body, status="200 OK"):
    page = f"""<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><title>SQL Injection и XSS</title></head>
<body>
<h1>SQL Injection и XSS</h1>
{body}
<p><a href="/">На главную</a></p>
</body>
</html>"""
    data = page.encode("utf-8")
    start_response(status, [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(data))),
    ])
    return [data]


def application(environ, start_response):
    path = environ["PATH_INFO"]
    parameters = parse_qs(environ["QUERY_STRING"], keep_blank_values=True)
    if environ["REQUEST_METHOD"] != "GET":
        return respond(start_response, "<p>Используйте GET.</p>", "405 Method Not Allowed")

    if path == "/":
        return respond(start_response, """
<h2>Поиск студента</h2>
<p>Имена для поиска: alice, bob, carol.</p>
<form action="/search" method="get">
<label>Имя: <input name="name" value="alice"></label>
<button>Найти</button>
</form>
<h2>Приветствие</h2>
<form action="/hello" method="get">
<label>Текст: <input name="text" value="Мир"></label>
<button>Показать</button>
</form>""")

    if path == "/search":
        name = parameters.get("name", [""])[0]
        try:
            students = find_students(name)
        except sqlite3.Error:
            return respond(start_response, "<p>Ошибка SQL-запроса.</p>", "400 Bad Request")
        body = f"<p>Найдено записей: {len(students)}</p><ul>"
        for student_name, group_name in students:
            body += f"<li>{escape(student_name)} — {escape(group_name)}</li>"
        body += "</ul>"
        return respond(start_response, body)

    if path == "/hello":
        text = parameters.get("text", [""])[0]
        # Текст выводится без экранирования.
        body = f"<p>Привет, {text}!</p>"
        return respond(start_response, body)

    return respond(start_response, "<p>Страница не найдена.</p>", "404 Not Found")


if __name__ == "__main__":
    with make_server("127.0.0.1", 8000, application) as server:
        print("http://127.0.0.1:8000 (остановка: Ctrl+C)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")

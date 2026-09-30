import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="DevSecOps Learning API")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/ideas.db"))


class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("must not be null")
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class Idea(IdeaCreate):
    id: int


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT
            )
            """)


def idea_from_row(row: sqlite3.Row) -> Idea:
    return Idea(id=row["id"], title=row["title"], description=row["description"])


initialize_database()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/ideas", response_class=HTMLResponse)
def ideas_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="ideas.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/ideas", response_model=list[Idea])
def list_ideas() -> list[Idea]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, description FROM ideas ORDER BY id"
        ).fetchall()
    return [idea_from_row(row) for row in rows]


@app.post("/api/ideas", response_model=Idea, status_code=status.HTTP_201_CREATED)
def create_idea(payload: IdeaCreate) -> Idea:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO ideas (title, description) VALUES (?, ?)",
            (payload.title, payload.description),
        )
        row = connection.execute(
            "SELECT id, title, description FROM ideas WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return idea_from_row(row)


@app.get("/api/ideas/{idea_id}", response_model=Idea)
def get_idea(idea_id: int) -> Idea:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, description FROM ideas WHERE id = ?", (idea_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found"
        )
    return idea_from_row(row)


@app.put("/api/ideas/{idea_id}", response_model=Idea)
def update_idea(idea_id: int, payload: IdeaUpdate) -> Idea:
    changes = payload.model_dump(exclude_unset=True)
    with get_connection() as connection:
        current = connection.execute(
            "SELECT id, title, description FROM ideas WHERE id = ?", (idea_id,)
        ).fetchone()
        if current is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found"
            )

        if changes:
            assignments = ", ".join(f"{field} = ?" for field in changes)
            connection.execute(
                f"UPDATE ideas SET {assignments} WHERE id = ?",
                (*changes.values(), idea_id),
            )
        row = connection.execute(
            "SELECT id, title, description FROM ideas WHERE id = ?", (idea_id,)
        ).fetchone()
    return idea_from_row(row)


@app.delete("/api/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(idea_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found"
            )

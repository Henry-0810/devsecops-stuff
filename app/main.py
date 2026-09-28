from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="DevSecOps Learning API")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class Idea(IdeaCreate):
    id: int


_ideas: dict[int, Idea] = {}
_next_id = 1


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
    return list(_ideas.values())


@app.post("/api/ideas", response_model=Idea, status_code=status.HTTP_201_CREATED)
def create_idea(payload: IdeaCreate) -> Idea:
    global _next_id

    idea = Idea(id=_next_id, **payload.model_dump())
    _ideas[_next_id] = idea
    _next_id += 1
    return idea


@app.get("/api/ideas/{idea_id}", response_model=Idea)
def get_idea(idea_id: int) -> Idea:
    idea = _ideas.get(idea_id)
    if idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")
    return idea


@app.put("/api/ideas/{idea_id}", response_model=Idea)
def update_idea(idea_id: int, payload: IdeaUpdate) -> Idea:
    idea = _ideas.get(idea_id)
    if idea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")

    updated = idea.model_copy(update=payload.model_dump(exclude_unset=True))
    _ideas[idea_id] = updated
    return updated


@app.delete("/api/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(idea_id: int) -> None:
    if idea_id not in _ideas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")
    del _ideas[idea_id]

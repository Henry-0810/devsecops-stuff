# devsecops-stuff
To practice and test out tools, integration (SAST, AI, SCA, Dynamic Security testing, etc...)

## FastAPI sample app

### Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Endpoints

- `GET /` - basic landing page
- `GET /health` - health status
- `GET /ideas` - simple frontend page for CRUD demo
- `GET /api/ideas` - list ideas
- `POST /api/ideas` - create idea
- `GET /api/ideas/{idea_id}` - read one idea
- `PUT /api/ideas/{idea_id}` - update idea
- `DELETE /api/ideas/{idea_id}` - delete idea

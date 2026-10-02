# ANAND University Assistant — Part 1

## Scope
This part implements the **New Student** module using a traditional FAQ/rule-based approach.

Covered:
- Admission rules
- Data gathering / general admission guidance
- Required documents
- Fee structure
- University FAQs
- Class locations
- Course comparison
- Entrance exams
- Hostel rules and regulations

## Technologies
- Frontend: HTML, CSS, JavaScript
- Backend: Python + FastAPI

## Run Backend

Open a terminal:

```bash
cd backend
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Linux/macOS:
```bash
source venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Start server:

```bash
uvicorn main:app --reload
```

Backend:
http://127.0.0.1:8000

API documentation:
http://127.0.0.1:8000/docs

## Run Frontend

Open `frontend/index.html` in a browser.

For best results, use VS Code Live Server.

## Next Part
Part 2 can replace the rule-based responses with the AI/RAG architecture specified in the project document for existing students.

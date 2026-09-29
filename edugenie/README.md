# EduGenie – Google Gemini Powered Learning Assistant

EduGenie is a lightweight, responsive, AI-driven educational web assistant built for students, self-learners, and educators. It combines cloud-based reasoning via the **Google Gemini API** with local open-source transformer inference using **LaMini-Flan-T5** (via Hugging Face and PyTorch).

---

## 1. Project Title
**EduGenie – Google Gemini Powered Learning Assistant**

---

## 2. Project Description
EduGenie is designed to accelerate learning and retention across diverse academic subjects. Rather than generic open-ended generation, EduGenie uses tailored educational prompts to provide:
- Focused, pedagogically sound Q&A.
- Intuitive, three-part concept explanations with real-world analogies.
- Interactive multiple-choice quizzes with live scoring and explanations.
- Structured educational text summarization with comparative metrics.
- Multi-tier progressive learning roadmaps (Beginner, Intermediate, Advanced).

All user queries, generated content, quizzes, and learning paths are automatically persisted in a local SQLite relational database.

---

## 3. Features
1. **Educational Q&A (`POST /qa`)**:
   - Accepts academic questions (e.g., *"Which is the largest ocean and why is it important?"*).
   - Provides direct answers enriched with educational background and takeaways.
   - Dual model support (Google Gemini or local LaMini-Flan-T5).
2. **Concept Explanation (`POST /explain`)**:
   - Deconstructs complex topics into three clear components:
     1. *What It Means (Simple Language)*
     2. *Core Rule / Formula / Mechanism*
     3. *Real-World Example or Analogy*
3. **Interactive Quiz Generation (`POST /quiz`)**:
   - Generates 3, 5, or 8 multiple-choice questions with 4 distinct options (A, B, C, D).
   - Guarantees structured JSON formatting from the AI engine.
   - Stores each question as an individual record in the `QUIZ` table linked to the parent query.
   - Frontend allows answer selection, instant automated grading, percentage score, celebratory badges, and answer explanations.
4. **Text Summarization (`POST /summarize`)**:
   - Summarizes long articles, textbook passages, and lecture notes.
   - Shows a clean split-view comparing the generated summary against the original source.
   - Displays word count reductions and percentage compression.
5. **Personalized Learning Path (`POST /learn`)**:
   - Generates progressive roadmaps tailored to skill level (*Beginner*, *Intermediate*, or *Advanced*).
   - Includes milestone modules, practical mini-projects, and study best practices.

---

## 4. Technology Stack
- **Backend Framework**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Template Engine**: Jinja2
- **Database & ORM**: SQLite 3, SQLAlchemy 2.0
- **AI & ML**:
  - **Google Gemini API**: `google-genai` SDK (configurable model e.g. `gemini-2.5-flash`, `gemini-1.5-flash`)
  - **Local Model**: `MBZUAI/LaMini-Flan-T5-248M` via Hugging Face `transformers` and `torch` (PyTorch)
- **Frontend**: HTML5, Modern CSS (Responsive Grid/Flexbox, custom color scheme), Vanilla JavaScript (AJAX & live quiz grading)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`

---

## 5. Architecture
EduGenie follows a modular, layered architecture:

```
[ Web Browser / Client ]
         │ (HTTP GET/POST Forms & JSON)
         ▼
[ FastAPI Routing Layer ]  <───> [ Jinja2 Templates & CSS/JS ]
         │
    ┌────┴─────────────────────────────┐
    ▼                                  ▼
[ AI Service Layer ]          [ Database Layer (SQLAlchemy) ]
 ├── gemini_service.py         ├── database.py (SessionLocal)
 ├── laminiflant5_service.py   ├── models.py (User, Query, Response, Quiz...)
 └── prompts.py                └── schemas.py (Pydantic validation)
         │                                  │
    ┌────┴─────────────┐                    ▼
    ▼                  ▼             [ data/edugenie.db (SQLite) ]
(Google Gemini)  (LaMini-Flan-T5)
```

---

## 6. Folder Structure
```
edugenie/
├── app/
│   ├── main.py                     # FastAPI application entry & router registration
│   ├── routers/
│   │   ├── qa.py                   # Q&A route handlers
│   │   ├── explain.py              # Concept explainer route handlers
│   │   ├── quiz.py                 # Quiz generator & scoring handlers
│   │   ├── summarize.py            # Text summarization handlers
│   │   └── learn.py                # Learning path roadmap handlers
│   ├── services/
│   │   ├── gemini_service.py       # Google GenAI SDK integration & JSON parsing
│   │   └── laminiflant5_service.py # LaMini-Flan-T5 lazy singleton service
│   ├── database/
│   │   ├── database.py             # SQLite engine & session management
│   │   ├── models.py               # SQLAlchemy ORM relational models
│   │   └── schemas.py              # Pydantic request/response validation
│   ├── prompts/
│   │   └── prompts.py              # Centralized educational prompt engineering
│   ├── templates/
│   │   ├── base.html               # Shared layout, navbar, alert banner, footer
│   │   ├── index.html              # Main dashboard with feature cards & stats
│   │   ├── qa.html                 # Q&A interface
│   │   ├── explain.html            # Concept explanation interface
│   │   ├── quiz.html               # Interactive quiz & scoring interface
│   │   ├── summarize.html          # Summarization comparison interface
│   │   └── learn.html              # Learning path roadmap interface
│   └── static/
│       ├── css/
│       │   └── style.css           # Modern responsive design
│       └── js/
│           └── app.js              # Loading indicators & form helpers
├── data/
│   └── edugenie.db                 # Auto-generated SQLite database
├── tests/
│   ├── __init__.py
│   └── test_app.py                 # Pytest test suite (17 comprehensive tests)
├── .env.example                    # Template for environment variables
├── .gitignore                      # Git ignore rules (protects .env and database)
├── requirements.txt                # Application dependencies
├── README.md                       # Complete documentation
└── run.py                          # Startup script: python run.py
```

---

## 7. Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### Step-by-Step Setup
1. Clone or navigate to the project directory:
   ```bash
   cd edugenie
   ```
2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## 8. Environment Variable Setup
1. Copy `.env.example` to create your `.env` file:
   ```bash
   cp .env.example .env
   # On Windows PowerShell:
   copy .env.example .env
   ```
2. Open `.env` in a text editor and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   LAMINI_MODEL=MBZUAI/LaMini-Flan-T5-248M
   ```
> **Security Note:** `.env` is listed in `.gitignore` and must never be committed to public version control.

---

## 9. How to Run
Start the application using either of the following commands:

**Option A (Using run.py):**
```bash
python run.py
```

**Option B (Using Uvicorn directly):**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 10. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Main dashboard with overview, statistics, and tool cards |
| `GET`  | `/health` | Healthcheck and model readiness status |
| `GET`  | `/qa` | Render Q&A form and recent history |
| `POST` | `/qa` | Submit educational question (JSON or Form) |
| `GET`  | `/explain` | Render concept explanation form |
| `POST` | `/explain` | Submit concept to break down (JSON or Form) |
| `GET`  | `/quiz` | Render interactive quiz builder |
| `POST` | `/quiz` | Generate MCQs with options and correct answers |
| `GET`  | `/summarize` | Render text summarizer |
| `POST` | `/summarize` | Generate concise summary and key takeaways |
| `GET`  | `/learn` | Render learning path creator |
| `POST` | `/learn` | Generate multi-level progressive curriculum |

All `POST` endpoints accept both standard HTML `application/x-www-form-urlencoded` submissions and dynamic `application/json` AJAX payloads.

---

## 11. Database Schema
EduGenie uses a relational SQLite database (`data/edugenie.db`) managed through SQLAlchemy ORM.

### Tables & Relationships
1. **`USER`**:
   - `UserID` (INTEGER PK, Auto-increment)
   - `UserName` (VARCHAR 100)
   - `Email` (VARCHAR 255, Unique)
   - `PasswordHash` (VARCHAR 255)
   - `CreatedAt` (DATETIME)
2. **`USER_QUERY`**:
   - `QueryID` (INTEGER PK, Auto-increment)
   - `UserID` (INTEGER FK -> `USER.UserID`)
   - `QueryType` (VARCHAR 50) — `'qa'`, `'explain'`, `'quiz'`, `'summarize'`, `'learn'`
   - `QueryText` (TEXT)
   - `CreatedAt` (DATETIME)
3. **`AI_RESPONSE`**:
   - `ResponseID` (INTEGER PK, Auto-increment)
   - `QueryID` (INTEGER FK -> `USER_QUERY.QueryID`)
   - `ResponseText` (TEXT)
   - `ModelUsed` (VARCHAR 100)
   - `CreatedAt` (DATETIME)
4. **`QUIZ`**:
   - `QuizID` (INTEGER PK, Auto-increment)
   - `QueryID` (INTEGER FK -> `USER_QUERY.QueryID`)
   - `QuestionText` (TEXT)
   - `OptionA` (VARCHAR 255), `OptionB` (VARCHAR 255), `OptionC` (VARCHAR 255), `OptionD` (VARCHAR 255)
   - `CorrectOption` (VARCHAR 10) — `'A'`, `'B'`, `'C'`, or `'D'`
   - `CreatedAt` (DATETIME)
5. **`SUMMARY`**:
   - `SummaryID` (INTEGER PK, Auto-increment)
   - `QueryID` (INTEGER FK -> `USER_QUERY.QueryID`)
   - `OriginalText` (TEXT)
   - `SummaryText` (TEXT)
   - `ModelUsed` (VARCHAR 100)
   - `CreatedAt` (DATETIME)
6. **`LEARNING_PATH`**:
   - `PathID` (INTEGER PK, Auto-increment)
   - `QueryID` (INTEGER FK -> `USER_QUERY.QueryID`)
   - `Topic` (VARCHAR 200)
   - `Level` (VARCHAR 50) — `'Beginner'`, `'Intermediate'`, `'Advanced'`
   - `RecommendedTopics` (TEXT)
   - `CreatedAt` (DATETIME)

---

## 12. AI Models

### 1. Google Gemini
- Cloud-based, large-context reasoning.
- Configured via the official `google-genai` SDK.
- Used for high-fidelity Q&A, deep explanations, JSON-structured quiz creation, and roadmaps.
- Includes automatic fallback if a particular model alias is unsupported.

### 2. LaMini-Flan-T5
- Local small language model (`MBZUAI/LaMini-Flan-T5-248M`).
- Integrated via Hugging Face `transformers` and `torch`.
- Lazy-loaded as a singleton on first request to prevent repeated weights downloading.
- Automatically handles Windows OpenMP runtime library configurations (`KMP_DUPLICATE_LIB_OK=TRUE`).
- Gracefully degrades to Gemini if local RAM or hardware limits prevent loading, ensuring the app never crashes.

---

## 13. Testing
Automated tests are located in `tests/test_app.py` and run offline without calling paid APIs:

```bash
pytest -v
```

### Coverage:
- Home dashboard rendering (`GET /`)
- Health check endpoint (`GET /health`)
- Q&A page and JSON submission (`POST /qa`)
- Concept explanation page and JSON submission (`POST /explain`)
- Quiz generation and multiple-choice question storage in `QUIZ` table (`POST /quiz`)
- Text summarization and storage in `SUMMARY` table (`POST /summarize`)
- Learning path generation and storage in `LEARNING_PATH` table (`POST /learn`)
- Input validation (empty questions, empty topics, short text)
- Database persistence and foreign key associations

All 17 tests pass with 0 errors.

---

## 14. GitHub Usage
When pushing this repository to GitHub:
1. Initialize Git and stage files:
   ```bash
   git init
   git add .
   ```
2. Verify that `.env` and `data/edugenie.db` are ignored:
   ```bash
   git status
   ```
3. Commit and push:
   ```bash
   git commit -m "feat: complete EduGenie educational assistant project"
   git remote add origin https://github.com/YOUR_USERNAME/edugenie.git
   git branch -M main
   git push -u origin main
   ```

---

## 15. Limitations & Future Scope
- **Rate Limits**: Free tier Google Gemini API keys are subject to per-minute quota limits.
- **Local Model Footprint**: Running `LaMini-Flan-T5-248M` locally requires ~1GB of RAM and downloads model weights on its first invocation.
- **Authentication**: A guest student user session is pre-seeded for frictionless local evaluation; JWT-based user login can be expanded as a future module.

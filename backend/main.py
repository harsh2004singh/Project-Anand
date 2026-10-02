"""ANAND - GBU Assistant backend.

This file keeps the original API contracts and business logic intact while
making the code easier to read and maintain for future updates.
"""

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ANAND - GBU Assistant")
kb = None

# Wildcard origin cannot be combined with credentials; lock origins down in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



NOTICE = "Please check the official GBU notice once to be sure."

# ---------------------------------------------------------------------------
# Human touch: short, simple, friendly
# ---------------------------------------------------------------------------
OPENERS = ["Sure!", "Of course!", "Happy to help!", "Good question!", "No problem!", ""]


def human(text: str) -> str:
    """Add a small friendly opener so replies don't all sound the same."""
    return f"{random.choice(OPENERS)} {text}".strip()


SMALL_TALK = [
    (["thanks", "thank you", "thankyou", "thx"],
     ["You're welcome! 😊 Ask me anything else you like.",
      "Glad I could help! Is there anything else you want to know?"]),
    (["bye", "goodbye", "see you", "good night"],
     ["Bye! All the best with your admission. 😊", "Take care! Come back anytime you have a question."]),
    (["how are you", "how are you doing", "how r u"],
     ["I'm doing great, thank you! 😊 How can I help you today?"]),
    (["who are you", "what are you", "your name"],
     ["I'm ANAND, the GBU assistant for new students. I can help with admission, documents, fees, "
      "courses, entrance exams, classes and hostel. What would you like to know?"]),
    (["hi", "hii", "hello", "hey", "namaste", "good morning", "good afternoon", "good evening"],
     ["Hi there! 😊 I'm ANAND. What would you like to know about GBU?",
      "Hello! Welcome to GBU. How can I help you today?"]),
]

# ---------------------------------------------------------------------------
# Topic answers (admins should replace with verified, current university text)
# ---------------------------------------------------------------------------
FAQS = {
    "admission": {
        "title": "Admission Rules",
        "answer": (
            "Admission rules depend on the course you choose. "
            "Mainly, check these things:\n"
            "• Are you eligible for the course?\n"
            "• What is the last date to apply?\n"
            "• Is there an entrance exam or counselling?\n\n"
            "Which course are you planning to apply for?"
        ),
    },
    "guidance": {
        "title": "Admission Guidance",
        "answer": (
            "Don't worry, it's easy if you go step by step. 😊\n"
            "1. Pick your course.\n"
            "2. Check if you are eligible.\n"
            "3. Find out if there is an entrance exam.\n"
            "4. Fill in the online form.\n"
            "5. Upload your documents.\n"
            "6. Pay the fee.\n"
            "7. Attend counselling and document check.\n\n"
            "Want a checklist made just for you? Tell me your last qualification, "
            "your percentage and the course you like."
        ),
    },
    "documents": {
        "title": "Required Documents",
        "answer": (
            "These documents are usually needed:\n"
            "• Class 10 and 12 marksheets\n"
            "• Graduation marksheets (for PG courses)\n"
            "• ID proof (like Aadhaar)\n"
            "• Passport-size photos\n"
            "• Category certificate (if it applies to you)\n"
            "• Migration/transfer certificate (if needed)\n\n"
            "Keep scanned copies and originals ready. The list can change by course, "
            "so check the latest notice."
        ),
    },
    "fees": {
        "title": "Fee Structure",
        "answer": (
            "The fee depends on the course and your category. "
            "It can include tuition, exam and hostel fees.\n\n"
            "For the exact amount, please see the latest official fee notice. "
            "Tell me your course and I'll tell you what to look for."
        ),
    },
    "faq": {
        "title": "University FAQs",
        "answer": (
            "I'm ANAND, and I'm here to make your admission easier. 😊\n"
            "You can ask me about:\n"
            "• Admission rules\n"
            "• Documents\n"
            "• Fees\n"
            "• Entrance exams\n"
            "• Comparing courses\n"
            "• Class locations\n"
            "• Hostel rules\n\n"
            "Just type your question in your own words."
        ),
    },
    "class": {
        "title": "Class Locations",
        "answer": (
            "Your classroom depends on your course, semester and the timetable. "
            "The best place to check is your department's latest timetable or notice board.\n\n"
            "Which department and semester are you in?"
        ),
    },
    "course": {
        "title": "Course Comparison",
        "answer": (
            "Sure, I can compare two courses for you. "
            "I'll tell you about duration, eligibility, what you study and career options.\n\n"
            "Just name the two courses, for example: 'Compare B.Tech and BCA'."
        ),
    },
    "entrance": {
        "title": "Entrance Exams",
        "answer": (
            "Whether you need an entrance exam depends on the course. "
            "Some courses ask for one, others use different selection rules.\n\n"
            "Tell me the course you want, and check the latest admission notice for the exact exam."
        ),
    },
    "hostel": {
        "title": "Hostel Rules and Regulations",
        "answer": (
            "Thinking of staying in the hostel? Here is what to check:\n"
            "• How to get a hostel room\n"
            "• Hostel fees\n"
            "• Entry and exit timings\n"
            "• Discipline and attendance rules\n"
            "• Visitor rules\n\n"
            "The official hostel rules from the university are final. "
            "Is there something specific you want to know?"
        ),
    },
}

# Phrase keywords. Multi-word phrases score higher; ties resolved by dict order.
KEYWORDS = {
    "class": ["classroom", "class room", "class location", "where is my class", "lecture hall",
              "building", "block", "department location", "class"],
    "hostel": ["hostel", "hostel rules", "warden", "accommodation", "mess", "curfew", "hostel room"],
    "entrance": ["entrance", "entrance exam", "entrance test", "cuet", "jee", "gate", "cutoff", "cut off"],
    "course": ["compare", "comparison", "versus", "vs", "course", "courses", "programme", "program",
               "curriculum", "career scope", "duration"],
    "documents": ["document", "documents", "certificate", "marksheet", "id proof", "photograph", "checklist"],
    "fees": ["fee", "fees", "fee structure", "payment", "cost", "charges", "tuition", "scholarship"],
    "admission": ["admission", "admissions", "apply", "eligibility", "application", "counselling",
                  "counseling", "last date", "deadline"],
    "guidance": ["guidance", "guide me", "suggest", "which course should", "my profile", "where do i start",
                 "how to start", "steps", "process"],
    "faq": ["faq", "faqs", "question", "help", "what can you do"],
}

SUGGESTIONS = ["Admission rules", "Required documents", "Fee structure", "Entrance exams",
               "Compare courses", "Class locations", "Hostel rules", "Admission guidance"]

# ---------------------------------------------------------------------------
# Course data for comparison (typical durations; edit to match GBU's actual programmes)
# ---------------------------------------------------------------------------
COURSES = {
    "btech": {"name": "B.Tech", "level": "UG", "duration": "4 years",
              "eligibility": "10+2 with Physics, Maths and one more science subject (check notice)",
              "focus": "Engineering basics, labs, projects, internships",
              "careers": "Engineer, developer, analyst, or higher studies (M.Tech/MBA)"},
    "bba": {"name": "BBA", "level": "UG", "duration": "3 years",
            "eligibility": "10+2 in any stream (check notice)",
            "focus": "Management basics, marketing, finance, HR",
            "careers": "Management trainee, marketing/finance roles, or MBA"},
    "bca": {"name": "BCA", "level": "UG", "duration": "3 years",
            "eligibility": "10+2, usually with Maths/Computer subject (check notice)",
            "focus": "Programming, databases, web and software development",
            "careers": "Developer, tester, IT support, or MCA"},
    "mba": {"name": "MBA", "level": "PG", "duration": "2 years",
            "eligibility": "Bachelor's degree with minimum marks; entrance score may be needed",
            "focus": "Leadership, strategy, and a specialisation like finance, marketing or HR",
            "careers": "Manager, consultant, business analyst, entrepreneur"},
    "mca": {"name": "MCA", "level": "PG", "duration": "2 years",
            "eligibility": "Bachelor's degree with Maths/relevant background (check notice)",
            "focus": "Advanced computing, software engineering, data and cloud",
            "careers": "Software engineer, architect, data roles"},
    "mtech": {"name": "M.Tech", "level": "PG", "duration": "2 years",
              "eligibility": "B.Tech/B.E. in a related branch; GATE may be relevant",
              "focus": "Specialised engineering, research, thesis",
              "careers": "Specialist engineer, researcher, PhD, teaching"},
}
COURSE_ALIASES = {
    "btech": ["btech", "b tech", "be", "engineering"], "bba": ["bba"], "bca": ["bca"],
    "mba": ["mba"], "mca": ["mca"], "mtech": ["mtech", "m tech"],
}

# Class locations: fill with real data from the university timetable / admin panel.
CLASS_LOCATIONS = {
    # "btech": "School of Engineering - Block/Room ...",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Convert user input into a consistent lower-case, plain-text format."""
    cleaned_text = text.lower().replace(".", "")
    return re.sub(r"[^a-z0-9\s]", " ", cleaned_text)


def has_phrase(text: str, phrase: str) -> bool:
    """Check whether a phrase appears as a full word/term in the cleaned text."""
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def detect_topic(message: str) -> Optional[str]:
    """Detect the most relevant FAQ topic from the message."""
    normalized_text = normalize(message)
    best_topic, best_score = None, 0

    for topic_id, phrases in KEYWORDS.items():
        score = sum(
            len(phrase.split())
            for phrase in phrases
            if has_phrase(normalized_text, normalize(phrase).strip())
        )
        if score > best_score:
            best_topic, best_score = topic_id, score

    return best_topic


def small_talk(message: str) -> Optional[str]:
    """Handle greeting and polite short chat before actual FAQ handling."""
    normalized_text = normalize(message)

    for phrases, replies in SMALL_TALK:
        if any(has_phrase(normalized_text, phrase) for phrase in phrases):
            return random.choice(replies)
    return None


def find_courses(message: str) -> list[str]:
    """Find course names mentioned in a user message."""
    normalized_text = normalize(message)
    return [
        course_id
        for course_id, aliases in COURSE_ALIASES.items()
        if any(has_phrase(normalized_text, alias) for alias in aliases)
    ]


def compare_courses(a: str, b: str) -> dict:
    ca, cb = COURSES[a], COURSES[b]
    parts = [f"Here is a simple comparison of {ca['name']} and {cb['name']} 😊"]
    for label, key in [("Duration", "duration"), ("Who can apply", "eligibility"),
                       ("What you study", "focus"), ("Career options", "careers")]:
        parts.append(f"\n{label}\n• {ca['name']}: {ca[key]}\n• {cb['name']}: {cb[key]}")
    parts.append(f"\nWant me to explain either one in more detail? {NOTICE}")
    return {"reply": "\n".join(parts), "topic": "course", "data": {a: ca, b: cb}}


def course_summary(cid: str) -> dict:
    c = COURSES[cid]
    reply = (f"{c['name']} is a {c['level']} course and takes {c['duration']}.\n"
             f"• Who can apply: {c['eligibility']}\n"
             f"• What you study: {c['focus']}\n"
             f"• Career options: {c['careers']}\n\n"
             f"Want to compare it with another course? Just tell me which one. {NOTICE}")
    return {"reply": reply, "topic": "course", "data": c}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


class StudentProfile(BaseModel):
    name: str
    qualification: str                 # "12th" or "graduation"
    percentage: Optional[float] = None
    category: Optional[str] = None     # General / OBC / SC / ST / EWS etc.
    programme_interest: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    needs_hostel: bool = False
    consent: bool = False              # permission to store details for follow-up


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """Simple health/info endpoint for the backend service."""
    return {"project": "ANAND", "part": 1, "module": "New Student Assistant"}


@app.get("/topics")
def topics():
    """List all supported FAQ topics and titles."""
    return [{"id": k, "title": v["title"]} for k, v in FAQS.items()]


@app.get("/topic/{topic_id}")
def topic(topic_id: str):
    """Return the answer text for a specific FAQ topic."""
    return FAQS.get(topic_id, {"title": "Not Found", "answer": "Topic not found."})


@app.get("/courses")
def courses():
    """List all supported courses with their ids and levels."""
    return [{"id": k, "name": v["name"], "level": v["level"]} for k, v in COURSES.items()]


@app.get("/compare")
def compare(a: str, b: str):
    if a not in COURSES or b not in COURSES:
        return {"reply": f"Sorry, I don't know that course. I can compare: {', '.join(COURSES)}"}
    return compare_courses(a, b)


@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        return {"reply": "Oops, your message looks empty. What would you like to ask? 😊",
                "topic": None, "suggestions": SUGGESTIONS}

    topic_id = detect_topic(message)
    mentioned = find_courses(message)

    # Greetings and small talk (only if the message has no real question in it)
    if topic_id is None and not mentioned:
        talk = small_talk(message)
        if talk:
            return {"reply": talk, "topic": None, "suggestions": SUGGESTIONS}

    # Course comparison / details
    if topic_id == "course" or (mentioned and topic_id in (None, "course")):
        if len(mentioned) >= 2:
            return {**compare_courses(mentioned[0], mentioned[1]), "suggestions": SUGGESTIONS}
        if len(mentioned) == 1:
            return {**course_summary(mentioned[0]), "suggestions": SUGGESTIONS}

    # Class locations: use stored data if a course is mentioned
    if topic_id == "class" and mentioned and mentioned[0] in CLASS_LOCATIONS:
        return {"reply": CLASS_LOCATIONS[mentioned[0]], "topic": "class", "suggestions": SUGGESTIONS}

    # Answer from the university PDFs when a good match exists
    if kb:
        pdf_hit = kb.answer(message)
        if pdf_hit:
            return {"reply": "I found this in the university document:\n\n" + pdf_hit["reply"],
                    "topic": topic_id, "from_pdf": True, "sources": pdf_hit["sources"],
                    "suggestions": SUGGESTIONS}

    if topic_id:
        return {"reply": human(FAQS[topic_id]["answer"]), "topic": topic_id, "suggestions": SUGGESTIONS}

    return {
        "reply": ("Sorry, I didn't quite get that. 😊 I can help with admission, documents, fees, "
                  "entrance exams, courses, class locations and hostel rules.\n\n"
                  "Try asking like this: \"What documents do I need?\" or \"Compare B.Tech and BBA\"."),
        "topic": None,
        "suggestions": SUGGESTIONS,
    }


LEADS_FILE = Path("leads.jsonl")


@app.post("/guidance")
def guidance(profile: StudentProfile):
    """Collect basic details and return a personal admission checklist."""
    qualification_text = profile.qualification.lower()
    is_postgraduate = any(
        keyword in qualification_text
        for keyword in ["graduat", "bachelor", "degree", "b.tech", "bba", "bca"]
    )
    level = "PG" if is_postgraduate else "UG"
    available_courses = [course["name"] for course in COURSES.values() if course["level"] == level]

    category_note = ""
    if profile.category and profile.category.lower() != "general":
        category_note = ", category certificate"

    steps = [
        f"Courses you can look at: {', '.join(available_courses)}.",
        "Read the official admission notice for eligibility, dates and seats.",
        "Check if your course needs an entrance exam.",
        "Register online and fill in the application form.",
        "Keep your documents ready: marksheets, ID proof, photos"
        + category_note
        + ", and migration/transfer certificate if needed.",
        "Pay the fee as per the latest fee notice.",
        "Attend counselling and document check when you are called.",
    ]

    if profile.needs_hostel:
        steps.append("Apply for the hostel separately and read the hostel rules.")

    saved = False
    if profile.consent:
        record = {**profile.model_dump(), "time": datetime.now(timezone.utc).isoformat()}
        with LEADS_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")
        saved = True

    return {
        "greeting": f"Hi {profile.name}! 😊 Here is your admission checklist.",
        "checklist": steps,
        "details_saved": saved,
        "note": NOTICE,
    }

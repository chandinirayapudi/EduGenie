"""EduGenie - Educational Prompt Engineering Module.

Contains carefully designed, reusable prompts for all five core features:
1. Q&A
2. Concept Explanation
3. Quiz Generation (Structured JSON output)
4. Text Summarization
5. Personalized Learning Path (Structured sections)
"""

SYSTEM_ROLE_PROMPT = """You are EduGenie, an expert, encouraging, and clear AI educational assistant.
Your goal is to help students, self-learners, and educators master topics effectively.
Always use accurate, engaging, and age-appropriate explanations.
Keep your language clear, organized, and avoid overwhelming technical jargon unless explained."""


def get_qa_prompt(question: str) -> str:
    """Prompt for answering educational questions with student context."""
    return f"""{SYSTEM_ROLE_PROMPT}

You are answering a student's question. Follow these strict guidelines:
1. Provide a direct, accurate, and concise answer to the question first.
2. Give helpful educational context, background, or a key takeaway to enrich their understanding.
3. Keep the tone encouraging, structured with bullet points or short paragraphs where appropriate.
4. Keep the answer concise and easy for a student to understand (avoid excessively long essays).

Student Question:
"{question}"

Your Educational Answer:"""


def get_explain_prompt(concept: str) -> str:
    """Prompt for breaking down difficult concepts simply."""
    return f"""{SYSTEM_ROLE_PROMPT}

Explain the concept "{concept}" in a clear, pedagogical way suitable for a student.
Structure your explanation into these exact 3 sections:

### 1. What It Means (Simple Explanation)
Explain what the concept is in plain, simple language that anyone can understand.

### 2. Core Rule, Formula, or Key Mechanism
If mathematical/scientific, state the formula and define variables. If conceptual/humanities, explain the fundamental rule, principle, or mechanism behind it.

### 3. Real-World Example or Intuitive Analogy
Give a vivid, relatable real-world example or story showing how this concept applies in daily life.

Concept to explain: "{concept}"
"""


def get_quiz_prompt(topic: str, num_questions: int = 5) -> str:
    """Prompt requesting strictly valid JSON formatted multiple-choice questions."""
    return f"""{SYSTEM_ROLE_PROMPT}

You are creating an interactive educational quiz on the topic: "{topic}".
Generate exactly {num_questions} multiple-choice questions.

CRITICAL: Return ONLY a valid JSON array of objects. Do not include markdown formatting or backticks around the JSON if possible, but if you do, wrap it in ```json ... ```.
Each JSON object must have EXACTLY these fields:
- "question": string (the question text)
- "option_a": string (first answer choice)
- "option_b": string (second answer choice)
- "option_c": string (third answer choice)
- "option_d": string (fourth answer choice)
- "correct_option": string (must be exactly "A", "B", "C", or "D")
- "explanation": string (brief 1-2 sentence explanation of why this answer is correct)

Example output format:
[
  {{
    "question": "What is the primary function of mitochondria in a cell?",
    "option_a": "Produce cellular energy (ATP)",
    "option_b": "Synthesize proteins",
    "option_c": "Store genetic code",
    "option_d": "Break down waste",
    "correct_option": "A",
    "explanation": "Mitochondria are known as the powerhouse of the cell because they generate most of the chemical energy needed."
  }}
]

Generate the JSON quiz for topic: "{topic}":"""


def get_summarize_prompt(text: str) -> str:
    """Prompt for educational text summarization preserving key takeaways."""
    return f"""{SYSTEM_ROLE_PROMPT}

Summarize the following educational text for a student.
Guidelines:
1. Provide a concise overview of the core message (1 paragraph).
2. Extract 3 to 5 key bullet points highlighting essential facts, definitions, or insights.
3. Provide a one-sentence "Student Takeaway / Summary in a Nutshell".
4. Maintain accuracy and do not omit crucial information.

Text to summarize:
\"\"\"
{text}
\"\"\"

Summary:"""


def get_learning_path_prompt(topic: str, level: str) -> str:
    """Prompt for generating a progressive structured curriculum and study recommendations."""
    return f"""{SYSTEM_ROLE_PROMPT}

Create a personalized, progressive learning path and study plan for a student who wants to master "{topic}" at the "{level}" level.

Format your response with the following structured sections:

## 🎯 Target Goal & Prerequisites
Brief overview of what the learner will achieve at the {level} level and any recommended prerequisites.

## 🗺️ Step-by-Step Curriculum
Provide an ordered sequence of 4-6 core learning milestones/modules. For each module, include:
- **Module Name**
- Key concepts to study
- Practical mini-exercise or project idea

## 💡 Smart Study Recommendations & Best Practices
- 3-4 actionable tips on how to practice, retain knowledge, and avoid common beginner/intermediate pitfalls for "{topic}".
- Recommended types of projects or practice resources.

Topic: "{topic}"
Skill Level: "{level}"
"""

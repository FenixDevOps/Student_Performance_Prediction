"""
recommendations.py
------------------
Analyses a student's input features, identifies strengths and weaknesses,
and generates up to 10 personalised improvement recommendations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple


# ── Benchmark thresholds (what counts as "good") ──────────────────────────────
BENCHMARKS = {
    "attendance":            {"good": 80,  "unit": "%",     "label": "Attendance"},
    "previous_gpa":          {"good": 7.0, "unit": "/10.0",  "label": "Previous GPA"},
    "study_hours":           {"good": 20,  "unit": "hrs/wk","label": "Study Hours"},
    "assignment_completion": {"good": 80,  "unit": "%",     "label": "Assignment Completion"},
    "participation_score":   {"good": 7,   "unit": "/10",   "label": "Class Participation"},
    "sleep_hours":           {"good": (6.5, 9.0), "unit": "hrs/day", "label": "Sleep Hours"},
    "practice_test_score":   {"good": 70,  "unit": "/100",  "label": "Practice Test Score"},
    "practice_problems":     {"good": 80,  "unit": "completed", "label": "Practice Problems"},
}

# ── Recommendation catalogue ──────────────────────────────────────────────────
_RECS: dict[str, list[str]] = {
    "attendance": [
        "🎯 Target ≥85 % attendance — each class builds on the last.",
        "📅 Set calendar reminders for every lecture so you never miss one accidentally.",
        "🤝 Partner with a classmate to keep each other accountable for showing up.",
    ],
    "study_hours": [
        "📚 Aim for at least 20 study hours per week — spread across short daily sessions.",
        "⏱️ Try the Pomodoro technique: 25 min focused study → 5 min break.",
        "📆 Block study slots in your calendar the way you would a class.",
    ],
    "assignment_completion": [
        "✅ Complete every assignment on time — consistency compounds over a semester.",
        "📝 Break large assignments into smaller tasks with personal mini-deadlines.",
        "🗂️ Use a to-do app (Todoist, Notion) to track submission deadlines.",
    ],
    "participation_score": [
        "🙋 Raise your hand at least once per class — active recall strengthens memory.",
        "💬 Join or start a study group to practise explaining concepts out loud.",
        "❓ Prepare one question before each lecture to stay engaged.",
    ],
    "sleep_hours": [
        "😴 Sleep 7–9 hours nightly — memory consolidation happens during deep sleep.",
        "📵 Stop screen use 30 min before bed to improve sleep quality.",
        "🌙 Keep a consistent sleep/wake schedule even on weekends.",
    ],
    "practice_test_score": [
        "📋 Take at least one practice test per topic before the actual exam.",
        "🔁 Review every wrong answer: understand *why* it was wrong, not just the correct answer.",
        "📖 Use spaced repetition (Anki, Quizlet) to lock in difficult concepts.",
    ],
    "practice_problems": [
        "🧮 Complete 80+ practice problems per subject each week.",
        "🎯 Focus on problem types you find hardest — don't just practise what you already know.",
        "📊 Track your accuracy per topic to spot hidden weak areas.",
    ],
    "previous_gpa": [
        "📈 Review foundational topics from previous courses that still appear in your syllabus.",
        "🧑‍🏫 Visit your professor's office hours to address any persisting knowledge gaps.",
        "📑 Re-read your previous semester notes before each related new lecture.",
    ],
    "general": [
        "🍎 Exercise for 30 min daily — physical activity boosts cognitive performance.",
        "🧘 Practise 10 min of mindfulness or meditation to reduce exam anxiety.",
        "📓 Keep a weekly study journal to reflect on what worked and what didn't.",
    ],
}


@dataclass
class PerformanceAnalysis:
    """Full breakdown of a student's academic performance."""
    strengths:       List[str] = field(default_factory=list)
    weaknesses:      List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary:         str       = ""


def _is_weak(key: str, value: float) -> bool:
    """Return True if the feature value is below the 'good' benchmark."""
    bench = BENCHMARKS[key]["good"]
    if key == "sleep_hours":
        lo, hi = bench
        return not (lo <= value <= hi)
    return value < bench


def analyse(features: dict, predicted_score: float) -> PerformanceAnalysis:
    """
    Analyse a student's features and return strengths, weaknesses, and
    personalised recommendations.

    Parameters
    ----------
    features : dict
        Student input features (same keys as BENCHMARKS).
    predicted_score : float
        The model's predicted exam score.

    Returns
    -------
    PerformanceAnalysis
    """
    strengths:  list[str] = []
    weaknesses: list[str] = []
    rec_pool:   list[str] = []

    for key, bench_info in BENCHMARKS.items():
        value = features.get(key)
        if value is None:
            continue
        label = bench_info["label"]
        unit  = bench_info["unit"]

        if _is_weak(key, value):
            weaknesses.append(f"{label}: {value} {unit}")
            rec_pool.extend(_RECS.get(key, []))
        else:
            strengths.append(f"{label}: {value} {unit}")

    # Always add 1–2 general tips
    rec_pool.extend(_RECS["general"])

    # De-duplicate, keep at most 10 recommendations
    seen: set[str] = set()
    unique_recs: list[str] = []
    for rec in rec_pool:
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)
        if len(unique_recs) == 10:
            break

    # Build summary sentence
    if predicted_score >= 85:
        summary = "You're performing at an excellent level! Keep up the great work and maintain your habits."
    elif predicted_score >= 70:
        summary = "You're doing well overall. A few targeted improvements can push you into the excellent range."
    elif predicted_score >= 50:
        summary = "You're at an average level. Addressing your weak areas now will make a significant difference."
    else:
        summary = "Your performance is at risk. Focus on the highest-priority recommendations below immediately."

    return PerformanceAnalysis(
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=unique_recs,
        summary=summary,
    )


# ── Standalone smoke test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_features = {
        "attendance":            60.0,
        "previous_gpa":          2.5,
        "study_hours":           10.0,
        "assignment_completion": 55.0,
        "participation_score":   4.0,
        "sleep_hours":           5.5,
        "practice_test_score":   45.0,
        "practice_problems":     30,
    }
    analysis = analyse(sample_features, predicted_score=48.0)
    print("\n=== Strengths ===")
    for s in analysis.strengths:
        print(f"  ✅ {s}")
    print("\n=== Needs Improvement ===")
    for w in analysis.weaknesses:
        print(f"  ⚠️  {w}")
    print("\n=== Recommendations ===")
    for i, r in enumerate(analysis.recommendations, 1):
        print(f"  {i}. {r}")
    print(f"\nSummary: {analysis.summary}")
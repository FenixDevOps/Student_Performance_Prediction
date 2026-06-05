from typing import List, Dict, Any

# Benchmarks for student attributes
BENCHMARKS = {
    "attendance": {"good": 80.0, "unit": "%", "label": "Attendance"},
    "previous_gpa": {"good": 7.0, "unit": "/10.0", "label": "Previous GPA"},
    "study_hours": {"good": 20.0, "unit": "hrs/wk", "label": "Study Hours"},
    "assignment_completion": {"good": 80.0, "unit": "%", "label": "Assignment Completion"},
    "participation_score": {"good": 7.0, "unit": "/10.0", "label": "Class Participation"},
    "sleep_hours": {"good": (6.5, 9.0), "unit": "hrs/day", "label": "Sleep Hours"},
    "practice_test_score": {"good": 70.0, "unit": "/100", "label": "Practice Test Score"},
    "practice_problems": {"good": 80.0, "unit": "solved", "label": "Practice Problems"},
}

RECOMMENDATION_CATALOG = {
    "attendance": [
        "🎯 Target ≥85% attendance. Each lecture builds on concepts from the previous ones.",
        "📅 Synchronize your class timetable with your personal calendar with automatic alert reminders.",
        "🤝 Partner with a study buddy to keep each other mutually accountable for showing up."
    ],
    "study_hours": [
        "📚 Aim for at least 20 study hours per week. Spread this across consistent daily slots.",
        "⏱️ Leverage the Pomodoro technique (25 min study, 5 min break) to combat fatigue.",
        "📆 Block out dedicated study hours in your weekly planner and treat them as non-negotiable."
    ],
    "assignment_completion": [
        "✅ Submit every single assignment on time. Homework counts directly toward GPA and anchors lecture concepts.",
        "📝 Divide larger projects into smaller deliverables with internal personal milestones.",
        "🗂️ Use visual planner boards (like Kanban, Trello, or Notion) to track project progress."
    ],
    "participation_score": [
        "🙋 Make a goal to ask at least one question or offer one comment during each lecture.",
        "💬 Join a peer study group to discuss and explain complex topics out loud.",
        "❓ Skim the reading materials before class so you are ready to engage with the professor."
    ],
    "sleep_hours": [
        "😴 Prioritize 7 to 8 hours of sleep. Memory consolidation occurs during deep sleep stages.",
        "📵 Turn off screens 30 minutes before bed to optimize sleep efficiency.",
        "🌙 Establish a stable circadian rhythm by waking up at the same time every day."
    ],
    "practice_test_score": [
        "📋 Complete at least one timed mock exam before the formal evaluation.",
        "🔁 Conduct error analyses on mock tests. Spend double the time review errors as you do correct answers.",
        "📖 Create custom flashcards for formula-heavy or factual definitions."
    ],
    "practice_problems": [
        "🧮 Commit to solving 12-15 practice problems daily instead of cramming them all on weekends.",
        "🎯 Highlight difficult homework problems and redo them a week later to test retrieval.",
        "📊 Keep a catalog of formulas and shortcut tricks for quick reference."
    ],
    "previous_gpa": [
        "📈 Devote 2 hours a week to reviewing foundations from earlier courses that carry over.",
        "🧑‍🏫 Visit office hours to clarify lingering gaps from previous semesters.",
        "📑 Maintain an indexed notebook of core concepts that link to current modules."
    ],
    "general": [
        "🍎 Take short 20-minute walks between study blocks. Cardio increases oxygen flow to the brain.",
        "🧘 Dedicate 5-10 minutes to breathing techniques before exams to reduce cognitive blockages.",
        "📓 Review your weekly achievements and failures in a personal study log."
    ]
}

def is_feature_weak(key: str, value: float) -> bool:
    """Check if the feature value is below the benchmark."""
    bench = BENCHMARKS[key]["good"]
    if key == "sleep_hours":
        lo, hi = bench
        return not (lo <= value <= hi)
    return value < bench

def run_performance_risk_analysis(features: dict, predicted_score: float) -> dict:
    """Analyze factors contributing to student academic risk."""
    risk_factors = []
    
    attendance = features.get("attendance", 100)
    study_hours = features.get("study_hours", 20)
    sleep = features.get("sleep_hours", 7.5)
    assignment = features.get("assignment_completion", 100)
    
    if attendance < 75:
        risk_factors.append("Low attendance is limiting direct instruction time and causing missing lecture links.")
    if study_hours < 10:
        risk_factors.append("Low independent study hours indicate insufficient consolidation of class materials.")
    if sleep < 6.0:
        risk_factors.append("Inadequate sleep hours are likely causing cognitive fatigue and lower class focus.")
    elif sleep > 9.5:
        risk_factors.append("Excessive sleep could indicate lethargy or poor time-blocking.")
    if assignment < 70:
        risk_factors.append("Low homework completion rate points to a lack of continuous practice and lost points.")
        
    risk_level = "Low"
    if predicted_score < 50 or attendance < 65:
        risk_level = "High"
    elif predicted_score < 70 or attendance < 78 or study_hours < 8.0:
        risk_level = "Medium"
        
    risk_description = "The student is currently in good standing. Keep up the consistent habits."
    if risk_level == "High":
        risk_description = "CRITICAL RISK: Multiple indicators suggest high potential for course failure. Immediate faculty/parent intervention is strongly advised."
    elif risk_level == "Medium":
        risk_description = "MODERATE RISK: Noticeable gaps in study hours, attendance, or practice test performance are dragging down predicted grades. Targeted corrective habits are required."
        
    return {
        "risk_level": risk_level,
        "risk_description": risk_description,
        "factors": risk_factors
    }

def generate_learning_roadmap(weaknesses_keys: List[str]) -> List[Dict[str, Any]]:
    """Generates a dynamic 4-week learning roadmap customized to identified weaknesses."""
    roadmap = []
    
    # Fallback to general/academic excellence if there are no weaknesses
    if not weaknesses_keys:
        return [
            {
                "week": 1,
                "title": "Maintain & Master",
                "focus": "Deepen understanding of core topics",
                "tasks": [
                    "Explore advanced/honors readings in your current syllabus.",
                    "Teach or peer-tutor a classmate struggling with the content (active teaching).",
                    "Establish a long-term research journal in your major domain."
                ]
            },
            {
                "week": 2,
                "title": "Build Peer Networks",
                "focus": "Collaboration and conceptual discussions",
                "tasks": [
                    "Lead a study circle to discuss key principles.",
                    "Engage in seminar debates or professor-led discussions."
                ]
            },
            {
                "week": 3,
                "title": "Optimize Workflow",
                "focus": "Productivity auditing",
                "tasks": [
                    "Audit your daily schedule to eliminate minor distractions.",
                    "Practice mindfulness to keep exam anxiety at 0."
                ]
            },
            {
                "week": 4,
                "title": "Continuous Excellence",
                "focus": "Reflection and review",
                "tasks": [
                    "Draft a reflection summary of your study processes this month.",
                    "Complete a comprehensive self-assessment to map future milestones."
                ]
            }
        ]
        
    # We have weaknesses! Build customized plan
    # Categorize weaknesses into priorities
    # Priority 1: Attendance, Sleep (Foundational / Lifestyle)
    # Priority 2: Study Hours, Assignment Completion (Academic habits)
    # Priority 3: Practice Problems, Practice Test Scores (Exam preparation)
    # Priority 4: Previous GPA, Participation (Long-term growth)
    
    p1 = [w for w in weaknesses_keys if w in ["attendance", "sleep_hours"]]
    p2 = [w for w in weaknesses_keys if w in ["study_hours", "assignment_completion"]]
    p3 = [w for w in weaknesses_keys if w in ["practice_problems", "practice_test_score"]]
    p4 = [w for w in weaknesses_keys if w in ["previous_gpa", "participation_score"]]
    
    # Week 1: Foundation & Routine
    week1_tasks = []
    if p1:
        for w in p1:
            week1_tasks.append(RECOMMENDATION_CATALOG[w][0])
    else:
        week1_tasks.append("Audit your morning routine to secure consistent lecture start times.")
        week1_tasks.append("Aim for exactly 7.5 to 8 hours of sleep per night.")
    week1_tasks.append("Log your sleep and wake times daily to identify sleep irregularities.")
    
    roadmap.append({
        "week": 1,
        "title": "Foundational Habits & Routines",
        "focus": "Stabilizing sleep schedules and securing lecture attendance",
        "tasks": week1_tasks
    })
    
    # Week 2: Academic Time Management
    week2_tasks = []
    if p2:
        for w in p2:
            week2_tasks.extend(RECOMMENDATION_CATALOG[w][:2])
    else:
        week2_tasks.append("Block out 3 distinct study periods of 2 hours in your weekly schedule.")
        week2_tasks.append("Finish all pending homework modules at least 24 hours before deadlines.")
    week2_tasks.append("Create a clean, dedicated study space free of phones and video distractions.")
    
    roadmap.append({
        "week": 2,
        "title": "Time Blocking & Submissions",
        "focus": "Boosting active study hours and completing weekly homework on time",
        "tasks": list(set(week2_tasks))[:3]
    })
    
    # Week 3: Active Practice & Mock Tests
    week3_tasks = []
    if p3:
        for w in p3:
            week3_tasks.extend(RECOMMENDATION_CATALOG[w][:2])
    else:
        week3_tasks.append("Complete 30 problems from a hard textbook chapter.")
        week3_tasks.append("Run a self-timed mock test on a previous unit.")
    week3_tasks.append("Review errors from your homework assignments and redo them on scratch paper.")
    
    roadmap.append({
        "week": 3,
        "title": "Active Practice & Testing",
        "focus": "Drilling problem types and validating recall via mock exams",
        "tasks": list(set(week3_tasks))[:3]
    })
    
    # Week 4: Lecture Engagement & Long-term Strategy
    week4_tasks = []
    if p4:
        for w in p4:
            week4_tasks.extend(RECOMMENDATION_CATALOG[w][:2])
    else:
        week4_tasks.append("Engage in a 5-minute conversation with your professor after class.")
        week4_tasks.append("Join a study group for upcoming final reviews.")
    week4_tasks.append("Summarize this week's topics in your own words in a cheat sheet.")
    
    roadmap.append({
        "week": 4,
        "title": "Class Engagement & Integration",
        "focus": "Participating in discussions and consolidating monthly study topics",
        "tasks": list(set(week4_tasks))[:3]
    })
    
    return roadmap

def generate_ai_analysis(features: dict, predicted_score: float) -> dict:
    """
    Analyzes student inputs to produce strengths, weaknesses,
    risk reports, and a milestone learning roadmap.
    """
    strengths = []
    weaknesses = []
    weaknesses_keys = []
    recommendations_pool = []
    
    for key, bench_info in BENCHMARKS.items():
        val = features.get(key)
        if val is None:
            continue
            
        label = bench_info["label"]
        unit = bench_info["unit"]
        
        if is_feature_weak(key, val):
            weaknesses.append(f"{label}: {val} {unit}")
            weaknesses_keys.append(key)
            recommendations_pool.extend(RECOMMENDATION_CATALOG.get(key, []))
        else:
            strengths.append(f"{label}: {val} {unit}")
            
    # Add general tips
    recommendations_pool.extend(RECOMMENDATION_CATALOG["general"])
    
    # Deduplicate and limit recommendations to 8 items
    seen = set()
    recommendations = []
    for rec in recommendations_pool:
        if rec not in seen:
            seen.add(rec)
            recommendations.append(rec)
        if len(recommendations) == 8:
            break
            
    # Summary message based on score
    if predicted_score >= 85:
        summary = "Outstanding performance prediction! Maintain your current study habits and focus on conceptual mastery."
    elif predicted_score >= 70:
        summary = "Solid projection, but there is room to improve. Fine-tune your weak areas to push into the Excellent category."
    elif predicted_score >= 50:
        summary = "Average performance projected. Prioritizing study times and mock exams will yield immediate grade gains."
    else:
        summary = "Underperformance risk. Immediate action to adjust sleep, attendance, and assignment completion is required."
        
    risk_analysis = run_performance_risk_analysis(features, predicted_score)
    roadmap = generate_learning_roadmap(weaknesses_keys)
    
    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "risk_level": risk_analysis["risk_level"],
        "risk_description": risk_analysis["risk_description"],
        "risk_factors": risk_analysis["factors"],
        "learning_roadmap": roadmap
    }

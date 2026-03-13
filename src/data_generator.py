"""
data_generator.py
-----------------
Generates a realistic synthetic dataset of 1500+ student records for training
the Student Performance Prediction model.

Each feature is correlated with the exam score in a realistic way, with added
noise to simulate real-world variance.
"""

import numpy as np
import pandas as pd
import os


def generate_student_dataset(n_samples: int = 1600, random_state: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic student performance dataset.

    Parameters
    ----------
    n_samples : int
        Number of student records to generate (default: 1600).
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with student features and exam scores.
    """
    rng = np.random.default_rng(random_state)

    # ── Core feature generation ────────────────────────────────────────────────

    # Attendance: 40–100 %
    attendance = rng.uniform(40, 100, n_samples)

    # Previous GPA: 1.5–10.0
    previous_gpa = rng.uniform(1.5, 10.0, n_samples)

    # Study hours per week: 2–40 hrs
    study_hours = rng.uniform(2, 40, n_samples)

    # Assignment completion rate: 30–100 %
    assignment_completion = rng.uniform(30, 100, n_samples)

    # Class participation score: 1–10
    participation_score = rng.uniform(1, 10, n_samples)

    # Sleep hours per day: 4–10 hrs
    sleep_hours = rng.uniform(4, 10, n_samples)

    # Practice test score: 20–100
    practice_test_score = rng.uniform(20, 100, n_samples)

    # Number of practice problems completed: 0–200
    practice_problems = rng.integers(0, 201, n_samples).astype(float)

    # ── Exam score formula (weighted combination + noise) ─────────────────────
    #
    # Weights are chosen to reflect real-world importance:
    #   practice_test_score  → strongest predictor
    #   previous_gpa         → normalised to 0-100 range
    #   study_hours          → normalised
    #   attendance
    #   assignment_completion
    #   participation_score  → normalised
    #   sleep_hours          → inverted U-shape penalty
    #   practice_problems    → normalised

    sleep_penalty = -np.abs(sleep_hours - 7.5) * 1.5   # optimal ~7.5 hrs

    raw_score = (
        0.28 * practice_test_score
        + 0.22 * (previous_gpa / 10.0 * 100)
        + 0.18 * (study_hours / 40.0 * 100)
        + 0.10 * attendance
        + 0.10 * assignment_completion
        + 0.05 * (participation_score / 10.0 * 100)
        + 0.05 * (practice_problems / 200.0 * 100)
        + sleep_penalty
        + rng.normal(0, 5, n_samples)          # Gaussian noise
    )

    # Clip to valid [0, 100] range
    exam_score = np.clip(raw_score, 0, 100).round(2)

    # ── Assemble DataFrame ────────────────────────────────────────────────────
    df = pd.DataFrame({
        "attendance":            attendance.round(2),
        "previous_gpa":          previous_gpa.round(2),
        "study_hours":           study_hours.round(2),
        "assignment_completion": assignment_completion.round(2),
        "participation_score":   participation_score.round(2),
        "sleep_hours":           sleep_hours.round(2),
        "practice_test_score":   practice_test_score.round(2),
        "practice_problems":     practice_problems.astype(int),
        "exam_score":            exam_score,
    })

    return df


def save_dataset(output_path: str = "data/dataset.csv") -> pd.DataFrame:
    """
    Generate and save the dataset to disk.

    Parameters
    ----------
    output_path : str
        Relative or absolute path for the CSV file.

    Returns
    -------
    pd.DataFrame
        The generated dataset.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = generate_student_dataset()
    df.to_csv(output_path, index=False)
    print(f"[data_generator] Dataset saved → {output_path}  ({len(df)} rows)")
    return df


# ── Standalone execution ──────────────────────────────────────────────────────
if __name__ == "__main__":
    save_dataset()
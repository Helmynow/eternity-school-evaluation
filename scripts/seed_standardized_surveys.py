"""
Seed standardized parent/staff surveys and questions into the database.
"""

from __future__ import annotations

import argparse
from typing import Dict, List

from backend.database import Database, Survey, SurveyQuestion
from backend.standardized_survey_templates import load_standardized_survey_bundle


QUESTION_TYPE_MAP = {
    "likert": "rating",
    "categorical": "multiple_choice",
    "open": "text",
}


def _map_question(question: Dict, section_name: str, order_index: int) -> Dict:
    question_type = QUESTION_TYPE_MAP.get(str(question.get("type")).lower(), "text")
    options = question.get("options") if question_type == "multiple_choice" else []
    return {
        "question_text": question.get("text"),
        "question_type": question_type,
        "category": question.get("domain") or section_name,
        "section": question.get("section") or section_name,
        "order_index": order_index,
        "required": question_type != "text",
        "identity_modes": ["anonymous", "conditional", "partial", "identified"],
        "sensitivity_level": "low",
        "options": options,
    }


def seed_standardized_surveys(*, dry_run: bool = False, overwrite: bool = False) -> None:
    bundle = load_standardized_survey_bundle()
    surveys = bundle.get("surveys", [])

    db = Database()
    with db.session_scope() as session:
        for template in surveys:
            title = template.get("name")
            if not title:
                continue

            existing = session.query(Survey).filter(Survey.title == title).first()
            if existing and not overwrite:
                print(f"Skipping existing survey: {title}")
                continue

            if existing and overwrite:
                session.query(SurveyQuestion).filter(SurveyQuestion.survey_id == existing.id).delete()
                survey = existing
                survey.description = template.get("description") or survey.description
                survey.survey_type = "standardized"
                survey.status = survey.status or "draft"
                print(f"Updating survey: {title}")
            else:
                survey = Survey(
                    title=title,
                    description=template.get("description")
                    or f"{template.get('audience')} {template.get('term_type')} standardized survey",
                    survey_type="standardized",
                    status="draft",
                )
                session.add(survey)
                session.flush()
                print(f"Creating survey: {title}")

            order_index = 1
            for section in template.get("sections", []):
                for question in section.get("questions", []):
                    payload = _map_question(question, section.get("name", ""), order_index)
                    order_index += 1
                    session.add(SurveyQuestion(survey_id=survey.id, **payload))

        if dry_run:
            print("Dry run enabled; rolling back changes.")
            session.rollback()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed standardized surveys into the database.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without committing")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing surveys with same title")
    args = parser.parse_args()

    seed_standardized_surveys(dry_run=args.dry_run, overwrite=args.overwrite)


if __name__ == "__main__":
    main()

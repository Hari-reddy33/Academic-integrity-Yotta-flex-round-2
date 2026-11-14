from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IntegrityRule
from app.services.similarity import compare_text


def compare_with_active_rule(text_a: str, text_b: str, db: Session) -> dict:
    result = compare_text(text_a, text_b)
    rule = db.scalar(select(IntegrityRule).order_by(IntegrityRule.effective_from.desc()))
    threshold = rule.review_threshold if rule else 0.72
    return {
        **result,
        "threshold": threshold,
        "review_flag": result["score"] >= threshold,
        "model": "TF-IDF word and bigram cosine baseline",
        "notice": (
            "Lexical overlap only. This is not a misconduct finding; "
            "review quotations, templates, attribution and context."
        ),
        "input_retained": False,
    }

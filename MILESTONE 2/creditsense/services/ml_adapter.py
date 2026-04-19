from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .settings import settings


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _heuristic_score(profile: dict[str, Any], ratios: dict[str, Any]) -> tuple[float, str]:
    score = 50.0

    credit_score = float(profile.get("credit_score") or 0)
    post_loan_dti = ratios.get("post_loan_dti")
    payment_history = str(profile.get("payment_history") or "").lower()
    employment_years = float(profile.get("employment_years") or 0)

    if credit_score >= 750:
        score += 25
    elif credit_score >= 680:
        score += 12
    elif credit_score >= 600:
        score += 3
    else:
        score -= 15

    if post_loan_dti is not None:
        if post_loan_dti <= 0.45:
            score += 18
        elif post_loan_dti <= 0.60:
            score += 6
        elif post_loan_dti <= 0.75:
            score -= 8
        else:
            score -= 18

    if "clean" in payment_history:
        score += 8
    elif "1" in payment_history:
        score -= 6
    elif "2+" in payment_history or "multiple" in payment_history:
        score -= 14

    if employment_years >= 2:
        score += 6
    elif employment_years >= 1:
        score += 2
    else:
        score -= 4

    final_score = _clamp(score)
    if final_score >= 75:
        return final_score, "LOW"
    if final_score >= 55:
        return final_score, "MEDIUM"
    return final_score, "HIGH"


class RiskModelAdapter:
    def __init__(self) -> None:
        self._model = None
        self._loaded = False
        self._model_path = Path(settings.model_path)
        self._fallback_path = Path(settings.fallback_model_path)

    def _load_model(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        for path in (self._model_path, self._fallback_path):
            if path.exists():
                try:
                    self._model = joblib.load(path)
                    return
                except Exception:
                    self._model = None

    def _feature_frame(self, profile: dict[str, Any], ratios: dict[str, Any]) -> pd.DataFrame:
        row = {
            "age": float(profile.get("age") or 0),
            "monthly_income": float(profile.get("monthly_income") or 0),
            "credit_score": float(profile.get("credit_score") or 0),
            "existing_emi_monthly": float(profile.get("existing_emi_monthly") or 0),
            "loan_amount_requested": float(profile.get("loan_amount_requested") or 0),
            "loan_tenure_months": float(profile.get("loan_tenure_months") or 0),
            "employment_years": float(profile.get("employment_years") or 0),
            "post_loan_dti": float(ratios.get("post_loan_dti") or 0),
            "ltv_ratio": float(ratios.get("ltv_ratio") or 0),
        }
        return pd.DataFrame([row])

    def score(self, profile: dict[str, Any], ratios: dict[str, Any]) -> tuple[float, str]:
        self._load_model()
        fallback_score, fallback_class = _heuristic_score(profile, ratios)
        if self._model is None:
            return fallback_score, fallback_class

        try:
            frame = self._feature_frame(profile, ratios)
            if hasattr(self._model, "predict_proba"):
                probs = self._model.predict_proba(frame)
                safe_prob = float(probs[0][-1])
                score = _clamp(safe_prob * 100)
            else:
                pred = float(self._model.predict(frame)[0])
                score = _clamp(pred * 100)

            if score >= 75:
                return score, "LOW"
            if score >= 55:
                return score, "MEDIUM"
            return score, "HIGH"
        except Exception:
            return fallback_score, fallback_class


risk_model = RiskModelAdapter()

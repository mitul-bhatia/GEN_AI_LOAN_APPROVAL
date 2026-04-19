from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class Scenario:
    name: str
    turns: list[str]


SCENARIOS = [
    Scenario(
        name="Salaried Personal Loan",
        turns=[
            "Rajesh Kumar age 45 from Mumbai, salaried, employment 6 years, monthly income Rs 60000",
            "Credit score is 720 and he has one existing loan with EMI Rs 8000 and clean payment history",
            "He needs personal loan of 5 lakh for 36 months with no collateral",
            "Generate report now",
        ],
    ),
    Scenario(
        name="Self Employed Secured",
        turns=[
            "Borrower name is Neha Jain, age 39, city Jaipur, self employed for 8 years, monthly income 180000",
            "Credit score 765, existing loan count 2, existing EMI 22000, payment history clean",
            "Loan requested 1200000 for business over 60 months, collateral property worth 2500000",
            "Please generate credit report",
        ],
    ),
    Scenario(
        name="Borderline Credit Watch",
        turns=[
            "Aman Verma 31 years old from Pune, contract employee, employment 2 years, monthly income 55000",
            "Credit score 681, no existing loan, payment history one default",
            "Wants vehicle loan amount 900000 tenure 48 months with vehicle collateral value 1000000",
            "Generate underwriting report",
        ],
    ),
    Scenario(
        name="High Risk Escalate",
        turns=[
            "Borrower is Imran Ali age 28 city Lucknow gig worker employment 1 year monthly income 35000",
            "Credit score 590, existing loan count 2, existing emi 15000, payment history 2+ defaults",
            "Need personal loan Rs 700000 for 36 months, no collateral",
            "Generate report",
        ],
    ),
    Scenario(
        name="Education Loan Conditional",
        turns=[
            "Sana Kapoor, 33, from Delhi, salaried for 3 years, income 90000",
            "Credit score 705, existing loan count 1, existing EMI 12000, clean history",
            "Applying for education loan 1000000 for 72 months, collateral fixed deposit value 1200000",
            "Please generate final report",
        ],
    ),
]


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def run_scenarios(base_url: str) -> dict[str, Any]:
    out: list[dict[str, Any]] = []

    with httpx.Client(timeout=240.0) as client:
        health_resp = client.get(_url(base_url, "/api/v1/health"))
        health_resp.raise_for_status()
        health_data = health_resp.json()

        for scenario in SCENARIOS:
            state_resp = client.get(_url(base_url, "/api/v1/agent/state/initial"))
            state_resp.raise_for_status()
            state = state_resp.json()["state"]

            final_payload: dict[str, Any] | None = None
            for turn in scenario.turns:
                response = client.post(
                    _url(base_url, "/api/v1/agent/turn"),
                    json={"user_message": turn, "state": state},
                )
                response.raise_for_status()
                payload = response.json()
                state = payload["state"]
                final_payload = payload

            assert final_payload is not None
            report_ready = bool(final_payload.get("report_ready"))
            retrieved_count = int(final_payload.get("retrieved_count") or 0)
            citations_count = int(final_payload.get("citations_count") or 0)
            decision = final_payload.get("decision")
            decision_score = final_payload.get("decision_score")

            out.append(
                {
                    "scenario": scenario.name,
                    "report_ready": report_ready,
                    "retrieved_count": retrieved_count,
                    "citations_count": citations_count,
                    "decision": decision,
                    "decision_score": decision_score,
                    "pass": report_ready and retrieved_count > 0 and citations_count > 0,
                }
            )

    passed = sum(1 for item in out if item["pass"])
    return {
        "health": health_data,
        "results": out,
        "summary": {
            "total": len(out),
            "passed": passed,
            "failed": len(out) - passed,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end borrower scenarios on CreditSense API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = run_scenarios(args.base_url)
    if args.pretty:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report))


if __name__ == "__main__":
    main()

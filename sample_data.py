import json
from datetime import date

import requests

BASE_URL = "http://127.0.0.1:8000"


def create_decision(title: str, context: str) -> int:
    response = requests.post(
        f"{BASE_URL}/decision",
        json={
            "date": date.today().isoformat(),
            "title": title,
            "context": context,
            "constraints": [{"text": "Budget limited"}],
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]


def add_assumptions(decision_id: int, assumptions: list[str]) -> None:
    response = requests.post(
        f"{BASE_URL}/decision/{decision_id}/assumptions",
        json=[{"text": item} for item in assumptions],
        timeout=10,
    )
    response.raise_for_status()


def add_outcome(decision_id: int, outcome: str) -> None:
    response = requests.post(
        f"{BASE_URL}/decision/{decision_id}/outcome",
        json={"text": outcome},
        timeout=10,
    )
    response.raise_for_status()


def print_reflection(decision_id: int) -> None:
    response = requests.get(
        f"{BASE_URL}/decision/{decision_id}/reflection",
        timeout=10,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


def main() -> None:
    decision_one = create_decision(
        "Launch onboarding survey",
        "We need better insight into activation drop-off during onboarding.",
    )
    add_assumptions(
        decision_one,
        [
            "Users are willing to answer a 3-question survey",
            "Survey completion will increase activation rate",
        ],
    )
    add_outcome(
        decision_one,
        "Users are willing to answer a 3-question survey, but activation rate stayed flat.",
    )

    decision_two = create_decision(
        "Reduce pricing tiers",
        "We suspect too many tiers are confusing prospects.",
    )
    add_assumptions(
        decision_two,
        [
            "Simpler tiers increase trial conversion",
            "Sales team will need fewer custom quotes",
        ],
    )
    add_outcome(
        decision_two,
        "Simpler tiers increase trial conversion and reduce custom quote requests.",
    )

    print_reflection(decision_one)
    print_reflection(decision_two)


if __name__ == "__main__":
    main()

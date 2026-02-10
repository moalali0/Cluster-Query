import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

CLIENTS = ["Bank_A", "Bank_B"]
CLAUSES = [
    "This agreement is governed by the laws of England and Wales.",
    "This agreement shall be governed by New York law.",
    "The parties submit to the exclusive jurisdiction of Brussels courts.",
    "No amendment is valid unless in writing and signed by both parties.",
    "Either party may terminate with 30 days written notice.",
    "Payment obligations survive termination of this agreement.",
    "Force majeure events suspend obligations for the affected party.",
    "Disputes shall be resolved by arbitration in London.",
    "Collateral must be delivered within one business day.",
    "Confidential information must not be disclosed to third parties.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate phase-0 mock clusters CSV")
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path. Defaults to /data/mock_clusters.csv when available, else data/mock_clusters.csv.",
    )
    return parser.parse_args()


def resolve_output_path(raw_output: str | None) -> Path:
    if raw_output:
        return Path(raw_output)

    docker_path = Path("/data/mock_clusters.csv")
    if docker_path.parent.exists():
        return docker_path

    return Path(__file__).resolve().parents[2] / "data" / "mock_clusters.csv"


def make_row(i: int) -> dict:
    client_id = CLIENTS[i % len(CLIENTS)]
    clause = CLAUSES[i % len(CLAUSES)]
    days_ago = 60 - i
    last_updated = datetime.now(timezone.utc) - timedelta(days=max(days_ago, 1))

    if "governed" in clause.lower() or "jurisdiction" in clause.lower():
        codified = {
            "Governing Law": {
                "Jurisdiction": "England & Wales" if i % 3 else "Belgium",
                "Party A": "Yes",
                "Party B": "Yes",
            }
        }
    else:
        codified = {
            "Credit Support Provider": {
                "Party A": "Yes",
                "Party B": "No" if i % 4 else "Yes",
                "Name": f"Entity-{(i % 12) + 1}",
            }
        }

    history = [
        {
            "query": "Please confirm codification approach for this clause.",
            "role": "Analyst",
            "date": (last_updated - timedelta(days=2)).date().isoformat(),
        },
        {
            "response": "Capture as agreed in client operating memo.",
            "role": "Client",
            "date": (last_updated - timedelta(days=1)).date().isoformat(),
        },
    ]

    return {
        "id": str(uuid4()),
        "client_id": client_id,
        "text_content": clause,
        "codified_data": json.dumps(codified, separators=(",", ":")),
        "query_history": json.dumps(history, separators=(",", ":")),
        "doc_count": 500 + ((i * 37) % 1400),
        "last_updated": last_updated.isoformat(),
    }


def main() -> None:
    args = parse_args()
    output_path = resolve_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "client_id",
                "text_content",
                "codified_data",
                "query_history",
                "doc_count",
                "last_updated",
            ],
        )
        writer.writeheader()
        for i in range(50):
            writer.writerow(make_row(i))

    print(f"Wrote 50 rows to {output_path}")


if __name__ == "__main__":
    main()

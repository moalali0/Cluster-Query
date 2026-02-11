import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid5, NAMESPACE_DNS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate phase-0 mock clusters CSV from codification data")
    parser.add_argument(
        "--input",
        default=None,
        help="Input codification CSV. Defaults to /data/mock_codification.csv (Docker) or data/mock_codification.csv.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path. Defaults to /data/mock_clusters.csv (Docker) or data/mock_clusters.csv.",
    )
    return parser.parse_args()


def resolve_path(raw: str | None, filename: str) -> Path:
    if raw:
        return Path(raw)

    docker_path = Path(f"/data/{filename}")
    if docker_path.parent.exists() and docker_path.parent.is_dir():
        return docker_path

    return Path(__file__).resolve().parents[2] / "data" / filename


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input, "mock_codification.csv")
    output_path = resolve_path(args.output, "mock_clusters.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group rows by Cluster ID
    clusters: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        clusters[row["Cluster"]].append(row)

    out_rows: list[dict] = []
    for cluster_id, entries in clusters.items():
        first = entries[0]

        # Deterministic UUID from cluster ID for reproducibility
        uid = str(uuid5(NAMESPACE_DNS, cluster_id))

        # Client from Tags (first segment, e.g. "Bank_A" from "Bank_A;ISDA;2002")
        tags = first.get("Tags", "")
        client_id = tags.split(";")[0] if tags else "Unknown"

        # Text content (same across all rows in a cluster)
        text_content = first.get("Text", "")

        # Build codified_data: {Term: {Attr1: Val1, Attr2: Val2, ...}}
        codified: dict[str, dict[str, str]] = defaultdict(dict)
        for entry in entries:
            term = entry.get("Term", "")
            attr = entry.get("Attribute", "")
            val = entry.get("Value", "")
            if term and attr:
                codified[term][attr] = val

        # Count unique Doc IDs
        doc_ids = {e.get("Doc id", "") for e in entries}
        doc_count = len(doc_ids)

        # Parse date
        raw_date = first.get("Clusterpoint Date", "")
        try:
            dt = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)

        # Build query_history from agreement context
        agreement_ref = first.get("Agreement Ref", "")
        tag_parts = tags.split(";")
        agreement_type = tag_parts[1] if len(tag_parts) > 1 else "Agreement"
        history = [
            {
                "query": f"Please confirm codification approach for {agreement_type} clause ({agreement_ref}).",
                "role": "Analyst",
                "date": dt.date().isoformat(),
            },
            {
                "response": "Capture as agreed in client operating memo.",
                "role": "Client",
                "date": dt.date().isoformat(),
            },
        ]

        out_rows.append(
            {
                "id": uid,
                "client_id": client_id,
                "text_content": text_content,
                "codified_data": json.dumps(dict(codified), separators=(",", ":")),
                "query_history": json.dumps(history, separators=(",", ":")),
                "doc_count": doc_count,
                "last_updated": dt.isoformat(),
            }
        )

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
        writer.writerows(out_rows)

    print(f"Transformed {len(rows)} codification rows into {len(out_rows)} cluster rows -> {output_path}")


if __name__ == "__main__":
    main()

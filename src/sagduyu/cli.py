from __future__ import annotations

import argparse
import json

from sagduyu.engine import CoordinationEngine
from sagduyu.scenarios import SCENARIOS, load_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a SAĞDUYU replay scenario.")
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    args = parser.parse_args()

    alerts = CoordinationEngine().analyze(load_scenario(args.scenario))
    for alert in alerts:
        print(json.dumps(alert.model_dump(mode="json"), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

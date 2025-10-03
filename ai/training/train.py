"""Minimal training script with MLflow initialization.

Run:
    python ai/training/train.py

Environment (optional):
    export MLFLOW_TRACKING_URI=./ai/mlruns   # defaults if not set
"""

from __future__ import annotations
import os
import time

try:
    import mlflow  # type: ignore
except ImportError:  # keep minimal: user installs via ai/requirements.txt
    mlflow = None  # type: ignore


def main() -> None:
    print("[training] minimal MLflow demo")
    if mlflow is None:
        print("[warning] mlflow not installed. Install with: pip install -r ai/requirements.txt")
        return

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "./ai/mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("demo_minimal")

    with mlflow.start_run() as run:
        mlflow.log_param("example_param", 42)
        for step in range(3):
            loss = 1.0 / (step + 1)
            mlflow.log_metric("loss", loss, step=step)
            time.sleep(0.1)
        print(f"Run complete: {run.info.run_id} (tracking_uri={tracking_uri})")


if __name__ == "__main__":  # pragma: no cover (minimal script)
    main()

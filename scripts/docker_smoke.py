"""Start an isolated container, check readiness and HTTP behavior, then remove it."""

import argparse
import subprocess
import time
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Locally built Docker image to test")
    args = parser.parse_args()
    name = f"ideas-smoke-{uuid.uuid4().hex[:12]}"
    subprocess.run(
        ["docker", "run", "--detach", "--name", name, args.image],
        check=True,
        timeout=30,
    )
    try:
        for _ in range(30):
            ready = subprocess.run(
                [
                    "docker",
                    "exec",
                    name,
                    "python",
                    "-c",
                    "from urllib.request import urlopen; "
                    "urlopen('http://127.0.0.1:8080/health', timeout=2)",
                ],
                capture_output=True,
                timeout=10,
            )
            if ready.returncode == 0:
                break
            time.sleep(2)
        else:
            raise RuntimeError("App did not become healthy within the readiness window")
        script = Path(__file__).with_name("smoke_test.py").read_text(encoding="utf-8")
        subprocess.run(
            ["docker", "exec", "-i", name, "python", "-"],
            input=script,
            text=True,
            check=True,
            timeout=60,
        )
    except Exception:
        subprocess.run(["docker", "logs", name], check=False, timeout=15)
        raise
    finally:
        subprocess.run(["docker", "rm", "--force", name], check=True, timeout=30)


if __name__ == "__main__":
    main()

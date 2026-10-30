"""Bounded HTTPS checks; never print credentials or response bodies on failure."""
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit


def get_json(url, token=None):
    headers = {"Authorization": "Bearer " + token} if token else {}
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        if response.status != 200:
            raise ValueError("Unexpected HTTP status")
        return json.load(response)


def main():
    base = os.environ.get("APP_URL", "").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment or parsed.path:
        sys.exit("APP_URL must be the HTTPS origin, without credentials, query or path.")
    expected = os.environ.get("EXPECTED_REVISION", "")
    token = os.environ.get("MONITORING_TOKEN", "")
    drill = os.environ.get("FAILURE_DRILL", "false") == "true"
    attempts = 1 if drill else int(os.environ.get("CHECK_ATTEMPTS", "12"))
    endpoint = "/__monitoring_drill__/" if drill else "/health/"
    start = time.monotonic()
    for attempt in range(attempts):
        try:
            request_start = time.monotonic()
            data = get_json(base + endpoint)
            duration = round((time.monotonic() - request_start) * 1000, 2)
            if data.get("status") != "ok" or (expected and data.get("revision") != expected):
                raise ValueError("Health or revision mismatch")
            if not token:
                sys.exit("MONITORING_TOKEN must be configured to verify resource metrics.")
            metrics = get_json(base + "/metrics/", token)
            if not all(isinstance(metrics.get(k), (float, int)) for k in ("memory_bytes", "cpu_seconds_total")):
                raise ValueError("Metrics response invalid")
            summary = (f"Health check passed. Response time: {duration} ms. "
                       f"Total readiness wait: {round(time.monotonic()-start, 1)} s. "
                       f"Worker memory ({metrics.get('memory_kind', 'unspecified')}): {round(metrics['memory_bytes']/1048576, 2)} MiB. "
                       f"Worker cumulative CPU: {metrics['cpu_seconds_total']} s.")
            print(summary)
            if os.environ.get("GITHUB_STEP_SUMMARY"):
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                    f.write(summary + "\n")
            return
        except Exception as error:
            # Class only: URL/error messages may contain confidential details.
            print(f"Check attempt {attempt+1} unsuccessful ({type(error).__name__}).")
            if attempt + 1 < attempts:
                time.sleep(10)
    sys.exit("Controlled monitoring drill failed as intended." if drill else "Service checks failed; inspect the hosting logs.")


if __name__ == "__main__":
    main()

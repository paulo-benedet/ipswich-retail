"""Trigger the exact CI-tested revision using a secret Render deploy hook."""
import os
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen


def main():
    hook = os.environ.get("RENDER_DEPLOY_HOOK", "")
    revision = os.environ.get("GITHUB_SHA", "")
    parts = urlsplit(hook)
    if parts.scheme != "https" or parts.hostname != "api.render.com" or not revision:
        sys.exit("Configure the Render HTTPS deploy hook and commit revision.")
    query = dict(parse_qsl(parts.query))
    query["ref"] = revision
    url = urlunsplit(parts._replace(query=urlencode(query)))
    try:
        with urlopen(Request(url, data=b"", method="POST"), timeout=30) as response:
            if response.status not in (200, 202):
                sys.exit("Render did not accept the deployment.")
    except Exception:
        sys.exit("Deployment trigger failed; verify the secret hook in Render. The hook was not logged.")
    print("Deployment requested for the CI-tested revision.")


if __name__ == "__main__":
    main()

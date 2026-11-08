import base64
import getpass
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings


GRAPHQL_URL = "https://i.instagram.com/graphql/query"
OPERATION_NAME = "IGSettingsBooleanMutation"
DOCUMENT_ID = "2669261950526978627082629536"
SETTING_ID = "hide_followers_following_list"
RESPONSE_KEY = "xdt_api__v1__settings__set_bool"
HIDE_LISTS = False


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("Redirect refused; credentials were not forwarded.")


def show_lists(sessionid: str) -> dict:
    if not sessionid or any(ord(c) <= 32 or ord(c) >= 127 or c in ';,"\\' for c in sessionid):
        raise ValueError("Enter only the sessionid cookie value, without 'sessionid='.")
    match = re.fullmatch(r"([1-9][0-9]*)(?::|%3[aA]).+", sessionid)
    if not match:
        raise ValueError("Invalid sessionid format: expected a numeric user ID followed by ':' or '%3A'.")
    user_id = match.group(1)
    token = base64.b64encode(json.dumps({
        "ds_user_id": user_id,
        "sessionid": sessionid,
        "should_use_header_over_cookies": True,
    }, separators=(",", ":")).encode()).decode("ascii")
    authorization = "Bearer IGT:2:" + token
    variables = {
        "setting_id": SETTING_ID,
        "allow_error_codes": True,
        "callsite": "account_privacy",
        "value": HIDE_LISTS,
    }
    form = {
        "method": "post",
        "format": "json",
        "server_timestamps": "true",
        "locale": "user",
        "fb_api_req_friendly_name": OPERATION_NAME,
        "client_doc_id": DOCUMENT_ID,
        "variables": json.dumps(variables),
    }
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=urllib.parse.urlencode(form).encode(),
        headers={
            "Authorization": authorization,
            "Cookie": f"sessionid={sessionid}; ds_user_id={user_id}",
            "IG-INTENDED-USER-ID": user_id,
            "X-IG-App-ID": "124024574287414",
            "X-Auth-Type": "instagram",
            "User-Agent": "Instagram 453.0.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "identity",
            "X-GraphQL-Client-Library": "pando",
            "X-FB-Friendly-Name": OPERATION_NAME,
        },
        method="POST",
    )

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise RuntimeError("Response too large.")
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        code = error.code
        with error:
            raw = error.read(16385)
        details = {}
        try:
            body = json.loads(raw) if len(raw) <= 16384 else {}
            if isinstance(body, dict):
                for key in ("message", "error_type", "status", "code"):
                    if isinstance(body.get(key), (str, int, bool)):
                        details[key] = body[key]
        except (ValueError, UnicodeError):
            pass
        text = json.dumps(details) if details else "No selected JSON error details."
        secrets = {authorization, token, sessionid, urllib.parse.unquote(sessionid),
                   urllib.parse.quote(sessionid, safe="")}
        for secret in sorted(secrets, key=len, reverse=True):
            if secret:
                text = text.replace(secret, "<REDACTED>")
        raise RuntimeError(f"HTTP {code}: {text[:1500]}. No retry performed.") from None


def update_confirmed(body: object) -> bool:
    if not isinstance(body, dict) or body.get("errors") or body.get("error") or body.get("status") == "fail":
        return False

    data = body.get("data")
    if not isinstance(data, dict):
        return False
    results = [
        value for key, value in data.items()
        if key == RESPONSE_KEY or key.startswith(RESPONSE_KEY + "(")
    ]
    if len(results) != 1 or not isinstance(results[0], dict):
        return False

    result = results[0]
    error_fields = (
        "error_name_value", "errorNameValue", "fallback_message", "fallbackMessage",
    )
    return result.get("value") is HIDE_LISTS and not any(result.get(key) for key in error_fields)


def main() -> int:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            session = getpass.getpass("Instagram sessionid: ").strip()
        body = show_lists(session)
        if not update_confirmed(body):
            raise RuntimeError("Instagram did not confirm disabling the setting. No retry performed.")
        print("Instagram confirmed that list hiding is disabled.")
        return 0
    except getpass.GetPassWarning:
        print("Private input is unavailable. Run this script in an interactive terminal.", file=sys.stderr)
    except EOFError:
        print("No input received.", file=sys.stderr)
    except RuntimeError as error:
        print(error, file=sys.stderr)
    except (urllib.error.URLError, TimeoutError, OSError):
        print("Network/TLS failure. No retry performed.", file=sys.stderr)
    except json.JSONDecodeError:
        print("Invalid JSON response. No retry performed.", file=sys.stderr)
    except ValueError as error:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit("Interrupted. The update may have been applied; check before retrying.")

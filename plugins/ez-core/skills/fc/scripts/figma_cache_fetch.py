#!/usr/bin/env python3
import argparse
import base64
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_SCRIPT = SCRIPT_DIR / "figma_cache_index.py"

PROTOCOL_VERSION = "2025-03-26"
ACTIONS = (
    "get_design_context",
    "get_metadata",
    "get_screenshot",
    "get_image",
    "download_assets",
    "get_variable_defs",
    "search_design_system",
    "get_libraries",
)

NODE_OPTIONAL_ACTIONS = frozenset(
    {"get_metadata", "get_libraries", "search_design_system"}
)

DESIGN_CONTEXT_ASSET_RE = re.compile(
    r'const\s+(img[A-Za-z0-9_]+)\s*=\s*"([^"]+)"'
)

# Cache entries older than this are re-fetched (see the fc skill).
CACHE_MAX_AGE = timedelta(days=7)


def parse_cached_at(cached_at):
    if not cached_at or cached_at == "unknown":
        return None
    try:
        return datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_cache_stale(cached_at):
    parsed = parse_cached_at(cached_at)
    if parsed is None:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - parsed > CACHE_MAX_AGE


def parse_figma_url(url):
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    file_key = None
    for marker in ("design", "board", "slides", "make"):
        if marker in parts:
            idx = parts.index(marker)
            if idx + 2 < len(parts) and parts[idx + 2] == "branch":
                file_key = parts[idx + 3] if idx + 3 < len(parts) else None
            elif idx + 1 < len(parts):
                file_key = parts[idx + 1]
            break
    node_id = None
    qs = parse_qs(parsed.query)
    if "node-id" in qs and qs["node-id"][0]:
        node_id = qs["node-id"][0]
    return file_key, node_id


def sse_to_messages(body):
    messages = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data = line[5:].strip()
            if data:
                try:
                    messages.append(json.loads(data))
                except json.JSONDecodeError:
                    continue
    return messages


def post(server, payload, session_id=None):
    req = urllib.request.Request(server, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    body = json.dumps(payload).encode("utf-8")
    resp = urllib.request.urlopen(req, body, timeout=180)
    new_session = resp.headers.get("Mcp-Session-Id") or session_id
    raw = resp.read().decode("utf-8", errors="replace")
    ctype = resp.headers.get("Content-Type") or ""
    message = None
    if raw:
        if "text/event-stream" in ctype:
            for m in sse_to_messages(raw):
                if isinstance(m, dict) and ("result" in m or "error" in m):
                    message = m
        else:
            message = json.loads(raw)
    return message, new_session


def first_text_content(response):
    content = response.get("content")
    if not isinstance(content, list):
        return ""
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                return text
    return ""


def extension_for_url(url, fallback="bin"):
    path = urlparse(url).path
    if "." in path.rsplit("/", 1)[-1]:
        return path.rsplit(".", 1)[-1].lower()
    return fallback


def download_url(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest.stat().st_size


def extract_design_context_assets(text):
    assets = []
    seen = set()
    for match in DESIGN_CONTEXT_ASSET_RE.finditer(text):
        name, url = match.group(1), match.group(2)
        if not url.startswith("http"):
            continue
        key = (name, url)
        if key in seen:
            continue
        seen.add(key)
        assets.append({"kind": "design_context", "name": name, "url": url})
    return assets


def parse_json_blob(text):
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def parse_download_assets_payload(result):
    if not isinstance(result, dict):
        return None
    for key in ("export", "rawImages", "svgAssets"):
        if key in result:
            return result
    text = first_text_content(result)
    if text:
        blob = parse_json_blob(text)
        if isinstance(blob, dict) and (
            "export" in blob or "rawImages" in blob or "svgAssets" in blob
        ):
            return blob
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    return None


def assets_from_download_payload(payload, only=None):
    items = []
    export = payload.get("export")
    if export and export.get("url") and (only in (None, "export")):
        fmt = export.get("format") or extension_for_url(export["url"], "png")
        items.append(
            {
                "kind": "export",
                "name": "export",
                "url": export["url"],
                "filename": f"export.{fmt}",
            }
        )
    if only in (None, "raw"):
        for idx, raw in enumerate(payload.get("rawImages") or [], start=1):
            if not raw.get("url"):
                continue
            fmt = raw.get("format") or extension_for_url(raw["url"], "bin")
            items.append(
                {
                    "kind": "raw",
                    "name": f"raw-{idx:02d}",
                    "url": raw["url"],
                    "filename": f"raw-{idx:02d}.{fmt}",
                }
            )
    if only in (None, "svg"):
        for idx, svg in enumerate(payload.get("svgAssets") or [], start=1):
            if not svg.get("url"):
                continue
            fmt = svg.get("format") or "svg"
            items.append(
                {
                    "kind": "svg",
                    "name": f"svg-{idx:02d}",
                    "url": svg["url"],
                    "filename": f"svg-{idx:02d}.{fmt}",
                }
            )
    return items


def assets_from_image_response(response):
    items = []
    content = response.get("content")
    if not isinstance(content, list):
        return items
    for idx, item in enumerate(content, start=1):
        if not isinstance(item, dict) or item.get("type") != "image":
            continue
        data = item.get("data")
        if not data:
            continue
        mime = item.get("mimeType") or "image/png"
        ext = mime.split("/")[-1] if "/" in mime else "png"
        items.append(
            {
                "kind": "get_image",
                "name": f"image-{idx:02d}",
                "data": data,
                "filename": f"export.{ext}",
            }
        )
    return items


def assets_from_cached_payload(payload, only=None, asset_var=None):
    action = payload.get("action")
    response = payload.get("response") or {}
    if action == "get_image":
        assets = assets_from_image_response(response)
        if only == "svg":
            return []
        if only == "raw":
            return []
        return assets
    if action == "download_assets":
        parsed = parse_download_assets_payload(response)
        if not parsed:
            return []
        return assets_from_download_payload(parsed, only=only)
    if action == "get_design_context":
        text = first_text_content(response)
        assets = extract_design_context_assets(text)
        results = []
        for asset in assets:
            if asset_var and asset["name"] != asset_var:
                continue
            ext = extension_for_url(asset["url"], "bin")
            if only == "svg" and ext != "svg":
                continue
            if only == "raw" and ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                continue
            if only == "export" and ext == "svg":
                continue
            results.append(
                {
                    "kind": "design_context",
                    "name": asset["name"],
                    "url": asset["url"],
                    "filename": f"{asset['name']}.{ext}",
                }
            )
        return results
    return []


def slugify_query(query):
    slug = re.sub(r"[^a-z0-9]+", "-", (query or "").strip().lower())
    slug = slug.strip("-")
    return slug[:80] if slug else "query"


def cache_filename(file_key, action, node_hyphen=None, query=None, libraries_offset=None):
    if action == "search_design_system":
        return f"{file_key}__search__{slugify_query(query)}.json"
    if action == "get_libraries":
        if libraries_offset is not None:
            return f"{file_key}__libraries__offset{libraries_offset}.json"
        return f"{file_key}__libraries.json"
    suffix = node_hyphen if node_hyphen else "pages"
    return f"{file_key}__{suffix}.json"


def build_tool_args(action, file_key, node_hyphen, args):
    tool_args = {"fileKey": file_key}
    if node_hyphen and action not in ("get_libraries", "search_design_system"):
        tool_args["nodeId"] = node_hyphen.replace("-", ":")

    if action == "get_design_context":
        tool_args["clientLanguages"] = args.client_languages
        tool_args["clientFrameworks"] = args.client_frameworks
        tool_args["disableCodeConnect"] = False
        if not args.include_screenshot:
            tool_args["excludeScreenshot"] = True
    elif action == "search_design_system":
        tool_args["query"] = args.query
        tool_args["disableCodeConnect"] = args.disable_code_connect
        tool_args["includeComponents"] = args.include_components
        tool_args["includeVariables"] = args.include_variables
        tool_args["includeStyles"] = args.include_styles
        if args.include_library_keys:
            tool_args["includeLibraryKeys"] = args.include_library_keys
    elif action == "get_libraries" and args.libraries_offset is not None:
        tool_args["offset"] = args.libraries_offset
    elif action == "download_assets":
        if args.scale is not None:
            tool_args["defaultScale"] = args.scale
        tool_args.setdefault("defaultFormat", "png")

    return tool_args


def default_files_dir(cache_root, action, file_key, node_hyphen):
    return Path(cache_root) / "assets" / action / f"{file_key}__{node_hyphen}"


def save_asset_files(items, files_dir):
    saved = []
    for item in items:
        dest = files_dir / item["filename"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if "data" in item:
            raw = base64.b64decode(item["data"])
            dest.write_bytes(raw)
            size = len(raw)
        else:
            size = download_url(item["url"], dest)
        saved.append(
            {
                "kind": item.get("kind"),
                "name": item.get("name"),
                "url": item.get("url"),
                "path": str(dest),
                "bytes": size,
            }
        )
        print(f"asset: {dest} ({size} bytes)")
    return saved


def call_mcp_tool(server, action, tool_args):
    init, session = post(
        server,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "figma-cache-fetch", "version": "1.1.0"},
            },
        },
    )
    if not init or "error" in init:
        raise RuntimeError(f"MCP initialize failed: {init}")
    post(
        server,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session,
    )
    reply, _ = post(
        server,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": action, "arguments": tool_args},
        },
        session,
    )
    if not reply or "error" in reply:
        raise RuntimeError(f"MCP tools/call failed: {reply}")
    result = reply.get("result")
    if not result or result.get("isError"):
        raise RuntimeError(f"Tool returned an error: {result}")
    return result


def rebuild_index(cache_root):
    if not INDEX_SCRIPT.is_file():
        return
    index_result = subprocess.run(
        [
            sys.executable,
            str(INDEX_SCRIPT),
            "--cache-root",
            str(Path(cache_root).resolve()),
        ],
        capture_output=True,
        text=True,
    )
    if index_result.returncode == 0:
        index_line = index_result.stdout.strip()
        if index_line:
            print(index_line)
    else:
        print(index_result.stderr.strip(), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fetch a Figma Dev Mode MCP response, cache JSON, and optionally "
            "download asset files."
        )
    )
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--action", default="get_design_context", choices=ACTIONS)
    parser.add_argument("--server", default="http://127.0.0.1:3845/mcp")
    parser.add_argument("--include-screenshot", action="store_true")
    parser.add_argument("--client-languages", default="typescript,vue")
    parser.add_argument("--client-frameworks", default="vue,nuxt")
    parser.add_argument(
        "--save-files",
        action="store_true",
        help=(
            "Download asset bytes after fetch. For get_design_context: saves "
            "localhost asset URLs embedded in generated code. For "
            "download_assets: saves export/rawImages/svgAssets."
        ),
    )
    parser.add_argument(
        "--files-dir",
        help="Directory for --save-files (default: <cache-root>/assets/<action>/<key>)",
    )
    parser.add_argument(
        "--only",
        choices=("export", "raw", "svg"),
        help="When saving files, limit to one asset class.",
    )
    parser.add_argument(
        "--asset-var",
        help=(
            "For get_design_context saves: only download this const name "
            "(e.g. imgFrame)."
        ),
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        metavar="N",
        help=(
            "For download_assets: pass defaultScale to MCP (e.g. 2 for @2x "
            "web assets)."
        ),
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore existing cache JSON and re-fetch from MCP.",
    )
    parser.add_argument(
        "--no-refresh-stale",
        action="store_true",
        help=(
            "Keep cache entries older than 7 days instead of auto-refreshing "
            "(default: stale entries are re-fetched)."
        ),
    )
    parser.add_argument(
        "--query",
        help="Required for search_design_system — text query to search.",
    )
    parser.add_argument(
        "--libraries-offset",
        type=int,
        default=None,
        help="Optional pagination offset for get_libraries.",
    )
    parser.add_argument(
        "--disable-code-connect",
        action="store_true",
        help="Pass disableCodeConnect=true for search_design_system.",
    )
    parser.add_argument(
        "--no-include-components",
        action="store_true",
        help="Pass includeComponents=false for search_design_system.",
    )
    parser.add_argument(
        "--no-include-variables",
        action="store_true",
        help="Pass includeVariables=false for search_design_system.",
    )
    parser.add_argument(
        "--no-include-styles",
        action="store_true",
        help="Pass includeStyles=false for search_design_system.",
    )
    parser.add_argument(
        "--include-library-key",
        action="append",
        default=[],
        dest="include_library_keys",
        help=(
            "Repeatable library key filter for search_design_system "
            "(maps to includeLibraryKeys)."
        ),
    )
    args = parser.parse_args()
    args.include_components = not args.no_include_components
    args.include_variables = not args.no_include_variables
    args.include_styles = not args.no_include_styles

    file_key, node_hyphen = parse_figma_url(args.url)
    if not file_key:
        print(f"Could not parse fileKey from URL: {args.url}", file=sys.stderr)
        return 1
    if args.action == "search_design_system" and not args.query:
        print("--query is required for search_design_system", file=sys.stderr)
        return 1
    if args.action not in NODE_OPTIONAL_ACTIONS and not node_hyphen:
        print(
            f"URL has no node-id, required for {args.action}: {args.url}",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.cache_root) / args.action
    out_path = out_dir / cache_filename(
        file_key,
        args.action,
        node_hyphen=node_hyphen,
        query=args.query,
        libraries_offset=args.libraries_offset,
    )
    suffix = node_hyphen if node_hyphen else "pages"
    files_dir = (
        Path(args.files_dir)
        if args.files_dir
        else default_files_dir(args.cache_root, args.action, file_key, suffix)
    )

    cache_payload = None
    if out_path.exists() and not args.refresh:
        try:
            cache_payload = json.loads(out_path.read_text(encoding="utf-8"))
            cached_at = cache_payload.get("cachedAt", "unknown")
            if not args.no_refresh_stale and is_cache_stale(cached_at):
                print(
                    f"cache stale: {out_path} (cachedAt {cached_at}) — refreshing"
                )
                cache_payload = None
            else:
                print(f"cache hit: {out_path} (cachedAt {cached_at})")
        except (json.JSONDecodeError, OSError):
            cache_payload = None

    if cache_payload is None:
        tool_args = build_tool_args(args.action, file_key, node_hyphen, args)

        try:
            result = call_mcp_tool(args.server, args.action, tool_args)
        except (urllib.error.URLError, OSError) as exc:
            print(
                "Cannot reach the Figma Dev Mode MCP Server at "
                f"{args.server} ({exc}).\n"
                "Open the Figma desktop app and enable Preferences -> "
                "'Enable Dev Mode MCP Server', then retry.",
                file=sys.stderr,
            )
            return 1
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        out_dir.mkdir(parents=True, exist_ok=True)
        cache_payload = {
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            "url": args.url,
            "fileKey": file_key,
            "nodeId": node_hyphen,
            "action": args.action,
            "toolArgs": tool_args,
            "response": result,
        }
        if args.action == "search_design_system":
            cache_payload["searchQuery"] = args.query
        if args.action == "get_libraries" and args.libraries_offset is not None:
            cache_payload["librariesOffset"] = args.libraries_offset
        out_path.write_text(
            json.dumps(cache_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if "response" not in cache_payload:
            print("Cache write verification failed", file=sys.stderr)
            return 1
        print(f"written: {out_path} ({out_path.stat().st_size} bytes)")
        rebuild_index(args.cache_root)

    if not args.save_files:
        return 0

    if args.action not in ("get_design_context", "download_assets", "get_image"):
        print(
            f"--save-files is only supported for get_design_context, "
            f"get_image, and download_assets, not {args.action}",
            file=sys.stderr,
        )
        return 1

    try:
        items = assets_from_cached_payload(
            cache_payload,
            only=args.only,
            asset_var=args.asset_var,
        )
    except Exception as exc:
        print(f"Could not parse assets from cache: {exc}", file=sys.stderr)
        return 1

    if not items:
        print(
            "No assets found to save. For icons, try download_assets on the "
            "icon Frame node, or get_design_context on the parent frame and "
            "--asset-var imgFrame.",
            file=sys.stderr,
        )
        return 1

    try:
        saved = save_asset_files(items, files_dir)
    except (urllib.error.URLError, OSError) as exc:
        print(f"Asset download failed: {exc}", file=sys.stderr)
        return 1

    manifest_path = files_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "cachedAt": datetime.now(timezone.utc).isoformat(),
                "sourceCache": str(out_path),
                "assets": saved,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

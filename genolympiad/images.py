"""Images for the tasks: generate them through an image API, import them, or export the prompts."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import paths, tasks

log_ = logging.getLogger(__name__)

BACKENDS = ("openai", "gemini", "ark", "bfl", "openrouter", "leonardo", "http")
KEY_ENV = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "ark": "ARK_API_KEY",
           "bfl": "BFL_API_KEY", "openrouter": "OPENROUTER_API_KEY",
           "leonardo": "LEONARDO_API_KEY"}
_BY_PREFIX = [("gpt-image", "openai"), ("dall-e", "openai"), ("gpt", "openai"),
              ("gemini", "gemini"), ("imagen", "gemini"), ("seedream", "ark"),
              ("doubao", "ark"), ("flux", "bfl"), ("lucid", "leonardo"),
              ("phoenix", "leonardo")]
_RETRY_STATUS = (408, 429, 500, 502, 503, 522, 524)
PICTURE_TYPES = (".png", ".jpg", ".jpeg", ".webp")


def backend_for(model):
    """The image API a model name belongs to, or None when the name does not say."""
    name = str(model).split("/")[-1].strip().lower()
    for prefix, backend in _BY_PREFIX:
        if name.startswith(prefix):
            return backend
    return None


def size_for(aspect_ratio, default="1024x1024"):
    """The image size for an aspect ratio such as "3:2"."""
    if not aspect_ratio:
        return default
    w, h = (float(x) for x in str(aspect_ratio).split(":"))
    if w / h > 1.15:
        return "1536x1024"
    if h / w > 1.15:
        return "1024x1536"
    return "1024x1024"


def read_key(env_var, key_file=None):
    """An API key from the environment, else from the first line of key_file; never printed."""
    if os.environ.get(env_var):
        return os.environ[env_var].strip()
    if key_file:
        with io.open(key_file, encoding="utf-8") as fh:
            value = fh.read().strip()
        if not value:
            raise ValueError("the key file %s is empty" % key_file)
        return value
    return None


def load_env(path=None):
    """Set NAME=value lines of the .env file in the repository root that the environment lacks."""
    path = path or os.path.join(paths.REPO_ROOT, ".env")
    if not os.path.isfile(path):
        return
    with io.open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name, value = name.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1].strip()
            if name and name not in os.environ:
                os.environ[name] = value


class Limits:
    """Which tasks are not generated: prompts longer than the context length, and listed ids."""

    def __init__(self, context_length=None, tokenizer=None, not_generated_ids=frozenset(),
                 not_generated_file=None):
        if context_length is not None and tokenizer is None:
            raise ValueError("a context length needs a tokenizer to count prompt tokens")
        self.context_length = context_length
        self.tokenizer = tokenizer
        self.not_generated_ids = frozenset(not_generated_ids)
        self.not_generated_file = not_generated_file

    def as_dict(self):
        """The limits as written into generation.json."""
        tok = self.tokenizer if isinstance(self.tokenizer, (str, type(None))) else "custom"
        return {"context_length": self.context_length, "tokenizer": tok,
                "not_generated_file": self.not_generated_file}


_TOKENIZERS = {}


def count_tokens(prompt, tokenizer):
    """Tokens in the prompt for a Hugging Face tokenizer name or a callable; None without one."""
    if tokenizer is None:
        return None
    if callable(tokenizer):
        return int(tokenizer(prompt))
    if tokenizer not in _TOKENIZERS:
        from transformers import AutoTokenizer
        _TOKENIZERS[tokenizer] = AutoTokenizer.from_pretrained(tokenizer)
    return len(_TOKENIZERS[tokenizer](prompt, add_special_tokens=True)["input_ids"])


def load_id_list(path):
    """Task ids from a text file (one per line) or a JSON list."""
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    if text.lstrip().startswith("["):
        return {str(x) for x in json.loads(text)}
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check(entry, prompt, limits):
    """The ledger entry for a task that will not be generated, or None."""
    rec = {"chars": len(prompt)}
    tokens = count_tokens(prompt, limits.tokenizer)
    if tokens is not None:
        rec["tokens"] = tokens
    if entry["task_id"] in limits.not_generated_ids:
        return dict(rec, status="not_generated", reason="listed_not_generated"), rec
    if limits.context_length is not None and tokens > limits.context_length:
        return dict(rec, status="not_generated", reason="prompt_longer_than_context_length"), rec
    return None, rec


def export_prompts(entries, path, tokenizer=None):
    """Write one JSON line per task: id, axis, prompt, aspect ratio, size and length; returns n."""
    n = 0
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        for e in entries:
            prompt = tasks.prompt_of(e)
            ratio = tasks.aspect_ratio_of(e)
            row = {"task_id": e["task_id"], "axis": e["axis"], "prompt": prompt,
                   "aspect_ratio": ratio, "size": size_for(ratio), "chars": len(prompt)}
            if tokenizer is not None:
                row["tokens"] = count_tokens(prompt, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def _ledger_path(run_dir):
    return os.path.join(run_dir, "generation.json")


def load_ledger(run_dir):
    """generation.json of a run, or an empty ledger."""
    p = _ledger_path(run_dir)
    if not os.path.exists(p):
        return {"tasks": {}}
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _write_ledger(run_dir, ledger):
    os.makedirs(run_dir, exist_ok=True)
    p = _ledger_path(run_dir)
    with io.open(p + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(p + ".tmp", p)


def _save_png(img, path):
    from PIL import Image
    if not isinstance(img, Image.Image):
        raise TypeError("the backend returned no image")
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path + ".tmp.png", format="PNG")
    os.replace(path + ".tmp.png", path)


def _open(raw):
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    img.load()
    return img


def _post_retry(do, what, tries=4, wait=8):
    """Call `do()` until it gives HTTP 200, retrying on rate limits and server errors."""
    last = None
    for attempt in range(tries):
        r = do()
        if r.status_code in (200, 201):
            return r
        last = "%s: %s" % (r.status_code, r.text[:160])
        if r.status_code in _RETRY_STATUS:
            time.sleep(wait * (attempt + 1))
            continue
        break
    raise RuntimeError("%s failed: %s" % (what, last))


def _openai(route, prompt, ratio, key, cfg):
    import requests
    r = _post_retry(lambda: requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": "Bearer " + key},
        json={"model": route, "prompt": prompt, "size": size_for(ratio, default="auto")},
        timeout=420), "OpenAI images")
    return _open(base64.b64decode(r.json()["data"][0]["b64_json"]))


def _openrouter(route, prompt, ratio, key, cfg):
    import requests
    body = {"model": route, "prompt": prompt}
    if ratio:
        body["aspect_ratio"] = ratio
    r = _post_retry(lambda: requests.post(
        "https://openrouter.ai/api/v1/images",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json=body, timeout=420), "OpenRouter images")
    data = (r.json().get("data") or [{}])[0]
    b64 = data.get("b64_json") or data.get("image") or ""
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return _open(base64.b64decode(b64))


def _gemini(route, prompt, ratio, key, cfg):
    import requests
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % route
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
    last = None
    for attempt in range(5):
        r = _post_retry(lambda: requests.post(
            url, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=body, timeout=420), "Gemini images", wait=12)
        cands = r.json().get("candidates") or []
        parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
        for p in parts:
            if "inlineData" in p:
                return _open(base64.b64decode(p["inlineData"]["data"]))
        last = "the answer carried no image"
        time.sleep(6 * (attempt + 1))
    raise RuntimeError("Gemini images failed: %s" % last)


def _ark(route, prompt, ratio, key, cfg):
    import requests
    url = "https://ark.ap-southeast.bytepluses.com/api/v3/images/generations"
    last = None
    for size in (size_for(ratio), "1K"):
        try:
            r = _post_retry(lambda: requests.post(
                url, headers={"Authorization": "Bearer " + key,
                              "Content-Type": "application/json"},
                json={"model": route, "prompt": prompt, "response_format": "url", "size": size,
                      "stream": False, "watermark": False}, timeout=420), "Ark images", wait=10)
        except RuntimeError as e:
            last = str(e)
            continue
        data = (r.json().get("data") or [{}])[0]
        if data.get("b64_json"):
            return _open(base64.b64decode(data["b64_json"]))
        if data.get("url"):
            got = requests.get(data["url"], timeout=120)
            got.raise_for_status()
            return _open(got.content)
        last = "the answer carried no image"
    raise RuntimeError("Ark images failed: %s" % last)


def _bfl(route, prompt, ratio, key, cfg):
    import requests
    head = {"x-key": key, "Content-Type": "application/json"}
    body = {"prompt": prompt, "output_format": "png"}
    if ratio:
        body["aspect_ratio"] = ratio
    r = _post_retry(lambda: requests.post("https://api.bfl.ai/v1/" + route.lstrip("/"),
                                          headers=head, json=body, timeout=180), "BFL images")
    job = r.json()
    url = job.get("polling_url") or ("https://api.bfl.ai/v1/get_result?id=" + job["id"])
    deadline = time.time() + 600
    while time.time() < deadline:
        g = requests.get(url, headers={"x-key": key}, timeout=60)
        doc = g.json() if g.status_code == 200 else {}
        status = (doc.get("status") or "").lower()
        if status == "ready":
            sample = (doc.get("result") or {}).get("sample")
            return _open(requests.get(sample, timeout=300).content)
        if status in ("error", "failed", "content moderated", "request moderated"):
            raise RuntimeError("BFL job %s: %s" % (status, str(doc)[:160]))
        time.sleep(3)
    raise RuntimeError("the BFL job did not finish within ten minutes")


_LEONARDO = "https://cloud.leonardo.ai/api/rest/"
_LEONARDO_MODELS = {}
_LEONARDO_LOCK = threading.Lock()


def _leonardo_name(text):
    return re.sub(r"v(?=\d)", "", re.sub(r"[^a-z0-9.]", "", str(text).lower()))


def _leonardo_schema(route, key):
    """The parameter schema Leonardo publishes for a model, or {} when it lists none."""
    import requests
    with _LEONARDO_LOCK:
        if not _LEONARDO_MODELS:
            r = _post_retry(lambda: requests.get(_LEONARDO + "v2/models",
                                                 headers={"Authorization": "Bearer " + key},
                                                 timeout=60), "Leonardo models")
            for m in r.json().get("productionApiAvailableModels") or []:
                _LEONARDO_MODELS[_leonardo_name(m.get("name"))] = m.get("parameters") or {}
    return (_LEONARDO_MODELS.get(_leonardo_name(route)) or {}).get("properties") or {}


def _fit_side(value, rule):
    step = int(rule.get("multipleOf") or 8)
    low, high = int(rule.get("minimum") or step), int(rule.get("maximum") or value)
    return max(low, min(high, int(round(value / float(step))) * step))


def leonardo_size(ratio, schema):
    """Width and height for the task's aspect ratio, kept inside the model's allowed range."""
    wide, high = (int(x) for x in size_for(ratio).split("x"))
    w_rule, h_rule = schema.get("width") or {}, schema.get("height") or {}
    shrink = min(1.0, float(w_rule.get("maximum") or wide) / wide,
                 float(h_rule.get("maximum") or high) / high)
    return _fit_side(wide * shrink, w_rule), _fit_side(high * shrink, h_rule)


def _leonardo_error(doc):
    if isinstance(doc, list):
        doc = doc[0] if doc and isinstance(doc[0], dict) else {}
    details = ((doc.get("extensions") or {}).get("details") or {})
    return details.get("code"), details.get("message") or doc.get("message") or doc.get("error")


def _leonardo(route, prompt, ratio, key, cfg):
    import requests
    schema = _leonardo_schema(route, key)
    limit = (schema.get("prompt") or {}).get("maxLength")
    if limit and len(prompt) > int(limit):
        raise ValueError("the prompt has %d characters and %s takes at most %d"
                         % (len(prompt), route, int(limit)))
    wide, high = leonardo_size(ratio, schema)
    head = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    body = {"model": route, "public": False,
            "parameters": {"prompt": prompt, "width": wide, "height": high, "quantity": 1,
                           "prompt_enhance": "OFF", "style_ids": []}}
    job, last = None, None
    for attempt in range(5):
        r = _post_retry(lambda: requests.post(_LEONARDO + "v2/generations", headers=head,
                                              json=body, timeout=180), "Leonardo images")
        doc = r.json()
        if isinstance(doc, dict):
            job = (doc.get("generate") or doc).get("generationId")
        if job:
            break
        code, last = _leonardo_error(doc)
        last = last or str(doc)[:160]
        if code == "VALIDATION_ERROR":
            raise RuntimeError("Leonardo refused the request: %s" % last)
        time.sleep(15 * (attempt + 1))
    if not job:
        raise RuntimeError("Leonardo images failed: %s" % str(last)[:160])
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(3)
        g = requests.get(_LEONARDO + "v1/generations/" + job, headers=head, timeout=60)
        gen = (g.json().get("generations_by_pk") or {}) if g.status_code == 200 else {}
        status = str(gen.get("status") or "").upper()
        if status == "COMPLETE":
            pictures = gen.get("generated_images") or []
            if not pictures:
                raise RuntimeError("the Leonardo job finished with no image")
            return _open(requests.get(pictures[0]["url"], timeout=300).content)
        if status == "FAILED":
            raise RuntimeError("Leonardo job failed: %s" % str(gen)[:160])
    raise RuntimeError("the Leonardo job did not finish within ten minutes")


SHAPES = {
    "openai": {"request": {"model": "${MODEL}", "prompt": "${PROMPT}", "size": "${SIZE}", "n": 1},
               "response": {"image_base64": "data[0].b64_json", "image_url": "data[0].url"}},
    "simple": {"request": {"prompt": "${PROMPT}", "width": "${WIDTH}", "height": "${HEIGHT}"},
               "response": {"image_base64": "image_base64", "image_url": "image_url"}},
}


def _dig(doc, path):
    node = doc
    for part in str(path).replace("]", "").replace("[", ".").split("."):
        if part == "":
            continue
        if isinstance(node, list):
            if not part.isdigit() or int(part) >= len(node):
                return None
            node = node[int(part)]
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
        if node is None:
            return None
    return node


_PLACEHOLDER = re.compile(r"\$\{(\w+)\}")


def _fill(template, values, unset=""):
    """Fill ${NAME} from the task, else a non-empty environment variable, else unset (None keeps it)."""
    if isinstance(template, dict):
        return {k: _fill(v, values, unset) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill(v, values, unset) for v in template]
    if isinstance(template, str):
        whole = _PLACEHOLDER.fullmatch(template.strip())
        if whole and whole.group(1) in values:
            return values[whole.group(1)]

        def one(m):
            if m.group(1) in values:
                return str(values[m.group(1)])
            return os.environ.get(m.group(1)) or (m.group(0) if unset is None else unset)
        return _PLACEHOLDER.sub(one, template)
    return template


def _http(route, prompt, ratio, key, cfg):
    import requests
    if not cfg or not (cfg.get("endpoint") or "").strip():
        raise RuntimeError("the http backend needs --backend-config")
    shape = SHAPES.get(str(cfg.get("format", "openai")).lower(), SHAPES["openai"])
    size = size_for(ratio)
    wide, high = (int(x) for x in size.lower().split("x"))
    values = {"MODEL": route, "PROMPT": prompt, "SIZE": size, "WIDTH": wide, "HEIGHT": high}
    body = _fill(cfg.get("request") or shape["request"], values)
    headers = {k: v for k, v in _fill(cfg.get("headers") or {}, values, unset=None).items()
               if not (isinstance(v, str) and _PLACEHOLDER.search(v))}
    headers.setdefault("Content-Type", "application/json")
    where = dict(shape["response"], **(cfg.get("response") or {}))
    timeout = float(cfg.get("timeout") or 420)
    r = _post_retry(lambda: requests.request(str(cfg.get("method") or "POST").upper(),
                                             cfg["endpoint"], headers=headers, json=body,
                                             timeout=timeout),
                    "the endpoint", tries=int(cfg.get("retries") or 5))
    doc = r.json()
    b64 = _dig(doc, where["image_base64"]) if where.get("image_base64") else None
    link = _dig(doc, where["image_url"]) if where.get("image_url") else None
    if b64:
        if str(b64).startswith("data:"):
            b64 = str(b64).split(",", 1)[1]
        return _open(base64.b64decode(b64))
    if link:
        return _open(requests.get(link, timeout=timeout).content)
    raise RuntimeError("the reply carried no image: %s" % str(doc)[:160])


_CALLS = {"openai": _openai, "openrouter": _openrouter, "gemini": _gemini, "ark": _ark,
          "bfl": _bfl, "leonardo": _leonardo, "http": _http}


def register_backend(name, fn):
    """Add an image backend: fn(task_id, prompt, size, model) returns a PIL image; needs no key."""
    def call(route, prompt, ratio, key, cfg):
        return fn(cfg["task_id"], prompt, size_for(ratio), route)
    _CALLS[name] = call


def backend_names():
    """Names of every image backend this process knows."""
    return tuple(_CALLS)


def load_http_config(path):
    """The description of your own HTTP image API from a JSON file; None without a file."""
    if not path:
        return None
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def generate(entries, run_dir, *, backend, model, limits, workers=8, key=None, http_config=None,
             route=None):
    """Make one image per task into run_dir/images and write generation.json.

    Returns the ledger with one more key, made_in_this_run, that is not written to the file.
    """
    if backend not in _CALLS:
        raise ValueError("unknown backend %r; choose one of %s" % (backend, ", ".join(BACKENDS)))
    if backend in KEY_ENV and not key:
        raise ValueError("no key for the %s image API: set %s or pass --key-file"
                         % (backend, KEY_ENV[backend]))
    ledger = load_ledger(run_dir)
    ledger.update(model=model, backend=backend, limits=limits.as_dict())
    ledger.setdefault("unmatched_files", [])
    book = ledger["tasks"]
    lock = threading.Lock()
    pending = []
    for e in entries:
        prompt = tasks.prompt_of(e)
        skip, rec = _check(e, prompt, limits)
        if skip:
            book[e["task_id"]] = skip
            continue
        rel = "images/%s.png" % e["task_id"]
        old = book.get(e["task_id"]) or {}
        if (old.get("status") in ("made", "imported") and old.get("prompt_sha256") == _sha256(prompt)
                and os.path.exists(os.path.join(run_dir, rel))):
            continue
        pending.append((e, prompt, rec, rel))

    def one(item):
        e, prompt, rec, rel = item
        cfg = dict(http_config or {}, task_id=e["task_id"])
        try:
            img = _CALLS[backend](route or model, prompt, tasks.aspect_ratio_of(e), key, cfg)
            _save_png(img, os.path.join(run_dir, rel))
            out = dict(rec, status="made", file=rel, prompt_sha256=_sha256(prompt))
        except (RuntimeError, ValueError, OSError, KeyError, TypeError) as err:
            log_.warning("generation failed for %s: %s", e["task_id"], err)
            out = dict(rec, status="not_generated", reason="generation_failed",
                       error=str(err)[:200])
        with lock:
            book[e["task_id"]] = out
        return out["status"]

    made = 0
    if pending:
        from tqdm import tqdm
        bar = tqdm(total=len(pending), desc="images", unit="task", dynamic_ncols=True)
        with ThreadPoolExecutor(max_workers=max(1, int(workers))) as ex, bar:
            for status in ex.map(one, pending):
                made += status == "made"
                bar.update(1)
    _write_ledger(run_dir, ledger)
    return dict(ledger, made_in_this_run=made)


def import_folder(folder, entries, run_dir, *, limits, log=print):
    """Copy <folder>/<task_id>.(png|jpg|jpeg|webp) into run_dir/images; returns the ledger."""
    from PIL import Image
    ledger = load_ledger(run_dir)
    ledger.update(model=ledger.get("model"), backend="images", limits=limits.as_dict())
    book = ledger["tasks"]
    seen = set()
    for e in entries:
        prompt = tasks.prompt_of(e)
        skip, rec = _check(e, prompt, limits)
        src = next((os.path.join(folder, e["task_id"] + ext) for ext in PICTURE_TYPES
                    if os.path.exists(os.path.join(folder, e["task_id"] + ext))), None)
        if src:
            seen.add(os.path.basename(src))
        if skip:
            book[e["task_id"]] = skip
            continue
        if not src:
            book[e["task_id"]] = dict(rec, status="not_generated", reason="no_image_supplied")
            continue
        rel = "images/%s.png" % e["task_id"]
        with Image.open(src) as img:
            img.load()
            _save_png(img, os.path.join(run_dir, rel))
        book[e["task_id"]] = dict(rec, status="imported", file=rel, prompt_sha256=_sha256(prompt))
    ledger["unmatched_files"] = sorted(
        f for f in os.listdir(folder) if f.lower().endswith(PICTURE_TYPES) and f not in seen)
    _write_ledger(run_dir, ledger)
    n_in = sum(1 for e in entries if book[e["task_id"]]["status"] == "imported")
    log("  imported %d image(s) from %s" % (n_in, os.path.normpath(folder)))
    return ledger

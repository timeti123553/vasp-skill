#!/usr/bin/env python3
"""Ingest a VASP article / note / web link into the skill's knowledge base.

Deps: L0 (standard library); PDF additionally needs `pypdf`

Link hygiene: Zhihu's `link.zhihu.com/?target=` redirects are unwrapped to the
real URL, and its auto-generated `zhida.zhihu.com/search` links (one per keyword,
several hundred characters each) are flattened to plain text.

Accepts:
  * a local file: .txt .md .log .py .rst .html (and .pdf with pypdf)
  * an http(s) link: HTML pages are converted to markdown-ish text and their
    citation meta tags are captured; PDF links are downloaded and parsed

Output: <skill>/references/articles/<YYYYMMDD>-<slug>.md with a metadata header
        (source file or URL, title, authors / journal / year / DOI, fetch time,
        tags). Existing files are never overwritten.

Usage:
  python add_article.py paper.pdf --tag COHP
  python add_article.py https://example.org/post --tag "LOBSTER"
  python add_article.py https://doi.org/10.1103/PhysRevB.109.000000 --proxy http://127.0.0.1:7890
  python add_article.py --selftest

Exit codes: 0 = ingested; 1 = nothing ingestible (empty page/body);
            2 = usage, missing file, network, or dependency error.
"""

import argparse
import datetime
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 (compatible; dsh-vasp-skill)")


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_url(s):
    return bool(re.match(r"^https?://", (s or "").strip(), re.I))


def slugify(stem):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", stem or "")
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:80] or "article"


# --------------------------------------------------------------------------- #
# fetching
# --------------------------------------------------------------------------- #

def fetch(url, timeout=30.0, proxy=None):
    """Return (raw_bytes, content_type, charset, final_url). Raises on failure."""
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.5",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        opener = urllib.request.build_opener()   # honours http_proxy/https_proxy/all_proxy
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read()
        ctype = (resp.headers.get_content_type() or "").lower()
        charset = resp.headers.get_content_charset()
        final = resp.geturl()
    return raw, ctype, charset, final


def decode_bytes(raw, charset=None):
    encodings = ([charset] if charset else []) + ["utf-8", "utf-8-sig", "gb18030", "big5", "latin-1"]
    for enc in encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


# --------------------------------------------------------------------------- #
# html -> markdown-ish text
# --------------------------------------------------------------------------- #

class HtmlToMarkdown(HTMLParser):
    """Very small HTML reader: keeps headings, paragraphs, list items and pre.

    Drops script/style/noscript/svg/template/iframe/form/nav/footer/header and
    collects a few bibliographic <meta> keys when a page exposes them.
    """

    SKIP = {"script", "style", "noscript", "svg", "template", "iframe", "form",
            "nav", "footer", "header", "button", "select"}
    HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ",
                "h5": "##### ", "h6": "###### "}
    BLOCKS = {"p", "div", "section", "article", "blockquote", "tr", "br", "pre", "table", "ul", "ol"}
    META_KEYS = {"citation_title", "citation_author", "citation_journal_title",
                 "citation_publication_date", "citation_doi", "citation_pdf_url",
                 "description", "og:title", "og:description", "author", "keywords"}

    def __init__(self, base_url=None):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.base_url = base_url
        self._link_stack = []
        self.out = []
        self.buf = []
        self.skip = 0
        self.title = None
        self.meta = {}
        self._in_title = False
        self._prefix = ""

    def _flush(self, prefix=""):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text:
            self.out.append(prefix + text)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "a":
            href = ""
            for k, v in attrs:
                if k.lower() == "href":
                    href = (v or "").strip()
            if "link.zhihu.com" in href:
                _t = parse_qs(urlparse(href).query).get("target")
                if _t and _t[0].startswith("http"):
                    href = _t[0]
            if "zhida.zhihu.com/search" in href:
                # Zhihu auto-wraps every keyword in an in-site search link;
                # it carries no citation value, so keep the text and drop the URL.
                self._link_stack.append(None)
                return
            if href and not href.lower().startswith(("javascript:", "#")):
                if self.base_url:
                    href = urljoin(self.base_url, href)
                self._link_stack.append((len(self.buf), href))
            else:
                self._link_stack.append(None)
            return
        if tag == "meta":
            d = dict((k.lower(), (v or "")) for k, v in attrs)
            key = (d.get("name") or d.get("property") or "").lower()
            val = (d.get("content") or "").strip()
            if key in self.META_KEYS and val:
                self.meta.setdefault(key, []).append(val)
            return
        if tag == "title":
            self._in_title = True
        elif tag in self.HEADINGS:
            self._flush()
            self._prefix = self.HEADINGS[tag]
        elif tag == "li":
            self._flush()
            self._prefix = "- "
        elif tag in self.BLOCKS:
            self._flush()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP:
            if self.skip:
                self.skip -= 1
            return
        if self.skip:
            return
        if tag == "a":
            if self._link_stack:
                mark = self._link_stack.pop()
                if mark is not None:
                    start, href = mark
                    text = re.sub(r"\s+", " ", "".join(self.buf[start:])).strip()
                    del self.buf[start:]
                    self.buf.append("[%s](%s)" % (text, href) if text else href)
            return
        if tag == "title":
            self._in_title = False
        elif tag in self.HEADINGS or tag == "li":
            self._flush(self._prefix)
            self._prefix = ""
        elif tag in self.BLOCKS:
            self._flush()

    def handle_data(self, data):
        if self.skip:
            return
        if self._in_title:
            self.title = (self.title or "") + data
        elif data.strip():
            self.buf.append(data)

    def close(self):
        HTMLParser.close(self)
        self._flush(self._prefix)
        self._prefix = ""

    def markdown(self):
        text = "\n\n".join(x for x in self.out if x.strip())
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def first(self, key):
        vals = self.meta.get(key)
        return vals[0] if vals else None


def html_to_markdown(html_text, base_url=None):
    """Return (markdown_text, meta_dict, title).

    Title precedence: citation_title -> og:title -> <title> -> first markdown
    heading. The last fallback matters for JS-heavy pages (e.g. WeChat) whose
    <title> is empty, where the real title is only the body's first heading.
    """
    p = HtmlToMarkdown(base_url=base_url)
    try:
        p.feed(html_text)
        p.close()
    except Exception:                                  # never fail ingestion on markup
        pass
    md = p.markdown()
    title = (p.first("citation_title") or p.first("og:title")
             or (p.title or "").strip() or None)
    if not title:
        for line in md.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    return md, p.meta, title


# --------------------------------------------------------------------------- #
# local files
# --------------------------------------------------------------------------- #

def read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "PDF ingestion needs `pypdf`. Run e.g. `pip install pypdf`, "
            "or convert the PDF to text/markdown and pass that file instead.")
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_file(path):
    """Return (body, kind, meta, title) for a local file."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return read_pdf(path), "pdf", {}, None
    for enc in ("utf-8", "utf-8-sig", "gbk", "big5", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError("Could not decode %s with utf-8/gbk/big5." % path)
    if ext in (".html", ".htm"):
        body, meta, title = html_to_markdown(text)
        return body, "html", meta, title
    return text, "text", {}, None


# --------------------------------------------------------------------------- #
# ingest
# --------------------------------------------------------------------------- #

def build_header(title, meta, source_label, kind, tags, n_chars, fetched_at=None):
    lines = ["# %s" % (title or "untitled"), ""]
    lines.append("- 来源: `%s`" % source_label)
    lines.append("- 类型: %s" % kind)
    if fetched_at:
        lines.append("- 抓取时间: %s" % fetched_at)
    if meta.get("citation_author"):
        lines.append("- 作者: %s" % "; ".join(meta["citation_author"]))
    elif meta.get("author"):
        lines.append("- 作者: %s" % "; ".join(meta["author"]))
    journal = (meta.get("citation_journal_title") or [None])[0]
    year = (meta.get("citation_publication_date") or [None])[0]
    if journal or year:
        lines.append("- 出处: %s%s" % (journal or "", (" (%s)" % year) if year else ""))
    if meta.get("citation_doi"):
        lines.append("- DOI: %s" % meta["citation_doi"][0])
    if tags:
        lines.append("- 标签: %s" % ", ".join(tags))
    lines.append("- 正文字数: %d" % n_chars)
    lines += ["", "---", ""]
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="Ingest a VASP article (file or URL) into the skill knowledge base.")
    p.add_argument("source", nargs="?", help="local file path or http(s) URL")
    p.add_argument("--tag", action="append", default=[], help="tag(s), repeatable")
    p.add_argument("--outdir", default=None, help="output dir (default: <skill>/references/articles)")
    p.add_argument("--no-header", action="store_true", help="append body only, without the metadata header")
    p.add_argument("--proxy", default=None, help="proxy for URL fetches, e.g. http://127.0.0.1:7890")
    p.add_argument("--source-url", default=None,
                   help="record this URL as the source instead of the local file name")
    p.add_argument("--timeout", type=float, default=30.0, help="fetch timeout in seconds (default 30)")
    p.add_argument("--selftest", action="store_true", help="run the built-in self test and exit")
    args = p.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.source:
        print("Error: a file path or URL is required", file=sys.stderr)
        return 2

    meta = {}
    title = None
    fetched_at = None

    if is_url(args.source):
        try:
            raw, ctype, charset, final = fetch(args.source, args.timeout, args.proxy)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            print("Error: fetch failed for %s: %s" % (args.source, exc), file=sys.stderr)
            print("Hint: behind a proxy pass --proxy http://host:port "
                  "(or set http_proxy/https_proxy/all_proxy).", file=sys.stderr)
            return 2
        source_label = final or args.source
        fetched_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if ctype == "application/pdf" or final.lower().endswith(".pdf"):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            try:
                tmp.write(raw)
                tmp.close()
                body = read_pdf(tmp.name)
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            kind = "pdf (url)"
        else:
            text = decode_bytes(raw, charset)
            looks_html = ctype in ("text/html", "application/xhtml+xml") or \
                "<html" in text[:4096].lower() or "<!doctype html" in text[:4096].lower()
            if looks_html:
                body, meta, title = html_to_markdown(text, base_url=final)
                kind = "html (url)"
            else:
                body, kind = text, "text (url)"
    else:
        src = os.path.abspath(args.source)
        if not os.path.isfile(src):
            print("Error: no such file: %s" % src, file=sys.stderr)
            return 2
        try:
            body, kind, meta, title = read_file(src)
        except RuntimeError as exc:
            print("Error: %s" % exc, file=sys.stderr)
            return 2
        source_label = args.source_url or os.path.basename(src)

    body = (body or "").strip()
    if not body:
        print("Nothing ingestible in %s (empty body)" % args.source)
        return 1

    stem = slugify(title or os.path.splitext(os.path.basename(source_label))[0])
    outdir = args.outdir or os.path.join(skill_root(), "references", "articles")
    os.makedirs(outdir, exist_ok=True)

    today = datetime.date.today().strftime("%Y%m%d")
    base = "%s-%s" % (today, stem)
    target = os.path.join(outdir, base + ".md")
    n = 2
    while os.path.exists(target):
        target = os.path.join(outdir, "%s_%d.md" % (base, n))
        n += 1

    if args.no_header:
        text = body + "\n"
    else:
        header = build_header(title, meta, source_label, kind, args.tag, len(body), fetched_at)
        text = header + body + "\n"

    with open(target, "w", encoding="utf-8") as f:
        f.write(text)

    print("Ingested into: %s" % target)
    print("  title : %s" % (title or stem))
    print("  kind  : %s" % kind)
    print("  tags  : %s" % (", ".join(args.tag) if args.tag else "none"))
    print("  chars : %d" % len(body))
    print("Next: distill reusable error/parameter knowledge into "
          "references/errors.md or references/workflows.md, then search with "
          "python scripts/search_kb.py \"<keyword>\"")
    return 0


# --------------------------------------------------------------------------- #
# self test (no network)
# --------------------------------------------------------------------------- #

SELFTEST_HTML = """<!doctype html>
<html><head>
<title>COHP analysis with LOBSTER</title>
<meta name="citation_title" content="Bonding analysis in FeO">
<meta name="citation_author" content="A. Author">
<meta name="citation_author" content="B. Author">
<meta name="citation_journal_title" content="Phys. Rev. B">
<meta name="citation_publication_date" content="2024">
<meta name="citation_doi" content="10.1103/PhysRevB.109.000000">
<script>var secret = 1;</script><style>p { color: red }</style>
</head><body>
<nav>menu should vanish</nav>
<h1>Introduction</h1>
<p>COHP shows bonding states below E_F.</p>
<ul><li>Use ICOHP for comparison</li><li>Check the pair list</li></ul>
<pre>cohpGenerator from 1.5 to 3.0</pre>
<p>see <a href="https://example.org/x">the tutorial</a> and <a href="javascript:void(0)">nothing</a></p>
</body></html>
"""


SELFTEST_HTML_NO_TITLE = ("<html><body><h1>Only a heading</h1>"
                          "<p>body text</p></body></html>")


def selftest():
    md, meta, title = html_to_markdown(SELFTEST_HTML)
    md2, _meta2, title2 = html_to_markdown(SELFTEST_HTML_NO_TITLE)
    checks = [
        ("title from citation_title", title == "Bonding analysis in FeO"),
        ("title falls back to first heading", title2 == "Only a heading"),
        ("h1 kept", "# Introduction" in md),
        ("paragraph kept", "bonding states below E_F" in md),
        ("list item kept", "- Use ICOHP for comparison" in md),
        ("pre kept", "cohpGenerator from 1.5 to 3.0" in md),
        ("script dropped", "secret" not in md),
        ("style dropped", "color: red" not in md),
        ("nav dropped", "menu should vanish" not in md),
        ("authors captured", len(meta.get("citation_author", [])) == 2),
        ("doi captured", meta.get("citation_doi", [None])[0] == "10.1103/PhysRevB.109.000000"),
        ("url detection", is_url("https://a.b/c") and not is_url("C:/tmp/a.md")),
        ("link kept as markdown", "[the tutorial](https://example.org/x)" in md),
        ("javascript link dropped", "javascript" not in md and "nothing" in md),
        ("relative link resolved", "[rel](https://host.example/rel/path)" in html_to_markdown(
            '<p><a href="/rel/path">rel</a></p>', base_url="https://host.example/dir/page")[0]),
        ("zhihu redirect unwrapped", "[x](https://example.org/a)" in html_to_markdown(
            '<p><a href="https://link.zhihu.com/?target=https%3A//example.org/a">x</a></p>')[0]),
        ("zhida search link flattened", html_to_markdown(
            '<p><a href="https://zhida.zhihu.com/search?content_id=1&amp;zd_token=abc">波恩</a></p>')[0] == "波恩"),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("selftest FAIL: %s" % ", ".join(failed))
        return 1

    with tempfile.TemporaryDirectory() as d:
        # local .html file through the same path main() uses
        html_path = os.path.join(d, "page.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(SELFTEST_HTML)
        rc = main([html_path, "--outdir", d, "--tag", "selftest",
                   "--source-url", "https://example.org/post"])
        if rc != 0:
            print("selftest FAIL: local html ingest returned %s" % rc)
            return 1
        produced = [x for x in os.listdir(d) if x.endswith(".md")]
        if len(produced) != 1:
            print("selftest FAIL: expected 1 markdown file, got %s" % produced)
            return 1
        with open(os.path.join(d, produced[0]), "r", encoding="utf-8") as f:
            head = f.read()
        for needle in ("# Bonding analysis in FeO", "- 来源: `https://example.org/post`",
                       "- 标签: selftest",
                       "- DOI: 10.1103/PhysRevB.109.000000",
                       "- 作者: A. Author; B. Author"):
            if needle not in head:
                print("selftest FAIL: missing in header: %s" % needle)
                return 1

        # plain text file
        txt_path = os.path.join(d, "notes.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("EDIFFG = -0.02\n")
        if main([txt_path, "--outdir", d]) != 0:
            print("selftest FAIL: plain text ingest failed")
            return 1

        # empty file must be a clean 'nothing ingestible', not a crash
        empty_path = os.path.join(d, "empty.txt")
        open(empty_path, "w").close()
        if main([empty_path, "--outdir", d]) != 1:
            print("selftest FAIL: empty input should return 1")
            return 1

    print("selftest OK: html->markdown, meta capture, file ingest, empty-input path")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)

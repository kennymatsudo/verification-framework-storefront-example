"""The shop as a browser without JavaScript sees it: submit its forms and read the HTML it serves.

The shop's pages are plain HTML forms, so a form POST here is the same request the "Add to cart" and
"Remove" buttons send. Page reads parse the served HTML directly; they never call the shop's code.
"""

import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

import connection

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def _request(path, form=None):
    """GET the path, or POST the form to it, following the shop's redirect. Returns (final path, HTML).
    Raises urllib.error.URLError or HTTPError when the shop doesn't answer 2xx."""
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    with urllib.request.urlopen(connection.base_url("shop") + path, data=data, timeout=10) as response:
        return urllib.parse.urlparse(response.url).path, response.read().decode()


def add_to_cart(product_id):
    """Press "Add to cart" for the product."""
    return _request("/cart/add", {"product_id": product_id})


def remove_from_cart(product_id):
    """Press "Remove" on the product's cart line."""
    return _request("/cart/remove", {"product_id": product_id})


def page(path):
    """The served HTML of a page, parsed."""
    return parse(_request(path)[1])


class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.children, self.parts = tag, dict(attrs), [], []

    def text(self):
        """The element's visible text, whitespace collapsed."""
        return " ".join(self._all_text().split())

    def _all_text(self):
        out = list(self.parts)
        for child in self.children:
            out.append(child._all_text())
        return " ".join(out)

    def find_all(self, attr):
        """Every descendant carrying the attribute, in document order."""
        found = []
        for child in self.children:
            if attr in child.attrs:
                found.append(child)
            found.extend(child.find_all(attr))
        return found

    def find(self, attr):
        found = self.find_all(attr)
        return found[0] if found else None


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node("root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].parts.append(data)


def parse(html):
    builder = _Builder()
    builder.feed(html)
    return builder.root


def cents(money):
    """'$1,234.50' as 123450. Raises ValueError on anything else."""
    match = re.fullmatch(r"\$([\d,]+)\.(\d\d)", money.strip())
    if not match:
        raise ValueError(f"not an amount: {money!r}")
    return int(match.group(1).replace(",", "")) * 100 + int(match.group(2))

"""Build the self-contained page without a Codex installation or network.

The template stores its sandboxed iframe document in an HTML attribute, so
escape the fragment once: a source '<div>' becomes '&lt;div&gt;' in that
attribute. The browser decodes it when the standalone shell creates srcdoc.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = '__HIP_FRAGMENT_HTML__'

def build():
    fragment = (ROOT/'src'/'hip-planes.html').read_text(encoding='utf-8')
    template = (ROOT/'src'/'page-template.html').read_text(encoding='utf-8')
    if template.count(TOKEN) != 1:
        raise ValueError('The page template must contain exactly one fragment placeholder')
    if len(fragment.encode('utf-8')) >= 1_000_000:
        raise ValueError('The inline source must remain smaller than 1 MB')
    output = ROOT/'index.html'
    output.write_text(template.replace(TOKEN, escape(fragment)), encoding='utf-8', newline='\n')
    print(f'Built {output.name}: {output.stat().st_size:,} bytes')

if __name__ == '__main__':
    build()

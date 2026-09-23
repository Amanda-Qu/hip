"""Replace only the inline mesh payload, preserving the editable visualization."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HTML=ROOT.parent/'src'/'hip-planes.html'
text=HTML.read_text(encoding='utf-8')
text,count=re.subn(r'(?<=<script type="application/json" id="hip-bone-mesh-data">).*?(?=</script>)',lambda _: (ROOT/'anatomy.json').read_text(encoding='utf-8'),text,count=1,flags=re.S)
assert count==1
assert len(text.encode('utf-8'))<1_000_000,'Inline data exceeds visualization limit'
HTML.write_text(text,encoding='utf-8')
print('Fragment bytes:',HTML.stat().st_size)

#!/usr/bin/env python3
"""Render the offline-capable demo from the checked replay JSON. No network."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
payload=json.loads((root/'replay_data.json').read_text())
text=(root/'template.html').read_text().replace('__REPLAY_DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c'))
(root/'index.html').write_text(text)
print(root/'index.html')

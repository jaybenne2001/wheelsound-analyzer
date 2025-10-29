from pathlib import Path
import html
import json
def export_html_report(res, label, reasons):
    out = Path("data/recordings") / f"report_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    body = "<h2>WheelSound Report</h2>"
    body += f"<p><b>Result:</b> {html.escape(label)}</p>"
    body += "<ul>" + "".join(f"<li>{html.escape(r)}</li>" for r in reasons) + "</ul>"
    body += "<h3>Raw metrics</h3><pre>" + html.escape(json.dumps(res, indent=2)) + "</pre>"
    out.write_text(f"<!doctype html><html><meta charset='utf-8'><body>{body}</body></html>")
    return str(out)

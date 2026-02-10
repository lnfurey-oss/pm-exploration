 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index 843cd67a7f70a150d61e34aca10184fe2ffe8a73..2e40203e0b7458f0454fb7b69fe4215b74225004 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,26 @@
-# pm-exploration
\ No newline at end of file
+# pm-decision-copilot
+
+A lightweight product decision journaling API built with FastAPI and SQLite.
+
+## Setup
+
+```bash
+pip install fastapi uvicorn sqlalchemy pydantic requests jinja2
+```
+
+## Run the API
+
+```bash
+uvicorn main:app --reload
+```
+
+Then open the forwarded port in Codespaces to view the UI at `/`.
+If you're running locally, open `http://127.0.0.1:8000/`.
+
+## Sample data
+
+Start the API, then run:
+
+```bash
+python sample_data.py
+```
 
EOF
)
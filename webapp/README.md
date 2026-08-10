# Smart Glasses simulator console

Dependency-free, local-only browser interface for the synthetic device gateway.
It provides device status, allowlisted command execution, bounded local command
history, JSON export, and a copyable Markdown review brief.

Run from the repository root:

```bash
python3 tools/web_console.py
```

Open `http://127.0.0.1:8766`. The server binds to loopback. The browser stores
synthetic command summaries in `localStorage`; clear them from the interface or
browser storage. No physical device, patient data, cloud AI, diagnosis,
treatment, or surgical navigation is involved.

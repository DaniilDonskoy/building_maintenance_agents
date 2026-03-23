# Server

To begin create `server_logs` directory for logs in root directory, `.env` file in `server` directory, add `ALLOW_ORIGINS=["localhost", "localhost:3000"]` to `.env`. And then run:

```bash
uvicorn server.main:app --host 0.0.0.0 --port 80
```

Then you can open `http://0.0.0.0/` in your browser.

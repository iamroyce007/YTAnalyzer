# YTAnalyzer - Deployment Notes

This repository contains a Flask backend that analyzes YouTube videos (transcripts, comments) and uses Gemini (Google) for summarization.

Files added to improve deployment compatibility:
- `.env.example` - example for local development
- `Procfile` - start command for Render and other PaaS
- `Dockerfile` - container image for Render or Docker-enabled deployments
- `requirements.txt` updated to include `python-dotenv`

Local development
- Copy `.env.example` to `.env` and fill in your keys.

  ```bash
  cp .env.example .env
  # edit .env and set GEMINI_API_KEY and YOUTUBE_API_KEY
  pip install -r requirements.txt
  python app.py
  ```

Render (recommended for backend)
- Create a new Web Service on Render (or connect your GitHub repo).
- Set the start command to:

  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT
  ```

- Add the environment variables in Render dashboard: `GEMINI_API_KEY`, `YOUTUBE_API_KEY` (and `PORT` if desired).
- Alternatively, enable Docker and Render will use the provided `Dockerfile`.

Vercel (frontend + options)
- Vercel is primarily designed for static sites and serverless functions.
- Recommended approach: deploy the static frontend on Vercel and deploy this backend to Render (or another service), then set the frontend to call the backend URL.
- If you want to deploy the backend on Vercel you have two main options:
  - Deploy as a Docker container (Vercel supports custom deployments using Docker). Use the included `Dockerfile`.
  - Use Render/Heroku for the backend and Vercel for the frontend for simplicity.

Important notes
- Do NOT commit real API keys to your repo. Use the platform's environment variable settings (Render, Vercel dashboard).
- The app now loads `.env` via `python-dotenv` for local development but will prefer process environment variables when present.

If you'd like, I can:
- Add an example frontend `vercel.json` or API shim for Vercel serverless functions.
- Create a small GitHub Actions workflow to build and push the Docker image to a registry before deploying.

Java integration (optional)
- The app previously attempted to run a local Java program with hardcoded Windows paths. In production this is unsafe.
- To enable Java execution set the following environment variables in your platform (Render / Vercel Docker / other):
  - `RUN_JAVA=true` to enable Java execution
  - `JAVA_CLASS_PATH` path to compiled Java classes
  - `MYSQL_JAR_PATH` path to the MySQL connector JAR
  If these are not set or `RUN_JAVA` is not true, the app will skip Java execution.

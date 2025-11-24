# Deploying this Flask app to Render and using it from your phone

This repository contains a Flask web app (`module1.py`) that renders a responsive
HTML UI (`templates/index.html`) and stores data in `doses.json`.

Below are step-by-step instructions to deploy it to Render (render.com) and then
open the app on your phone.

1) Prepare your repo

- Confirm the repository root contains: `module1.py`, `templates/`, `Procfile`, `requirements.txt`.
- We updated `Procfile` to bind Gunicorn to Render's `$PORT`.

2) Push the project to GitHub

From the `x:\journal` folder (Windows PowerShell):

```powershell
git init
git add .
git commit -m "Initial commit: Flask app for Elvanse Tracker"
# create a repo on GitHub, then add the remote and push
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

3) Create a Web Service on Render

- Sign in to https://render.com and click "New" → "Web Service".
- Connect your GitHub account and choose the repository you pushed.
- For the Environment, choose "Python".
- Build settings:
  - Build Command: pip install -r requirements.txt
  - Start Command: gunicorn module1:app --bind 0.0.0.0:$PORT
  - Branch: main (or whatever branch you pushed)

Render will build the app and provide a public URL such as `https://your-app.onrender.com`.

4) Test and use the app on your phone

- Open the public URL in your phone's browser. The site is responsive and should
  work on mobile.
- The app uses HTTPS by default on Render. If you need to allow uploads or more
  advanced features, add environment variables or storage as needed in Render's
  dashboard.

Notes and tips

- If your app uses heavy desktop/mobile GUI code (`lisagraph.py`, Kivy), do *not*
  include that in the web service's runtime; it's for local GUI use only.
- If you want the app to autosave per-user rather than a single `doses.json`, you
  should move to a persistent database (Postgres) and configure Render's database
  or an external db.

If you want, I can:
- create a small `render.yaml` for Infrastructure-as-Code
- add a lightweight health-check endpoint
- push the changes to a GitHub repo for you (I'll need repository details/permissions)

---
Generated helper files: `requirements.txt`, updated `Procfile` to include $PORT.

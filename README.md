## Deploying to Vercel (Recommended)

This project is now set up for easy deployment to Vercel using their Python serverless runtime.

### Quick Deploy Steps
1. **Push your code to GitHub**
   - Make sure your project is in a GitHub repository (public or private).

2. **Sign up or log in to Vercel**
   - Go to [https://vercel.com/](https://vercel.com/) and sign in with your GitHub account.

3. **Import your project**
   - Click **"Add New Project"** and select your GitHub repo.

4. **Deploy**
   - Vercel will auto-detect the Python API in `api/index.py` and use `requirements.txt` in `api/`.
   - All routes are handled by the Flask app in `api/index.py`.
   - After deployment, you’ll get a live URL to access your chatbot.

#### Notes for Vercel
- All backend logic is now in `api/index.py` (not `app.py`).
- If you use files for storage (like `knowledge_base.json`), changes made at runtime may not persist between deploys or restarts on Vercel. For persistent storage, consider a database.
- For more advanced configuration, see the [Vercel Python docs](https://vercel.com/docs/frameworks/python).

---

## Running Locally (for development)

You can still run the app locally using either `app.py` or `api/index.py`.

### Option 1: Run with app.py (classic Flask)
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask server:
   ```bash
   python app.py
   ```
5. Open your browser and go to [http://localhost:5000](http://localhost:5000)

### Option 2: Run with api/index.py (matches Vercel)
1. (Optional) Activate your virtual environment as above.
2. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```
3. Start the Flask server:
   ```bash
   python api/index.py
   ```
4. Open your browser and go to [http://localhost:5000](http://localhost:5000)

---

## Features

- Modern WhatsApp-style UI
- Real-time chat interaction
- Add new knowledge via the UI
- Mobile-responsive design

---

## .gitignore

This project now includes `__pycache__/` in `.gitignore` to avoid tracking Python bytecode files.
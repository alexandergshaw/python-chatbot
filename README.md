## Python Chatbot (Flask + Bootstrap)

### 🚀 Deploy to Vercel
1. Push your code to GitHub.
2. Go to [vercel.com](https://vercel.com/) and import your repo.
3. Click **Deploy**. Vercel will auto-detect everything. Done!

### 🖥️ Run Locally
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```
3. Start the server:
   ```bash
   python api/index.py
   ```
4. Open [http://localhost:5000](http://localhost:5000) in your browser.

---

**Features:**
- Modern Bootstrap UI
- Real-time chat (all knowledge is stored in your browser)
- Add new Q&A via the UI
- Mobile-friendly

---

**.gitignore:**
`__pycache__/` is ignored by default.
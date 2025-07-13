## Deploying to Vercel

You can deploy this Flask app to Vercel for free using the Vercel website. Here’s how:

1. **Push your code to GitHub**
   - Make sure your project is in a GitHub repository (public or private).

2. **Sign up or log in to Vercel**
   - Go to [https://vercel.com/](https://vercel.com/) and sign in with your GitHub account.

3. **Import your project**
   - Click **"Add New Project"** and select your GitHub repo.

4. **Configure the project**
   - For a Python (Flask) app, set the following in the Vercel dashboard:
     - **Framework Preset:** `Other`
     - **Build Command:** `pip install -r requirements.txt`
     - **Output Directory:** `.`
     - **Root Directory:** (leave blank or set to your project folder if needed)
   
5. **Deploy**
   - Click **Deploy**. Vercel will build and deploy your Flask app.
   - After deployment, you’ll get a live URL to access your chatbot.

**Note:**
- If you use files for storage (like `knowledge_base.json`), changes made at runtime may not persist between deploys or restarts on Vercel. For persistent storage, consider a database.
- For more advanced configuration, see the [Vercel Python docs](https://vercel.com/docs/frameworks/python).
# Python ChatBot with Flask UI

A simple chatbot implementation using ChatterBot and Flask, featuring a modern WhatsApp-style UI.

## Setup

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

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Features

- Modern WhatsApp-style UI
- Real-time chat interaction
- Basic English language training
- Mobile-responsive design

## Note

This application uses ChatterBot 1.0.4, which requires Python < 3.8 on Windows systems. For other operating systems, different Python versions may be compatible. 
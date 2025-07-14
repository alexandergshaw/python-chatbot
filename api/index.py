
# Suppress debug/info logs from noisy libraries and root logger
import logging
logging.basicConfig(level=logging.WARNING)
for noisy_logger in [
    "transformers",
    "sentence_transformers",
    "torch",
    "chatterbot",
    "chatterbot.storage",
    "urllib3"
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from datetime import datetime, timedelta
import os
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '../templates')
STATIC_DIR = os.path.join(BASE_DIR, '../static')
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Serve favicon.ico from the static directory

@app.route('/')
def index():
    return render_template('index.html')

handler = app  # Required by Vercel Python runtime
  
if __name__ == "__main__":
    app.run(debug=True)

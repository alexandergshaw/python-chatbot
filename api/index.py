
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

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import os
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route('/')
def index():
    return render_template('index.html')

handler = app  # Required by Vercel Python runtime
  
if __name__ == "__main__":
    app.run(debug=True)

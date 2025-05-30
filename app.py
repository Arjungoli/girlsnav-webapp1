import os
from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename

from video_frames import extract_frames
from analyze_frames import aggregate_stats

UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "GirlsNav_frames"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!doctype html>
<html>
<head><title>GirlsNav Game Stats</title></head>
<body>
  <h1>Upload Basketball Game Video</h1>
  <form method=post enctype=multipart/form-data action="/upload">
    <input type=file name=video>
    <input type=submit value=Upload>
  </form>

  {% if stats %}
    <h2>Final Game Stats</h2>
    <pre>{{ stats }}</pre>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return "No video file uploaded", 400

    video = request.files["video"]
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(video_path)

    # Extract frames
    extract_frames(video_path, folder=FRAMES_FOLDER, step=30)

    # Analyze frames
    points, passes, rebounds = aggregate_stats(FRAMES_FOLDER)

    # Render stats
    stats = f"Points per Player: {dict(points)}\nTotal Passes: {passes}\nRebounds per Player: {dict(rebounds)}"
    return render_template_string(HTML_TEMPLATE, stats=stats)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

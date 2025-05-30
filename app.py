import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

from video_frames import extract_frames
from analyze_frames import aggregate_stats

UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "GirlsNav_frames"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files["video"]
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(video_path)

    # Extract frames
    extract_frames(video_path, output_dir=FRAMES_FOLDER, step=30)

    # Analyze frames
    points, passes, rebounds = aggregate_stats(FRAMES_FOLDER)

    # Return stats as JSON
    return jsonify({
        "stats": {
            "points": dict(points),
            "passes": passes,
            "rebounds": dict(rebounds)
        }
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

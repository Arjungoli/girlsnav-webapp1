import os
import cv2
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from video_frames import extract_frames
from analyze_frames import aggregate_stats

UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "GirlsNav_frames"
THUMBNAIL_FOLDER = "thumbnails"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["THUMBNAIL_FOLDER"] = THUMBNAIL_FOLDER

# Create necessary directories
for folder in [UPLOAD_FOLDER, FRAMES_FOLDER, THUMBNAIL_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def generate_thumbnail(video_path, thumbnail_path):
    """Generate a thumbnail from the first frame of the video."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(thumbnail_path, frame)
    cap.release()
    return ret

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

    # Generate thumbnail
    thumbnail_filename = f"{os.path.splitext(filename)[0]}_thumb.jpg"
    thumbnail_path = os.path.join(app.config["THUMBNAIL_FOLDER"], thumbnail_filename)
    if generate_thumbnail(video_path, thumbnail_path):
        return jsonify({
            "success": True,
            "filename": filename,
            "thumbnail": thumbnail_filename
        })
    else:
        return jsonify({"error": "Failed to generate thumbnail"}), 500

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename):
    return send_from_directory(app.config["THUMBNAIL_FOLDER"], filename)

@app.route("/analyze", methods=["POST"])
def analyze_video():
    data = request.get_json()
    if not data or "filename" not in data:
        return jsonify({"error": "No filename provided"}), 400

    filename = secure_filename(data["filename"])
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(video_path):
        return jsonify({"error": "Video file not found"}), 404

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

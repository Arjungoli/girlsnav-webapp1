import os
from pathlib import Path
from typing import Dict, Tuple, Any
import cv2
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from video_frames import extract_frames
from analyze_frames import aggregate_stats

# Configuration
class Config:
    UPLOAD_FOLDER = Path("uploads")
    FRAMES_FOLDER = Path("GirlsNav_frames")
    THUMBNAIL_FOLDER = Path("thumbnails")
    ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Create necessary directories
for folder in [Config.UPLOAD_FOLDER, Config.FRAMES_FOLDER, Config.THUMBNAIL_FOLDER]:
    folder.mkdir(exist_ok=True)

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return Path(filename).suffix.lower() in Config.ALLOWED_EXTENSIONS

def generate_thumbnail(video_path: Path, thumbnail_path: Path) -> bool:
    """Generate a thumbnail from the first frame of the video."""
    try:
        cap = cv2.VideoCapture(str(video_path))
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(str(thumbnail_path), frame)
        cap.release()
        return ret
    except Exception as e:
        app.logger.error(f"Error generating thumbnail: {str(e)}")
        return False

@app.route("/", methods=["GET"])
def index() -> str:
    """Render the main page."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_video() -> Tuple[Dict[str, Any], int]:
    """Handle video upload and generate thumbnail."""
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files["video"]
    if not video.filename:
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(video.filename):
        return jsonify({
            "error": f"Invalid file type. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        }), 400

    try:
        filename = secure_filename(video.filename)
        video_path = Config.UPLOAD_FOLDER / filename
        video.save(video_path)

        # Generate thumbnail
        thumbnail_filename = f"{Path(filename).stem}_thumb.jpg"
        thumbnail_path = Config.THUMBNAIL_FOLDER / thumbnail_filename
        
        if generate_thumbnail(video_path, thumbnail_path):
            return jsonify({
                "success": True,
                "filename": filename,
                "thumbnail": thumbnail_filename
            })
        else:
            return jsonify({"error": "Failed to generate thumbnail"}), 500

    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename: str) -> Any:
    """Serve thumbnail images."""
    try:
        return send_from_directory(Config.THUMBNAIL_FOLDER, filename)
    except Exception as e:
        app.logger.error(f"Error serving thumbnail: {str(e)}")
        return jsonify({"error": "Thumbnail not found"}), 404

@app.route("/analyze", methods=["POST"])
def analyze_video() -> Tuple[Dict[str, Any], int]:
    """Analyze the uploaded video and return statistics."""
    try:
        data = request.get_json()
        if not data or "filename" not in data:
            return jsonify({"error": "No filename provided"}), 400

        filename = secure_filename(data["filename"])
        video_path = Config.UPLOAD_FOLDER / filename

        if not video_path.exists():
            return jsonify({"error": "Video file not found"}), 404

        # Extract frames
        extract_frames(str(video_path), output_dir=str(Config.FRAMES_FOLDER), step=30)

        # Analyze frames
        points, passes, rebounds = aggregate_stats(str(Config.FRAMES_FOLDER))

        # Return stats as JSON
        return jsonify({
            "stats": {
                "points": dict(points),
                "passes": passes,
                "rebounds": dict(rebounds)
            }
        })

    except Exception as e:
        app.logger.error(f"Error analyzing video: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

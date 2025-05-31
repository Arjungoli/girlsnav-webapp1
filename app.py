import os
from pathlib import Path
from typing import Dict, Tuple, Any
import cv2
import logging
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from video_frames import extract_frames
from analyze_frames import aggregate_stats

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    logger.info(f"Created directory: {folder}")

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return Path(filename).suffix.lower() in Config.ALLOWED_EXTENSIONS

def generate_thumbnail(video_path: Path, thumbnail_path: Path) -> bool:
    """Generate a thumbnail from the first frame of the video."""
    try:
        logger.info(f"Generating thumbnail for video: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Failed to open video file: {video_path}")
            return False
            
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(str(thumbnail_path), frame)
            logger.info(f"Successfully generated thumbnail: {thumbnail_path}")
        else:
            logger.error("Failed to read frame from video")
        cap.release()
        return ret
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}", exc_info=True)
        return False

@app.route("/", methods=["GET"])
def index() -> str:
    """Render the main page."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_video() -> Tuple[Dict[str, Any], int]:
    """Handle video upload and generate thumbnail."""
    try:
        logger.info("Received upload request")
        
        if "video" not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file uploaded"}), 400

        video = request.files["video"]
        if not video.filename:
            logger.error("No filename in uploaded file")
            return jsonify({"error": "No selected file"}), 400

        logger.info(f"Received file: {video.filename}")
        
        if not allowed_file(video.filename):
            logger.error(f"Invalid file type: {video.filename}")
            return jsonify({
                "error": f"Invalid file type. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            }), 400

        filename = secure_filename(video.filename)
        video_path = Config.UPLOAD_FOLDER / filename
        
        logger.info(f"Saving file to: {video_path}")
        video.save(video_path)
        
        if not video_path.exists():
            logger.error(f"File was not saved successfully: {video_path}")
            return jsonify({"error": "Failed to save video file"}), 500

        # Generate thumbnail
        thumbnail_filename = f"{Path(filename).stem}_thumb.jpg"
        thumbnail_path = Config.THUMBNAIL_FOLDER / thumbnail_filename
        
        logger.info(f"Generating thumbnail: {thumbnail_path}")
        if generate_thumbnail(video_path, thumbnail_path):
            logger.info("Upload and thumbnail generation successful")
            return jsonify({
                "success": True,
                "filename": filename,
                "thumbnail": thumbnail_filename
            })
        else:
            logger.error("Failed to generate thumbnail")
            return jsonify({"error": "Failed to generate thumbnail"}), 500

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/thumbnails/<filename>")
def get_thumbnail(filename: str) -> Any:
    """Serve thumbnail images."""
    try:
        logger.info(f"Serving thumbnail: {filename}")
        return send_from_directory(Config.THUMBNAIL_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error serving thumbnail: {str(e)}", exc_info=True)
        return jsonify({"error": "Thumbnail not found"}), 404

@app.route("/analyze", methods=["POST"])
def analyze_video() -> Tuple[Dict[str, Any], int]:
    """Analyze the uploaded video and return statistics."""
    try:
        logger.info("Received analysis request")
        data = request.get_json()
        if not data or "filename" not in data:
            logger.error("No filename in analysis request")
            return jsonify({"error": "No filename provided"}), 400

        filename = secure_filename(data["filename"])
        video_path = Config.UPLOAD_FOLDER / filename

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return jsonify({"error": "Video file not found"}), 404

        logger.info(f"Extracting frames from: {video_path}")
        # Extract frames
        extract_frames(str(video_path), output_dir=str(Config.FRAMES_FOLDER), step=30)

        logger.info("Analyzing frames")
        # Analyze frames
        points, passes, rebounds = aggregate_stats(str(Config.FRAMES_FOLDER))

        logger.info("Analysis complete")
        # Return stats as JSON
        return jsonify({
            "stats": {
                "points": dict(points),
                "passes": passes,
                "rebounds": dict(rebounds)
            }
        })

    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

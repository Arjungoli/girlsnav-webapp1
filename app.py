from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

# Folder to store uploaded video files
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to render the UI
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# Route to handle video upload via AJAX
@app.route("/upload", methods=["POST"])
def upload_video():
    file = request.files.get("video")
    if not file:
        return jsonify({"status": "error", "message": "No video file uploaded"}), 400

    # Save uploaded file
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Return path for frontend preview
    return jsonify({
        "status": "success",
        "thumbnail": f"/static/uploads/{filename}"
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)

from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from video_frames import extract_frames
from analyze_frames import aggregate_stats

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)
        
        try:
            # Extract frames
            extract_frames(video_path, interval_sec=2)
            
            # Get the frames directory name
            video_name = os.path.splitext(filename)[0]
            frames_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{video_name}_frames")
            
            # Analyze frames
            points, passes, rebounds = aggregate_stats(frames_dir)
            
            return jsonify({
                'success': True,
                'stats': {
                    'points': dict(points),
                    'passes': passes,
                    'rebounds': dict(rebounds)
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True) 
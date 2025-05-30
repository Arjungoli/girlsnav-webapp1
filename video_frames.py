import cv2
import os

def extract_frames(video_path, interval_sec=1):
    """
    Extracts frames from a video file at regular intervals and saves them in a folder
    located in the same directory as the script.

    Args:
        video_path (str): Path to the input video file.
        interval_sec (int): Time interval between frames (in seconds).
    """
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Create output folder in the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, f"{video_name}_frames")
    os.makedirs(output_folder, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file: {video_path}")

    # Frame rate (frames per second)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_count % interval == 0:
            frame_filename = os.path.join(output_folder, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(frame_filename, frame)
            print(f"Saved: {frame_filename}")
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"\n✅ Done. Extracted {saved_count} frames to folder: {output_folder}")

# Example usage
if __name__ == "__main__":
    video_path = "GirlsNav.mp4"               # Replace with your video file
    extract_frames(video_path, interval_sec=2)

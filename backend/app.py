import os
import re
import zipfile
import shutil
from flask import jsonify, Flask, request, render_template, send_from_directory
from subprocess import run


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def downloadVideoOrPlaylist ():
    data = request.get_json()
    youtubeURL = data.get('url')
    
    match = re.search(r'list=([^&]+)', youtubeURL)
    unique_folder_name = match.group(1) if match else "single_video_download"
    
    if not youtubeURL:
        return jsonify ({"status": "error", "message": "No YouTube URL provided in the request body."}), 400
    
    command = [
        'yt-dlp',
        '-f', 'bestaudio[ext=m4a]',
        '--yes-playlist',
        '-o', os.path.join(DOWNLOADS_DIR, f'{unique_folder_name}/%(playlist_index)s - %(title)s.%(ext)s'),
        youtubeURL
    ]
    
    try:
        result = run (
            command,
            capture_output=True,
            text=True,
            cwd=DOWNLOADS_DIR,
            timeout=3600
        )
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"Download complete! Files saved to: {DOWNLOADS_DIR}",
                "download_id": unique_folder_name
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Download falied by yt-dlp.",
                "details": result.stderr
            }), 500
    except FileNotFoundError:
        return jsonify({
            "status": "error", 
            "message": "yt-dlp command not found. Ensure it is installed and available."
        }), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected server error occurred: {str(e)}"}), 500

# app.py (New Route)

@app.route('/serve/<download_id>')
def serve_download(download_id):
    """Packages the locally saved files into a ZIP and serves it to the browser."""
    
    # 1. Define Paths
    source_folder = os.path.join(DOWNLOADS_DIR, download_id)
    zip_filename = f'{download_id}_playlist.zip'
    zip_filepath = os.path.join(DOWNLOADS_DIR, zip_filename)

    if not os.path.isdir(source_folder):
        return jsonify({"status": "error", "message": "Download folder not found."}), 404

    try:
        # 2. Create the ZIP archive
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Add file, preserving the folder structure relative to the source folder
                    zipf.write(full_path, os.path.relpath(full_path, source_folder))
        
        # 3. Send the file to the browser
        # This forces the browser to open the download dialog
        response = send_from_directory(
            directory=DOWNLOADS_DIR, 
            path=zip_filename, 
            as_attachment=True, 
            mimetype='application/zip'
        )

        # 4. Cleanup: Remove the temporary files immediately after serving (optional but recommended)
        shutil.rmtree(source_folder)
        os.remove(zip_filepath)

        return response
        
    except Exception as e:
        # If zipping or serving fails
        return jsonify({"status": "error", "message": f"Error zipping or serving file: {str(e)}"}), 500
if __name__ == '__main__':
    app.run(debug=True)
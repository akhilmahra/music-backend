from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"status": "Backend Running"}


def safe_extract(ydl, url, retries=3):
    """
    Retry wrapper for yt-dlp extraction
    """
    last_error = None

    for i in range(retries):
        try:
            print(f"Download attempt {i + 1}")
            return ydl.extract_info(url, download=True)
        except Exception as e:
            last_error = e
            print(f"Attempt {i + 1} failed: {e}")
            time.sleep(1)

    raise Exception(f"Download failed after retries: {last_error}")


@app.route("/download", methods=["POST"])
def download_audio():

    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    video_url = data["url"]
    unique_id = str(uuid.uuid4())

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        f"{unique_id}.%(ext)s"
    )

    ydl_opts = {
        # ✅ more stable format selection
        "format": "bestaudio[ext=m4a]/bestaudio/best",

        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,

        "cookiefile": "cookies.txt",

        # 🔥 stability settings
        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": True,
        "concurrent_fragment_downloads": 1,
        "ignoreerrors": False,

        # helps avoid YouTube blocking (very important on Render)
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },

        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        },

        # audio conversion
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            # optional small delay (helps reduce random blocking)
            time.sleep(1)

            info = safe_extract(ydl, video_url, retries=3)

            title = info.get("title", "Unknown")

        # find downloaded file safely
        file_path = None

        for file in os.listdir(DOWNLOAD_FOLDER):
            if file.startswith(unique_id):
                file_path = os.path.join(DOWNLOAD_FOLDER, file)
                break

        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Audio file not found after download"}), 500

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{title}.m4a",
            mimetype="audio/mp4"
        )

    except Exception as e:
        import traceback
        print("FULL ERROR:")
        traceback.print_exc()

        return jsonify({
            "error": str(e),
            "type": str(type(e))
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

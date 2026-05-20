from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {
        "status": "Backend Running"
    }


@app.route("/download", methods=["POST"])
def download_audio():

    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "error": "No URL provided"
        }), 400

    video_url = data["url"]

    unique_id = str(uuid.uuid4())

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        f"{unique_id}.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,s
        "quiet": True,
        "cookiefile": "cookies.txt",
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "192",
        }],
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                video_url,
                download=True
            )

            title = info.get("title", "Unknown")

        final_file = f"{DOWNLOAD_FOLDER}/{unique_id}.m4a"

        if not os.path.exists(final_file):

            return jsonify({
                "error": "Audio conversion failed"
            }), 500

        return send_file(
            final_file,
            as_attachment=True,
            download_name=f"{title}.m4a",
            mimetype="audio/mp4"
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )

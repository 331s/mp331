from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import glob
import base64

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()

# Cookie yukle
COOKIE_FILE = None
_b64 = os.environ.get("YT_COOKIES_B64", "")
if _b64:
    try:
        _path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(_path, "wb") as f:
            f.write(base64.b64decode(_b64))
        COOKIE_FILE = _path
    except Exception as e:
        print(f"Cookie yukleme hatasi: {e}")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

# Cookie durumunu kontrol et
@app.route("/cookie-check")
def cookie_check():
    b64 = os.environ.get("YT_COOKIES_B64", "")
    if not b64:
        return jsonify({"status": "ENV VAR YOK", "cookie_file": None})
    if not COOKIE_FILE:
        return jsonify({"status": "DECODE BASARISIZ", "cookie_file": None})
    try:
        with open(COOKIE_FILE, "r") as f:
            lines = f.readlines()
        return jsonify({
            "status": "OK",
            "cookie_file": COOKIE_FILE,
            "line_count": len(lines),
            "first_line": lines[0].strip() if lines else "",
            "has_sid": any("SID" in l for l in lines),
            "has_sapisid": any("SAPISID" in l for l in lines),
        })
    except Exception as e:
        return jsonify({"status": f"OKUMA HATASI: {e}"})

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    quality = request.form.get("quality", "192")
    if quality not in {"128", "192", "256", "320"}:
        quality = "192"
    if not url:
        return "Lutfen bir YouTube linki girin.", 400

    temp_dir = tempfile.mkdtemp()
    ydl_opts = {
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
        "ffmpeg_location": FFMPEG_PATH,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality},
            {"key": "FFmpegMetadata", "add_metadata": True},
        ],
        "postprocessor_args": {"ffmpegextractaudio": ["-b:a", f"{quality}k"]},
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if COOKIE_FILE:
        ydl_opts["cookiefile"] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "ses")

        mp3_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
        if not mp3_files:
            return "MP3 olusturulamadi.", 500

        safe_title = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "ses"
        return send_file(mp3_files[0], as_attachment=True, download_name=f"{safe_title}.mp3", mimetype="audio/mpeg")

    except Exception as e:
        return f"Hata: {str(e)}", 400

if __name__ == "__main__":
    app.run(debug=True)

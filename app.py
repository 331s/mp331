from flask import Flask, render_template, request, send_file, jsonify
import os, tempfile, glob, base64, subprocess, sys, shutil

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()
YTDLP_PATH  = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
if not os.path.exists(YTDLP_PATH):
    YTDLP_PATH = "yt-dlp"

# Node.js yolunu bul
NODE_PATH = shutil.which("node") or shutil.which("nodejs") or ""

COOKIE_FILE = None
_b64 = os.environ.get("YT_COOKIES_B64", "")
if _b64:
    try:
        _path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(_path, "wb") as f:
            f.write(base64.b64decode(_b64))
        COOKIE_FILE = _path
    except Exception as e:
        print(f"Cookie hatasi: {e}")

app = Flask(__name__)

def base_cmd():
    cmd = [
        YTDLP_PATH,
        "--no-playlist",
        # Node.js varsa JS runtime olarak kullan
        "--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
        # EJS script'i GitHub'dan indir (n challenge ve format sorununu çözer)
        "--no-warnings",
    ]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    return cmd

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    r = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({
        "yt_dlp": r.stdout.strip(),
        "ffmpeg": FFMPEG_PATH,
        "node": NODE_PATH,
        "cookie": COOKIE_FILE is not None,
    })

@app.route("/download", methods=["POST"])
def download():
    url     = request.form.get("url", "").strip()
    quality = request.form.get("quality", "192")
    if quality not in {"128", "192", "256", "320"}:
        quality = "192"
    if not url:
        return "Lutfen bir YouTube linki girin.", 400

    temp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    cmd = base_cmd() + [
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", f"{quality}k",
        "--ffmpeg-location", FFMPEG_PATH,
        "-o", out_tmpl,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    mp3_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
    if not mp3_files:
        err = result.stderr or result.stdout
        return f"Hata: {err[:800]}", 400

    title = os.path.splitext(os.path.basename(mp3_files[0]))[0]
    safe  = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "ses"
    return send_file(mp3_files[0], as_attachment=True, download_name=f"{safe}.mp3", mimetype="audio/mpeg")

import traceback

@app.errorhandler(500)
def internal_error(e):
    return f"<pre>500 Error:\n{traceback.format_exc()}</pre>", 500

if __name__ == "__main__":
    app.run(debug=True)

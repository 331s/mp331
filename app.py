from flask import Flask, render_template, request, send_file, jsonify
import os, tempfile, glob, base64, subprocess, sys

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    result = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({
        "yt_dlp_cli": result.stdout.strip(),
        "ffmpeg": FFMPEG_PATH,
        "cookie_loaded": COOKIE_FILE is not None,
    })

@app.route("/cookie-check")
def cookie_check():
    if not COOKIE_FILE:
        return jsonify({"status": "COOKIE YOK"})
    try:
        with open(COOKIE_FILE, "r") as f:
            lines = f.readlines()
        return jsonify({
            "status": "OK",
            "line_count": len(lines),
            "has_sid": any("SID" in l for l in lines),
            "has_sapisid": any("SAPISID" in l for l in lines),
        })
    except Exception as e:
        return jsonify({"status": f"HATA: {e}"})

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

    cmd = [
        YTDLP_PATH,
        "--no-playlist",
        # 2026 SABR fix: web_creator cookie ile PO token gerektirmiyor
        "--extractor-args", "youtube:player_client=web_creator,tv,mweb",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", f"{quality}k",
        "--ffmpeg-location", FFMPEG_PATH,
        "-o", out_tmpl,
        "--no-warnings",
    ]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        return f"Hata: {result.stderr or result.stdout}", 400

    mp3_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
    if not mp3_files:
        return f"MP3 olusturulamadi. Cikti: {result.stdout[:500]}", 500

    title = os.path.splitext(os.path.basename(mp3_files[0]))[0]
    safe  = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "ses"
    return send_file(mp3_files[0], as_attachment=True, download_name=f"{safe}.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)

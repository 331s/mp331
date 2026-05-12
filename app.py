from flask import Flask, render_template, request, Response, jsonify, stream_with_context
import os, tempfile, base64, subprocess, sys, shutil, json

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

def base_args():
    args = [
        "--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
        "--no-warnings", "--no-playlist",
    ]
    if COOKIE_FILE:
        args += ["--cookies", COOKIE_FILE]
    return args

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    r = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({"yt_dlp": r.stdout.strip(), "node": NODE_PATH, "cookie": COOKIE_FILE is not None})

@app.route("/info", methods=["POST"])
def info():
    """Video bilgisini ve formatları çek — hızlı, download yok"""
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL gerekli"}), 400

    cmd = [YTDLP_PATH] + base_args() + ["-J", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return jsonify({"error": r.stderr[:300]}), 400
    try:
        data = json.loads(r.stdout)
        return jsonify({
            "title": data.get("title", ""),
            "duration": data.get("duration", 0),
            "thumbnail": data.get("thumbnail", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/download", methods=["POST"])
def download():
    """Doğrudan stream: sunucuya kaydetmeden client'a gönder"""
    url     = request.form.get("url", "").strip()
    quality = request.form.get("quality", "192")
    if quality not in {"128", "192", "256", "320"}:
        quality = "192"
    if not url:
        return "URL gerekli", 400

    # yt-dlp'yi ffmpeg pipeline ile çalıştır, stdout'a yaz
    cmd = [
        YTDLP_PATH,
        "-f", "bestaudio/best",
        "--no-playlist",
        "--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
        "--no-warnings",
        "--concurrent-fragments", "4",
        "-o", "-",          # stdout'a yaz
        "--quiet",
    ]
    if COOKIE_FILE:
        cmd += ["--cookies", COOKIE_FILE]
    cmd.append(url)

    # ffmpeg ile mp3'e dönüştür, stdout'a yaz
    ffmpeg_cmd = [
        FFMPEG_PATH,
        "-i", "pipe:0",
        "-vn",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", f"{quality}k",
        "-f", "mp3",
        "pipe:1",
    ]

    def generate():
        yt = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        ff = subprocess.Popen(ffmpeg_cmd, stdin=yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        yt.stdout.close()
        try:
            while True:
                chunk = ff.stdout.read(65536)
                if not chunk:
                    break
                yield chunk
        finally:
            ff.wait()
            yt.wait()

    return Response(
        stream_with_context(generate()),
        mimetype="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=audio.mp3",
            "X-Accel-Buffering": "no",
        }
    )

if __name__ == "__main__":
    app.run(debug=True)

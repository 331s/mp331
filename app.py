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
    args = ["--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
            "--no-warnings", "--no-playlist"]
    if COOKIE_FILE:
        args += ["--cookies", COOKIE_FILE]
    return args

def safe_filename(title):
    return "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "audio"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/version")
def version():
    r = subprocess.run([YTDLP_PATH, "--version"], capture_output=True, text=True)
    return jsonify({"yt_dlp": r.stdout.strip(), "node": NODE_PATH, "cookie": COOKIE_FILE is not None})

@app.route("/info", methods=["POST"])
def info():
    url = request.form.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL gerekli"}), 400
    cmd = [YTDLP_PATH] + base_args() + ["-J", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return jsonify({"error": r.stderr[:300]}), 400
    try:
        data = json.loads(r.stdout)
        return jsonify({"title": data.get("title", ""), "duration": data.get("duration", 0)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/download", methods=["POST"])
def download():
    url     = request.form.get("url", "").strip()
    quality = request.form.get("quality", "192")
    if quality not in {"128", "192", "256", "320"}:
        quality = "192"
    if not url:
        return "URL gerekli", 400

    # Önce başlığı hızlıca çek
    title_r = subprocess.run(
        [YTDLP_PATH] + base_args() + ["--print", "title", url],
        capture_output=True, text=True, timeout=15
    )
    title = safe_filename(title_r.stdout.strip()) if title_r.returncode == 0 else "audio"

    # yt-dlp → ffmpeg → client pipe
    yt_cmd = [
        YTDLP_PATH, "-f", "bestaudio/best",
        "--no-playlist",
        "--js-runtimes", f"node:{NODE_PATH}" if NODE_PATH else "node",
        "--no-warnings", "--concurrent-fragments", "4",
        "-o", "-", "--quiet",
    ]
    if COOKIE_FILE:
        yt_cmd += ["--cookies", COOKIE_FILE]
    yt_cmd.append(url)

    # Metadata'yı yt-dlp'den çek
    meta_r = subprocess.run(
        [YTDLP_PATH] + base_args() + [
            "--print", "%(title)s|||%(uploader)s|||%(upload_date)s",
            url
        ],
        capture_output=True, text=True, timeout=15
    )
    meta_parts = (meta_r.stdout.strip().split("|||") + ["", "", ""])[:3]
    track_title = meta_parts[0] or title
    artist      = meta_parts[1] or ""
    year        = meta_parts[2][:4] if len(meta_parts[2]) >= 4 else ""

    ff_cmd = [
        FFMPEG_PATH, "-i", "pipe:0", "-vn",
        "-ar", "44100", "-ac", "2",
        "-b:a", f"{quality}k",
        "-metadata", f"title={track_title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"date={year}",
        "-metadata", f"comment=youtube",
        "-id3v2_version", "3",
        "-f", "mp3", "pipe:1",
    ]

    def generate():
        yt = subprocess.Popen(yt_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        ff = subprocess.Popen(ff_cmd, stdin=yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
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
            "Content-Disposition": f'attachment; filename="{title}.mp3"',
            "X-Accel-Buffering": "no",
        }
    )

if __name__ == "__main__":
    app.run(debug=True)

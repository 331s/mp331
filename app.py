from flask import Flask, render_template, request, send_file
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
        return 'ffmpeg'

FFMPEG_PATH = get_ffmpeg_path()

COOKIE_FILE = None
_cookie_b64 = os.environ.get('YT_COOKIES_B64', '')
if _cookie_b64:
    try:
        _cookie_path = os.path.join(tempfile.gettempdir(), 'yt_cookies.txt')
        with open(_cookie_path, 'wb') as _f:
            _f.write(base64.b64decode(_cookie_b64))
        COOKIE_FILE = _cookie_path
    except Exception:
        pass

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    quality = request.form.get('quality', '192')

    if quality not in {'128', '192', '256', '320'}:
        quality = '192'
    if not url:
        return "Lütfen bir YouTube linki girin.", 400

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
        'postprocessor_args': {
            'ffmpegextractaudio': ['-b:a', f'{quality}k'],
        },
        'quiet': True,
        'no_warnings': True,
    }

    if COOKIE_FILE:
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'ses')

        mp3_files = glob.glob(os.path.join(temp_dir, '*.mp3'))
        if not mp3_files:
            return "MP3 dosyası oluşturulamadı.", 500

        file_path = mp3_files[0]
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "ses"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{safe_title}.mp3",
            mimetype='audio/mpeg'
        )

    except yt_dlp.utils.DownloadError as e:
        return f"İndirme hatası: {str(e)}", 400
    except Exception as e:
        return f"Beklenmedik bir hata: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

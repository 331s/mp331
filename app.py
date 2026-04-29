from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import tempfile
import glob

# FFmpeg yolunu belirle: önce sistem, yoksa imageio-ffmpeg
def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return 'ffmpeg'

FFMPEG_PATH = get_ffmpeg_path()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    quality = request.form.get('quality', '192')

    allowed_qualities = {'128', '192', '256', '320'}
    if quality not in allowed_qualities:
        quality = '192'
    if not url:
        return "Lütfen bir YouTube linki girin.", 400

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        'format': 'bestaudio/best',
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
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web'],
            }
        },
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'ses')

        mp3_files = glob.glob(os.path.join(temp_dir, '*.mp3'))
        if not mp3_files:
            return "MP3 dosyası oluşturulamadı.", 500

        file_path = mp3_files[0]
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-()[]").strip() or "ses"
        download_name = f"{safe_title}.mp3"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='audio/mpeg'
        )

    except yt_dlp.utils.DownloadError as e:
        return f"İndirme hatası: {str(e)}", 400
    except Exception as e:
        return f"Beklenmedik bir hata: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

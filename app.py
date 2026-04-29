from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import tempfile
import glob

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    quality = request.form.get('quality', '192')

    # Güvenli kalite doğrulama
    allowed_qualities = {'128', '192', '256', '320'}
    if quality not in allowed_qualities:
        quality = '192'
    if not url:
        return "Lütfen bir YouTube linki girin.", 400

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
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
        # preferredquality sadece öneri; bitrate'i FFmpeg'e zorla geçiyoruz
        'postprocessor_args': {
            'ffmpegextractaudio': ['-b:a', f'{quality}k'],
        },
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'ses')

        # Find the converted mp3 file
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
        return f"İndirme hatası: Video bulunamadı veya erişim kısıtlı.", 400
    except Exception as e:
        return f"Beklenmedik bir hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

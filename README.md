<div align="center">

<br>

# <span>MP3</span>31

**YouTube videolarını yüksek kaliteli MP3'e dönüştür.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br>

![MP404 Preview](https://i.imgur.com/pegKgov.png)

<br>

</div>

---

## ✨ Özellikler

- 🎵 **Çoklu kalite seçeneği** — 128 / 192 / 256 / 320 kbps
- ⚡ **Hızlı dönüşüm** — yt-dlp + FFmpeg ile optimize edilmiş pipeline
- 📋 **Akıllı yapıştır** — Panoda YouTube linki varsa otomatik algılar
- 🔒 **Gizlilik odaklı** — Dosyalar sunucuda saklanmaz, işlem sonrası silinir
- 🎨 **Modern arayüz** — Animasyonlu dark UI, tamamen responsive

---

## 🚀 Kurulum

### Gereksinimler

- Python 3.8+
- FFmpeg (sistem genelinde kurulu olmalı)

### 1. Repoyu klonla

```bash
git clone https://github.com/331s/mp331.git
cd mp331
```

### 2. Sanal ortam oluştur

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları yükle

```bash
pip install flask yt-dlp
```

### 4. FFmpeg kurulumu

```bash
# Windows (winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 5. Çalıştır

```bash
python app.py
```

Tarayıcıda aç: `http://127.0.0.1:5000`

---

## 📁 Proje Yapısı

```
mp331/
├── app.py                  # Flask backend
├── templates/
│   └── index.html          # Ana sayfa
└── static/
    ├── css/
    │   └── style.css       # Stiller
    └── js/
        └── main.js         # Frontend mantığı
```

---

## 🎛️ Kalite Seçenekleri

| Kalite | Boyut (yaklaşık) | Kullanım |
|--------|-----------------|----------|
| 128 kbps | ~1 MB/dk | Podcast, konuşma |
| 192 kbps | ~1.4 MB/dk | Genel müzik dinleme |
| 256 kbps | ~2 MB/dk | Yüksek kalite |
| 320 kbps | ~2.4 MB/dk | Maksimum kalite |

---

## ⚙️ Nasıl Çalışır?

```
YouTube URL
    │
    ▼
yt-dlp → En iyi ses akışını indirir
    │
    ▼
FFmpeg → Seçilen bitrate'te MP3'e dönüştürür (-b:a Xk)
    │
    ▼
Flask → Dosyayı tarayıcıya gönderir (send_file)
    │
    ▼
Tarayıcı → Otomatik indirir, sunucudan silinir
```

---

## 🛠️ Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, Flask |
| İndirici | yt-dlp |
| Dönüştürücü | FFmpeg |
| Frontend | Vanilla HTML / CSS / JS |
| Fontlar | Bebas Neue, JetBrains Mono, Manrope |

---

## ⚠️ Yasal Uyarı

Bu proje yalnızca **kişisel ve eğitim amaçlı** geliştirilmiştir. Telif hakkıyla korunan içeriklerin izinsiz indirilmesi YouTube'un [Kullanım Koşulları](https://www.youtube.com/static?template=terms)'nı ihlal edebilir. Sorumluluk kullanıcıya aittir.

---

<div align="center">

Geliştirici: **331 Studios** &nbsp;•&nbsp; Barış

</div>

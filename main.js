/* ===========================
   MP331 — main.js
   =========================== */

const form        = document.getElementById('downloadForm');
const urlInput    = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const pasteBtn    = document.getElementById('pasteBtn');
const statusMsg   = document.getElementById('statusMsg');
const headerBadge = document.getElementById('headerBadge');
const featQuality = document.getElementById('featQuality');

let videoTitle = '';  // /info'dan gelen başlık

/* ---------- Quality selector sync ---------- */
function getSelectedQuality() {
    const checked = form.querySelector('input[name="quality"]:checked');
    return checked ? checked.value : '192';
}

function syncQualityUI(val) {
    if (headerBadge) headerBadge.textContent = `${val}kbps • MP3`;
    if (featQuality) featQuality.textContent = `${val} kbps MP3`;
}

form.querySelectorAll('input[name="quality"]').forEach(radio => {
    radio.addEventListener('change', () => syncQualityUI(getSelectedQuality()));
});
syncQualityUI(getSelectedQuality());

/* ---------- Paste button ---------- */
pasteBtn.addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text.trim()) {
            urlInput.value = text.trim();
            urlInput.focus();
            pasteBtn.style.color = 'var(--accent)';
            setTimeout(() => (pasteBtn.style.color = ''), 600);
        }
    } catch { urlInput.focus(); }
});

urlInput.addEventListener('focus', async () => {
    if (urlInput.value) return;
    try {
        const text = await navigator.clipboard.readText();
        if (isYouTubeURL(text.trim())) urlInput.value = text.trim();
    } catch {}
});

function isYouTubeURL(str) {
    return /^https?:\/\/(www\.)?(youtube\.com\/(watch|shorts)|youtu\.be\/)/.test(str);
}

/* ---------- URL değişince başlığı çek ---------- */
let infoDebounce = null;
urlInput.addEventListener('input', () => {
    if (!statusMsg.hidden) hideStatus();
    videoTitle = '';
    clearTimeout(infoDebounce);
    const val = urlInput.value.trim();
    if (isYouTubeURL(val)) {
        infoDebounce = setTimeout(() => fetchInfo(val), 600);
    }
});

async function fetchInfo(url) {
    try {
        const fd = new FormData();
        fd.append('url', url);
        const res  = await fetch('/info', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.title) videoTitle = data.title;
    } catch {}
}

/* ---------- Form submit ---------- */
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return showStatus('Lütfen bir YouTube linki girin.', 'error');
    if (!isYouTubeURL(url)) return showStatus('Geçerli bir YouTube linki giriniz.', 'error');

    setLoading(true);
    hideStatus();

    try {
        const formData = new FormData(form);
        // Başlığı backend'e gönder — ekstra yt-dlp çağrısı olmadan kullanılır
        formData.append('title', videoTitle || 'audio');

        const response = await fetch('/download', { method: 'POST', body: formData });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `Hata: ${response.status}`);
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
        const filename = filenameMatch ? filenameMatch[1] : `${videoTitle || 'audio'}.mp3`;

        const objectURL = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objectURL;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objectURL);

        showStatus(`✓ İndirme tamamlandı! ${getSelectedQuality()} kbps MP3 kaydedildi.`, 'success');
        urlInput.value = '';
        videoTitle = '';

    } catch (err) {
        showStatus('⚠ ' + (err.message || 'Bir hata oluştu, tekrar deneyin.'), 'error');
    } finally {
        setLoading(false);
    }
});

function setLoading(state) {
    downloadBtn.disabled = state;
    downloadBtn.classList.toggle('loading', state);
}
function showStatus(message, type = 'error') {
    statusMsg.textContent = message;
    statusMsg.className = `status-msg ${type}`;
    statusMsg.hidden = false;
}
function hideStatus() { statusMsg.hidden = true; }

const observer = new MutationObserver(() => {
    const fast = downloadBtn.disabled;
    document.querySelectorAll('.waveform span').forEach(bar => {
        const dur = parseFloat(getComputedStyle(bar).getPropertyValue('--dur') || 1);
        bar.style.animationDuration = fast ? `${dur * 0.35}s` : '';
    });
});
observer.observe(downloadBtn, { attributes: true, attributeFilter: ['disabled'] });

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

// init
syncQualityUI(getSelectedQuality());

/* ---------- Paste button ---------- */
pasteBtn.addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text.trim()) {
            urlInput.value = text.trim();
            urlInput.focus();
            flashPaste();
        }
    } catch {
        urlInput.focus();
    }
});

function flashPaste() {
    pasteBtn.style.color = 'var(--accent)';
    setTimeout(() => (pasteBtn.style.color = ''), 600);
}

/* ---------- Auto-paste on focus if clipboard has YouTube URL ---------- */
urlInput.addEventListener('focus', async () => {
    if (urlInput.value) return;
    try {
        const text = await navigator.clipboard.readText();
        if (isYouTubeURL(text.trim())) {
            urlInput.value = text.trim();
        }
    } catch { /* permission denied, skip */ }
});

function isYouTubeURL(str) {
    return /^https?:\/\/(www\.)?(youtube\.com\/(watch|shorts)|youtu\.be\/)/.test(str);
}

/* ---------- Form submit — fetch + streaming download ---------- */
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = urlInput.value.trim();
    if (!url) return showStatus('Lütfen bir YouTube linki girin.', 'error');

    if (!isYouTubeURL(url)) {
        return showStatus('Geçerli bir YouTube linki giriniz.', 'error');
    }

    setLoading(true);
    hideStatus();

    try {
        const formData = new FormData(form);
        const response = await fetch('/download', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `Hata: ${response.status}`);
        }

        /* Trigger file download in browser */
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = contentDisposition.match(/filename\*?=['"]?([^'";]+)['"]?/);
        const filename = filenameMatch
            ? decodeURIComponent(filenameMatch[1])
            : 'ses.mp3';

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

    } catch (err) {
        showStatus('⚠ ' + (err.message || 'Bir hata oluştu, tekrar deneyin.'), 'error');
    } finally {
        setLoading(false);
    }
});

/* ---------- Helpers ---------- */
function setLoading(state) {
    downloadBtn.disabled = state;
    downloadBtn.classList.toggle('loading', state);
}

function showStatus(message, type = 'error') {
    statusMsg.textContent = message;
    statusMsg.className = `status-msg ${type}`;
    statusMsg.hidden = false;
}

function hideStatus() {
    statusMsg.hidden = true;
}

/* ---------- Clear status on input change ---------- */
urlInput.addEventListener('input', () => {
    if (!statusMsg.hidden) hideStatus();
});

/* ---------- Waveform — slow bars on idle, fast on loading ---------- */
function setWaveformSpeed(fast) {
    const bars = document.querySelectorAll('.waveform span');
    bars.forEach(bar => {
        const dur = parseFloat(getComputedStyle(bar).getPropertyValue('--dur') || 1);
        bar.style.animationDuration = fast ? `${dur * 0.35}s` : '';
    });
}

const observer = new MutationObserver(() => {
    setWaveformSpeed(downloadBtn.disabled);
});
observer.observe(downloadBtn, { attributes: true, attributeFilter: ['disabled'] });

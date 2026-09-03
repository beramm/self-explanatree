# Self-Explanation

## Deskripsi

Project **Self-Explanation** adalah proyek tanaman bisa "ngomong" berbasis Raspberry Pi. Dengan menggunakan berbagai teknologi pemrosesan suara dan AI, tanaman dapat mendengarkan, memproses, dan memberikan respons suara layaknya berbicara.

**Author:** RND SMP

## Alur Kerja

1. **VAD (Voice Activity Detection)**
   - Menggunakan *WebRTC VAD* di Python untuk mendeteksi bagian suara.
2. **STT (Speech to Text)**
   - Menggunakan *Faster Whisper* untuk mengubah suara menjadi teks.
3. **Kirim ke AI**
   - Teks dikirim ke *OpenAI* untuk mendapat respons cerdas.
4. **TTS (Text to Speech)**
   - Mengubah hasil AI menjadi suara dengan *Piper*.
5. **Output**
   - Suara hasil TTS diucapkan ke speaker (tanaman "berbicara").

## Instalasi

1. Pastikan Anda telah menginstal Python 3.9+ dan `uv` (Python process manager).  
   Instal `uv` jika belum:
   ```bash
   pip install uv
   ```

2. Kloning repository dan install dependensi:
   ```bash
   sudo apt install -y build-essential portaudio19-dev
   uv sync
   ```

3. Set environment variable untuk Gemini di file `.env`:
   ```env
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   ```

4. Download model suara Piper (contoh: suara Bahasa Indonesia - id_ID-news_tts-medium):
   ```bash
   uv run -m piper.download_voices --download-dir=.models id_ID-news_tts-medium
   ```

## Menjalankan Project

Pastikan semua langkah di atas sudah dilakukan, lalu jalankan aplikasi dengan perintah:
```bash
uv run -m app
```

---

Selamat mencoba! 🌱🔊

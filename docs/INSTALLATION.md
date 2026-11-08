# Panduan Instalasi Lengkap Project Apex (Multi-OS)

Panduan resmi untuk memasang, mengonfigurasi, dan menjalankan **Project Apex** di berbagai sistem operasi: Linux (Ubuntu/Debian, Arch Linux, Fedora), macOS, dan Windows.

---

## 1. Persyaratan Sistem
* **Python:** Versi 3.10 atau lebih tinggi (`python3 --version`).
* **Git:** Versi 2.20 atau lebih baru.
* **Akses Internet:** Untuk mengunduh dependensi dan menghubungi API LLM.
* **Memori RAM:** Minimal 256 MB RAM (sangat hemat, tanpa model lokal berat).

---

## 2. Instalasi di Linux & macOS (Satu Perintah)

Buka terminal dan jalankan:

```bash
git clone <repo-url> /home/chandra/Proj
cd /home/chandra/Proj
chmod +x install.sh
./install.sh
```

Skrip installer otomatis:
1. Memeriksa keberadaan Python >= 3.10.
2. Membuat virtual environment di `.venv`.
3. Memasang dependensi (`rich`, `prompt-toolkit`, `requests`, `pyyaml`, `websockets`, `pypdf`).
4. Mendaftarkan perintah global `apex` ke `~/.local/bin/apex`.
5. Menyiapkan folder konfigurasi default di `~/.apex/apex.json`.

---

## 3. Instalasi di Windows (PowerShell)

Buka PowerShell (sebagai user biasa atau Administrator) dan jalankan:

```powershell
git clone <repo-url> C:\Users\YourUser\Proj
cd C:\Users\YourUser\Proj
.\install.ps1
```

Skrip akan mendaftarkan perintah `apex` ke PATH pengguna di `%USERPROFILE%\.apex\bin\apex.cmd`.

---

## 4. Konfigurasi Awal: Wizard Interaktif 6-Tahap

Setelah instalasi selesai, jalankan perintah setup:

```bash
apex setup
```

Pemandu interaktif akan memandu Anda melalui 6 tahap:
1. **Pemeriksaan Lingkungan & OS Host**
2. **Koneksi Provider AI Utama & Tambahan** (OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, Together, Ollama)
3. **Pemilih File SOUL & Persona** (pilih file `soul.md` kustom Anda)
4. **Editor Prompt Injection 3-Lapis** (Global, Per-Model, Chat Script Priming)
5. **Gateway Messaging & Otorisasi Pemilik** (Telegram Bot Token, WhatsApp Baileys, Discord, Whitelist ID)
6. **Live Diagnostic Healthcheck** (Pengujian otomatis koneksi model dengan penunjuk error visual jika ada masalah)

---

## 5. Menjalankan Sebagai Service Daemon 24/7 (Ubuntu Server / Systemd)

Untuk menjalankan Project Apex tanpa henti di latar belakang server:

1. Salin file service:
   ```bash
   sudo cp systemd/apex.service /etc/systemd/system/
   ```
2. Sesuaikan username dan path pada `/etc/systemd/system/apex.service`.
3. Aktifkan dan jalankan:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now apex
   sudo systemctl status apex
   ```
4. Atau gunakan perintah bawaan Apex:
   ```bash
   apex gateway start
   apex gateway status
   apex gateway stop
   ```

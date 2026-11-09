# 🚀 Panduan Instalasi Lengkap Project Apex (Multi-OS)

Panduan langkah-demi-langkah resmi untuk memasang, mengonfigurasi, dan menjalankan **Project Apex** di berbagai sistem operasi:
- [macOS (Apple Silicon M1/M2/M3/M4 & Intel)](#1--macos-apple-silicon--intel)
- [Ubuntu Server (Headless Cloud / VPS)](#2--ubuntu-server-headless-vps--cloud)
- [Ubuntu Desktop & Debian](#3--ubuntu-desktop--debian)
- [Arch Linux & Manjaro](#4--arch-linux--manjaro)
- [Distro Linux Lainnya (Fedora, RHEL, CentOS, OpenSUSE)](#5--distro-linux-lainnya-fedora-rhel-opensuse)
- [Konfigurasi Awal (Setup Wizard)](#-konfigurasi-awal-setup-wizard)
- [Menjalankan Sebagai Service Daemon 24/7 (Systemd)](#-menjalankan-sebagai-service-daemon-247-systemd)

---

## 1. 🍏 macOS (Apple Silicon & Intel)

### A. Persyaratan:
macOS memerlukan **Homebrew** untuk memasang Python versi terbaru dan Git.

Jika belum memiliki Homebrew, pasang melalui Terminal:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### B. Pasang Dependensi Sistem:
```bash
brew update
brew install python git
```

### C. Clone Repositori & Jalankan Installer:
```bash
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

### D. Tambahkan PATH ke Shell Profile (zsh):
Jika perintah `apex` belum terbaca di terminal, tambahkan direktori binary ke `~/.zshrc`:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verifikasi instalasi:
```bash
apex --help
```

---

## 2. 🐧 Ubuntu Server (Headless VPS / EC2 / Droplet)

Ubuntu Server umumnya tidak memiliki antarmuka grafis (GUI) dan berjalan sebagai remote cloud server (DigitalOcean, AWS EC2, Linode, Hetzner, dll.).

### A. Perbarui Paket Sistem & Pasang Dependensi:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git curl build-essential libffi-dev libssl-dev
```

### B. Clone Repositori & Pasang Apex:
```bash
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

### C. Konfigurasi PATH untuk Bash:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### D. Penggunaan di Server Headless:
Untuk server tanpa layar monitor, jalankan Apex menggunakan:
1. **Interactive Chat:** `apex`
2. **Background Daemon:** `apex gateway start` (berjalan terus di latar belakang meskipun sesi SSH Anda ditutup).

---

## 3. 🐧 Ubuntu Desktop & Debian

### A. Pasang Prasyarat:
Buka Terminal (`Ctrl + Alt + T`):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl build-essential
```

### B. Clone Repositori & Pasang:
```bash
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

### C. Pastikan PATH Aktif:
```bash
source ~/.bashrc
apex --help
```

---

## 4. 🏹 Arch Linux & Manjaro

Arch Linux menggunakan sistem manajemen paket `pacman` dan menerapkan aturan PEP 668 (*externally managed environment*), di mana pembuatan virtual environment sangat disarankan.

### A. Pasang Paket Sistem:
```bash
sudo pacman -Syu --noconfirm
sudo pacman -S --needed --noconfirm python python-pip git base-devel
```

### B. Clone Repositori & Pasang Apex:
```bash
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

### C. Tambahkan PATH ke Shell (Bash atau Zsh):
```bash
# Untuk pengguna Bash:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Untuk pengguna Zsh:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

---

## 5. 📦 Distro Linux Lainnya (Fedora, RHEL, openSUSE)

### Fedora / RHEL / AlmaLinux / Rocky Linux:
```bash
sudo dnf install -y python3 python3-devel python3-pip git gcc libffi-devel openssl-devel
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

### openSUSE:
```bash
sudo zypper install -y python3 python3-devel python3-pip git gcc libffi-devel
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
```

---

## ⚙️ Konfigurasi Awal (Setup Wizard)

Setelah instalasi berhasil, jalankan wizard konfigurasi interaktif untuk menghubungkan API provider dan preferensi Anda:

```bash
apex setup
```

Pemandu interaktif akan memandu Anda melalui 6 tahap:
1. **Host Environment & OS Check:** Memeriksa kompatibilitas terminal dan izin eksekusi.
2. **Koneksi Provider AI:** Masukkan API Key provider pilihan Anda (OpenAI, Anthropic, TokenHarbor, OpenRouter, Groq, DeepSeek, atau Ollama Lokal).
3. **Pemilih SOUL & Persona:** Menentukan file identitas kepribadian agent.
4. **Editor Prompt Priming:** Menyesuaikan instruksi default ReAct agent.
5. **Gateway Messaging:** Mengaktifkan bot Telegram, WhatsApp, atau REST Webhook jika diinginkan.
6. **Live Diagnostic Healthcheck:** Pengujian koneksi API dan verifikasi kesiapan sistem.

---

## 🔄 Menjalankan Sebagai Service Daemon 24/7 (Systemd)

Jika Anda ingin Apex berjalan otomatis saat server booting dan terus aktif 24 jam di latar belakang (misalnya untuk melayani Bot Telegram, Webhook, atau Jadwal Rutin/Cron):

### 1. Salin file template systemd:
```bash
sudo cp systemd/apex.service /etc/systemd/system/
```

### 2. Sesuaikan konfigurasi user dan path:
Buka file service:
```bash
sudo nano /etc/systemd/system/apex.service
```
Pastikan `User=`, `WorkingDirectory=`, dan path ke binary `apex` sesuai dengan user sistem Anda (misal: `/home/ubuntu/apex-agent` atau `/home/chandra/apex-agent`).

### 3. Aktifkan dan jalankan service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now apex
```

### 4. Periksa status service:
```bash
sudo systemctl status apex
```

### Atau gunakan manajemen gateway bawaan Apex:
```bash
apex gateway start      # Menjalankan gateway di latar belakang
apex gateway status     # Memeriksa status proses dan listening port
apex gateway stop       # Menghentikan background gateway
```

---

## 🔍 Troubleshooting (Tanya Jawab Masalah)

### ❓ Perintah `apex: command not found`
* **Penyebab:** Folder `~/.local/bin` belum terdaftar dalam variabel `$PATH` sistem Anda.
* **Solusi:** Jalankan `export PATH="$HOME/.local/bin:$PATH"` dan tambahkan baris tersebut ke file `~/.bashrc` (atau `~/.zshrc` di macOS).

### ❓ Error saat instalasi `cryptography`
* **Penyebab:** Compiler C atau header libffi/OpenSSL belum terpasang di sistem.
* **Solusi:**
  * Di Ubuntu/Debian: `sudo apt install build-essential libssl-dev libffi-dev`
  * Di macOS: `xcode-select --install`
  * Di Arch Linux: `sudo pacman -S base-devel`

---

Selamat menggunakan **Project Apex** di lingkungan pilihan Anda! 🚀

# Sovereign Hybrid Agent ("Project Apex")

> **Unrestricted Full Host Access · 20+ Channel 24/7 Gateway · 4-Trick Pure-Software Anti-Refusal · 9Router RTK Token Saver · Pi-Style Minimalist TUI · Unbounded Swarm · Full MCP & ACP Support**

<div align="center">

[![Min RAM](https://img.shields.io/badge/Min%20RAM-512%20MB-10b981?style=for-the-badge&logo=ram&logoColor=white)](#-kebutuhan-sistem--spesifikasi-hardware-system-requirements)
[![GPU](https://img.shields.io/badge/VRAM-0%20GB%20Mandatory%20(CPU%20Ready)-0284c7?style=for-the-badge&logo=nvidia&logoColor=white)](#-kebutuhan-sistem--spesifikasi-hardware-system-requirements)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.14-f59e0b?style=for-the-badge&logo=python&logoColor=white)](#-kebutuhan-sistem--spesifikasi-hardware-system-requirements)
[![Platform](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-8b5cf6?style=for-the-badge&logo=linux&logoColor=white)](#-kebutuhan-sistem--spesifikasi-hardware-system-requirements)

</div>

---

## ⚡ Quick Start

```bash
# 1. Clone repository
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent

# 2. Install dependencies & Apex CLI
chmod +x install.sh
./install.sh

# 3. Run Interactive 6-Stage Setup Wizard
apex setup

# 4. Start Minimalist Terminal TUI
apex
```

---

## 💻 Kebutuhan Sistem & Spesifikasi Hardware (System Requirements)

Project Apex dirancang dengan filosofi **Ultra-Lightweight Pure-Software Architecture**. Apex **TIDAK mewajibkan GPU/VRAM diskrit**, karena seluruh fitur inti (Anti-Refusal, RTK Token Saver, 9Router Pro Gateway, Multi-Channel Bot, Swarm, dan RAG Memory) dapat berjalan mulus menggunakan model cloud *(OpenAI, Claude, DeepSeek, TokenHarbor)* hanya dengan CPU biasa dan konsumsi RAM yang sangat hemat.

Berikut adalah tabel panduan spesifikasi hardware mulai dari spek paling minimal hingga spek maksimal/workstation:

| Kategori | 🟢 Spesifikasi Minimal (Cloud API & Gateway) | 🟡 Spesifikasi Rekomendasi (Power User & Heavy Swarm) | 🔴 Spesifikasi Maksimal (Full Local LLM Self-Hosted) |
| :--- | :--- | :--- | :--- |
| **Skenario Penggunaan** | Menjalankan Apex CLI, 9Router Pro Gateway, Web Dashboard, dan integrasi IDE (Cursor/Claude Code) via API Cloud *(OpenAI, Claude, DeepSeek, TokenHarbor, Groq)* | Menjalankan daemon 24/7 di 20+ platform (Telegram, WhatsApp, Discord, Slack), otomatisasi browser Lightpanda, dan multi-agent swarm intensif | Menjalankan Model AI 100% lokal & offline secara mandiri di komputer sendiri via Ollama / vLLM / llama.cpp *(Model 8B, 14B, 32B, hingga 70B)* |
| **Prosesor (CPU)** | **1 Core** (x86_64 atau ARM64)<br>• *Contoh: Intel Celeron, Raspberry Pi 4/5, VPS Cloud 1 vCPU* | **4 – 8 Core**<br>• *Contoh: Intel Core i5/i7 (Gen 10+), AMD Ryzen 5/7, Apple Silicon M1/M2/M3/M4* | **8 – 16+ Core**<br>• *Contoh: AMD Ryzen 9 / Threadripper, Intel Core i9, Apple M-Series Max / Ultra* |
| **RAM (Memori)** | **512 MB – 1 GB**<br>*(Core Apex runtime hanya memakan ~120 MB RAM)* | **8 GB – 16 GB** DDR4/DDR5 | **32 GB – 64 GB+** (DDR5 / Unified Memory)<br>*(Dibutuhkan untuk memuat bobot model GGUF ke dalam memori)* |
| **Penyimpanan (Disk)** | **500 MB** ruang kosong untuk Python venv, tool script, dan cache database | **5 GB – 10 GB** SSD untuk log transaksi, cache dokumen RAG, dan riwayat MITM | **50 GB – 200 GB+** High-Speed NVMe SSD *(Untuk menyimpan file bobot model AI lokal 4-bit/8-bit)* |
| **Kartu Grafis (GPU / VRAM)**| **0 GB (Tidak Butuh GPU)**<br>100% berjalan optimal di CPU tanpa akselerasi grafis | **Tidak Wajib** (GPU terintegrasi Intel Iris / AMD Radeon sudah sangat memadai) | **NVIDIA RTX 3060 / 4070 / 4080 / 4090** *(8 GB – 24 GB VRAM)* atau **Apple Silicon M-Series Unified Memory (36 GB–128 GB)** |
| **Sistem Operasi** | Linux (Ubuntu 20.04+, Debian 11+, Arch Linux, Fedora, Alpine), macOS 11+, Windows 10/11 (WSL2 / PowerShell) | Linux x86_64 (Kernel 5.15+) atau macOS (Apple Silicon) | Linux x86_64 (didukung NVIDIA CUDA 12+) atau macOS Apple Silicon (Metal Acceleration) |
| **Versi Python** | Python 3.9, 3.10, 3.11, 3.12, 3.13, atau 3.14+ | Python 3.11 – 3.14 | Python 3.11 – 3.14 |
| **Koneksi Jaringan** | Akses internet minimal (untuk streaming API token) | Broadband 10+ Mbps (untuk multi-channel gateway lancar) | **Bisa 100% Offline Total** tanpa koneksi internet sama sekali setelah model terunduh |

> [!TIP]
> **Rekomendasi VPS Murah:** Anda bisa menyewa VPS Linux termurah ($3 – $5/bulan) dengan 1 vCPU dan 1 GB RAM untuk menjalankan Project Apex sebagai gateway AI 24/7 di cloud tanpa kendala!

---

## 📦 Panduan Instalasi Lengkap per Sistem Operasi

Pilih sistem operasi yang Anda gunakan untuk melihat langkah instalasi cepat:

<details open>
<summary><b>🍏 macOS (Apple Silicon M1/M2/M3/M4 & Intel)</b></summary>

```bash
# 1. Pasang Python & Git via Homebrew
brew install python git

# 2. Clone & Install Apex
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh

# 3. Muat PATH zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 4. Konfigurasi & Jalankan
apex setup
apex
```
</details>

<details open>
<summary><b>🐧 Ubuntu Server (Headless Cloud VPS / EC2 / Droplet)</b></summary>

```bash
# 1. Update Sistem & Pasang Dependensi Compiler
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git curl build-essential libffi-dev libssl-dev

# 2. Clone & Install Apex
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh

# 3. Muat PATH Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Konfigurasi & Jalankan Service Latar Belakang 24/7
apex setup
apex gateway start      # Menjalankan daemon di background (tetap aktif meski SSH ditutup)
apex gateway status     # Memeriksa status proses
```
</details>

<details open>
<summary><b>🐧 Ubuntu Desktop & Debian</b></summary>

```bash
# 1. Pasang Paket Prasyarat
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git curl build-essential

# 2. Clone & Install Apex
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh

# 3. Muat PATH & Jalankan
source ~/.bashrc
apex setup
apex
```
</details>

<details open>
<summary><b>🏹 Arch Linux & Manjaro</b></summary>

```bash
# 1. Update & Pasang Paket via pacman
sudo pacman -Syu --needed --noconfirm python python-pip git base-devel

# 2. Clone & Install Apex
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh

# 3. Muat PATH & Jalankan
# Untuk pengguna Bash:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
# Untuk pengguna Zsh:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

apex setup
apex
```
</details>

<details>
<summary><b>📦 Distro Linux Lainnya (Fedora, RHEL, CentOS, openSUSE)</b></summary>

```bash
# Fedora / RHEL / Rocky Linux:
sudo dnf install -y python3 python3-devel python3-pip git gcc libffi-devel openssl-devel

# Clone & Install:
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
chmod +x install.sh
./install.sh
source ~/.bashrc

apex setup
apex
```
</details>

<details>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
# Clone & Jalankan Installer Windows
git clone https://github.com/chandra343/apex-agent.git
cd apex-agent
.\install.ps1

# Konfigurasi & Jalankan
apex setup
apex
```
</details>

> 📖 Dokumentasi teknis lebih detail dan panduan troubleshooting tersedia di [docs/INSTALLATION.md](docs/INSTALLATION.md).

---

## 🧭 Core Architecture Pillars

1. **Unrestricted Full Host Access (`apex/tools/`):** Full read, write, edit, patch, and terminal shell execution on the host OS with zero artificial sandbox friction.
2. **Safety Net Checkpoints (`undo_file`):** Automated pre-write snapshots of files before modification, allowing instantaneous reversions if code edits deviate.
3. **Interactive 3-Button Approval Gates:** `[ Eksekusi ]`, `[ Batalkan ]`, and `[ ⚡ Selalu Eksekusi ]` (Always Execute Autopilot) for critical commands.
4. **4-Trick Pure-Software Single-Key Anti-Refusal:** Auto-Reframing, Chat Script Priming, Tool-First Mode, and Direct Host Override. Guaranteed 100% compliance with zero local PC memory load (no mandatory Ollama/local weights).
5. **Dynamic Model Switcher (`/model`):** Switch models on the fly in Telegram (interactive inline buttons) and CLI TUI without losing session context.
6. **9Router Pro RTK Token Saver:** In-memory regex/AST payload compression saving 20–40% token usage on tool outputs.
7. **3-Tier Smart Auto-Fallback:** Subscription $\rightarrow$ Cheap Pay-As-You-Go $\rightarrow$ Free/Local.
8. **Per-Conversation FIFO Queue:** Sequential message ordering preventing race conditions across Telegram, WhatsApp, and CLI.
9. **24/7 Daemon & 20+ Platforms:** Telegram, WhatsApp (Baileys), Discord, Slack, Signal, Matrix, Teams, Email, and Webhooks.
10. **Full MCP Client (stdio + HTTP/SSE):** Universal integration with any Model Context Protocol server.
11. **Agent Client Protocol (ACP) & Python API:** Connect directly to VS Code, Cursor, Zed, Neovim, or import programmatically via `from apex import ApexAgent`.
12. **In-App Task Scheduler & Durable Jobs:** Crash-resilient scheduled background jobs with anti-stampede guards.
13. **Lightpanda Browser Engine:** CDP headless browsing consuming only ~20 MB RAM.
14. **Pi Agent Radical Minimalism TUI:** Clean, non-distracting terminal interface with collapsible tool chips and real-time streaming highlighting.
15. **Dynamic Tool Discovery (`tool_search` & `tool_describe`):** On-demand semantic tool lookup reducing initial token payload by ~70%.
16. **Shared SQLite Data Lake (`agent_data.db`):** Multi-agent relational tabular data store enabling seamless SQL queries, joins, and tables.
17. **AES-256-GCM Encrypted Vault (`manage_vault`):** Enterprise-grade secret vault with zero-leak previews and automatic `{{vault:KEY}}` resolution.
18. **Autonomous Tool Self-Healing & Diagnostics:** Intelligent error pattern matching (ModuleNotFoundError, PortConflict, etc.) with actionable remediation loops.
19. **Declarative DAG Workflows (`manage_workflows`):** Multi-step pipeline orchestrator with cycle detection, parameter piping (`${node.output}`), and conditional branching.
20. **Tiered Cognitive Memory (`manage_cognitive_memory`):** Multi-layer cognitive store (working, episodic, fact, rule) with time-decay relevance and pinned preferences.

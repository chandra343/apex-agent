# Sovereign Hybrid Agent ("Project Apex")

> **Unrestricted Full Host Access · 20+ Channel 24/7 Gateway · 4-Trick Pure-Software Anti-Refusal · 9Router RTK Token Saver · Pi-Style Minimalist TUI · Unbounded Swarm · Full MCP & ACP Support**

Project Apex combines the proven production architectural pillars of **Hermes Agent**, **Zeline**, **OpenClaw & Lobster**, **9Router & 9Router Pro**, **Lightpanda Browser**, and **Pi Agent (`pi.dev`)** into a unified, sovereign AI companion.

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

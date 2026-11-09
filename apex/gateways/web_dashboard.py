"""Modern Interactive Web Gateway & 9Router Pro AI Provider Dashboard for Project Apex.

Provides:
- FastAPI Web Server + WebSocket Real-Time Chat
- 9Router-Style AI Provider & Account Management Hub (Login, Add Keys, Model Switcher, Ping Test)
- Encrypted AES-256-GCM Secret Vault Web Manager
- Single-Page Application (SPA) with Dark Mode, Tailwind CSS, marked.js, highlight.js
- Live Tool Execution Monitoring & Omni-Modal Document Reader
- System Metrics & Token Ledger Visualizer
"""
from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from apex.agent import default_agent
from apex.config import config, DATA_DIR, PKG_ROOT
from apex.memory.store import memory_store
from apex.router.fallback import fallback_router
from apex.router.provider_manager import provider_manager
from apex.router.ledger import token_ledger
from apex.security.vault import secret_vault
from apex.tools import tool_registry
from apex.tools.doc_reader import read_any_file


app = FastAPI(title="Apex Sovereign Agent Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Embedded High-Aesthetic Single Page Application (HTML/JS)
# ---------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apex Sovereign AI — 9Router Pro Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Marked.js (Markdown) -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Highlight.js (Code Syntax) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        apex: {
                            50: '#ecfeff',
                            100: '#cffafe',
                            500: '#06b6d4',
                            600: '#0891b2',
                            700: '#0e7490',
                            800: '#155e75',
                            900: '#082f49',
                            dark: '#0b0f19',
                            card: '#111827',
                            border: '#1f2937'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #374151; }
        pre code.hljs { border-radius: 0.5rem; padding: 1rem; }
    </style>
</head>
<body class="bg-apex-dark text-slate-100 min-h-screen flex flex-col font-sans antialiased">

    <!-- Top Navigation Bar -->
    <header class="bg-apex-card border-b border-apex-border h-16 flex items-center justify-between px-6 z-10 sticky top-0 shadow-lg">
        <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-cyan-500/30 shadow-md">
                <i class="fa-solid fa-bolt text-white text-lg"></i>
            </div>
            <div>
                <div class="font-bold text-lg tracking-wide flex items-center gap-2">
                    <span>PROJECT APEX</span>
                    <span class="text-xs bg-cyan-900/60 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-700/50">9Router Pro</span>
                </div>
                <div class="text-xs text-slate-400">Sovereign Hybrid AI Agent Engine</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <nav class="hidden md:flex items-center gap-1.5 bg-apex-dark p-1 rounded-xl border border-apex-border">
            <button onclick="switchTab('chat')" id="tab-chat" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all bg-cyan-600 text-white shadow-sm flex items-center gap-1.5">
                <i class="fa-solid fa-terminal text-xs"></i> Chat Console
            </button>
            <button onclick="switchTab('providers')" id="tab-providers" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
                <i class="fa-solid fa-network-wired text-xs"></i> 9Router AI Hub
            </button>
            <button onclick="switchTab('vault')" id="tab-vault" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
                <i class="fa-solid fa-key text-xs"></i> Vault Secrets
            </button>
            <button onclick="switchTab('docs')" id="tab-docs" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
                <i class="fa-solid fa-file-invoice text-xs"></i> Doc & OCR Reader
            </button>
            <button onclick="switchTab('tools')" id="tab-tools" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
                <i class="fa-solid fa-toolbox text-xs"></i> Tools Explorer
            </button>
            <button onclick="switchTab('stats')" id="tab-stats" class="px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-1.5">
                <i class="fa-solid fa-chart-line text-xs"></i> Tokens & Metrics
            </button>
        </nav>

        <!-- Right System Indicators -->
        <div class="flex items-center gap-4">
            <div class="text-right hidden sm:block">
                <div id="active-model-display" class="text-xs font-mono font-semibold text-cyan-400">Loading model...</div>
                <div class="text-[10px] text-emerald-400 flex items-center justify-end gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> <span id="active-provider-display">Host Connected</span>
                </div>
            </div>
            <button onclick="loadStatus(); if(currentTab==='providers')loadProviders();" title="Refresh Status" class="w-8 h-8 rounded-lg bg-apex-border/60 hover:bg-apex-border text-slate-300 flex items-center justify-center transition-all">
                <i class="fa-solid fa-arrows-rotate text-sm"></i>
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 flex overflow-hidden">

        <!-- ======================= TAB 1: CHAT CONSOLE ======================= -->
        <section id="view-chat" class="flex-1 flex overflow-hidden">
            <!-- Sidebar Sessions -->
            <aside class="w-72 bg-apex-card border-r border-apex-border flex flex-col hidden lg:flex">
                <div class="p-4 border-b border-apex-border flex items-center justify-between">
                    <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Sessions</span>
                    <button onclick="newSession()" class="text-xs bg-cyan-600/80 hover:bg-cyan-600 text-white px-2.5 py-1 rounded-md transition-all flex items-center gap-1">
                        <i class="fa-solid fa-plus"></i> New
                    </button>
                </div>
                <div id="session-list" class="flex-1 overflow-y-auto p-2 space-y-1">
                    <div class="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 text-sm font-medium flex items-center gap-2 cursor-pointer">
                        <i class="fa-solid fa-message text-xs"></i>
                        <span class="truncate">web_session</span>
                    </div>
                </div>
                <div class="p-3 border-t border-apex-border text-xs text-slate-500 flex items-center justify-between">
                    <span>Apex SQLite Store</span>
                    <i class="fa-solid fa-database"></i>
                </div>
            </aside>

            <!-- Chat Area -->
            <div class="flex-1 flex flex-col bg-apex-dark overflow-hidden">
                <!-- Message Feed -->
                <div id="chat-messages" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
                    <!-- Welcome Card -->
                    <div class="max-w-3xl mx-auto bg-apex-card border border-apex-border/80 rounded-2xl p-6 shadow-xl">
                        <div class="flex items-center gap-3 mb-3">
                            <span class="text-2xl">🚀</span>
                            <h2 class="text-lg font-bold text-white">Selamat Datang di Apex Web Dashboard!</h2>
                        </div>
                        <p class="text-sm text-slate-300 leading-relaxed mb-4">
                            Apex adalah asisten rekayasa otonom dengan 9Router AI Gateway terintegrasi, eksekutor terminal Bash, pembaca dokumen omni-modal, brankas enkripsi AES-256, dan alur kerja DAG otomatis.
                        </p>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Bantu cek spesifikasi sistem host dan ruang disk')">
                                <span class="font-semibold text-cyan-400">🔍 Cek Spesifikasi Host:</span> "Bantu cek spesifikasi sistem host dan ruang disk"
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Tampilkan daftar tabel pada database ~/.apex/agent_data.db')">
                                <span class="font-semibold text-cyan-400">📊 Shared Data Lake:</span> "Tampilkan daftar tabel pada database ~/.apex/agent_data.db"
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="switchTab('providers')">
                                <span class="font-semibold text-cyan-400">🌐 9Router AI Hub:</span> Kelola akun provider AI, tambah token, & ganti model
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="switchTab('vault')">
                                <span class="font-semibold text-cyan-400">🔐 Brankas Kredensial:</span> Simpan API Key & Password aman di AES-256 Vault
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Live Tool Execution Indicator -->
                <div id="live-tool-bar" class="hidden px-6 py-2 bg-cyan-950/70 border-t border-cyan-800/60 flex items-center justify-between text-xs text-cyan-300 animate-pulse">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-cog fa-spin"></i>
                        <span id="live-tool-text">Menjalankan tool...</span>
                    </div>
                    <span class="text-[10px] bg-cyan-900 px-2 py-0.5 rounded border border-cyan-700">ReAct Host</span>
                </div>

                <!-- Input Box -->
                <div class="p-4 bg-apex-card border-t border-apex-border">
                    <div class="max-w-3xl mx-auto flex items-end gap-2 bg-apex-dark border border-apex-border rounded-xl p-2 focus-within:border-cyan-500 transition-all shadow-inner">
                        <button onclick="document.getElementById('file-upload').click()" title="Unggah Dokumen / Gambar" class="p-2 text-slate-400 hover:text-cyan-400 transition-all">
                            <i class="fa-solid fa-paperclip"></i>
                        </button>
                        <input type="file" id="file-upload" class="hidden" onchange="handleDocInspect(this.files[0])">
                        
                        <textarea id="prompt-input" rows="1" onkeydown="handleKeyDown(event)" placeholder="Ketik perintah atau instruksi untuk Apex... (Shift+Enter untuk baris baru)" class="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1.5 max-h-36"></textarea>
                        
                        <button id="send-button" onclick="handleSend()" class="bg-cyan-600 hover:bg-cyan-500 text-white w-9 h-9 rounded-lg flex items-center justify-center transition-all shadow-md shrink-0">
                            <i class="fa-solid fa-arrow-up"></i>
                        </button>
                    </div>
                    <div class="text-center text-[10px] text-slate-500 mt-2">
                        Project Apex • Host Sovereignty • Turn-1 Action Mode • AES-256 Vault
                    </div>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 2: 9ROUTER AI PROVIDERS & ACCOUNTS ======================= -->
        <section id="view-providers" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-6xl mx-auto space-y-6">
                <!-- Header Banner -->
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-apex-card via-slate-900 to-cyan-950 p-6 rounded-2xl border border-cyan-800/40 shadow-xl">
                    <div>
                        <div class="flex items-center gap-2">
                            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-network-wired text-cyan-400"></i> 9Router Pro AI Hub
                            </h2>
                            <span class="text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full font-mono">Multi-Provider</span>
                        </div>
                        <p class="text-xs text-slate-300 mt-1">Kelola akun provider AI, tambahkan API key, ganti model aktif secara instan, dan tes latensi.</p>
                    </div>
                    <div class="flex flex-wrap items-center gap-2">
                        <button onclick="scanLocalEngines()" class="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium rounded-xl transition-all flex items-center gap-2 shadow-sm">
                            <i class="fa-solid fa-microchip text-cyan-400"></i> Scan AI Lokal (Ollama)
                        </button>
                        <button onclick="openAddProviderModal()" class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-xl transition-all flex items-center gap-2 shadow-md shadow-cyan-600/20">
                            <i class="fa-solid fa-plus"></i> Tambah / Login Akun
                        </button>
                    </div>
                </div>

                <!-- Active Routing Status Banner -->
                <div class="bg-apex-card border border-apex-border rounded-xl p-4 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-cyan-900/60 border border-cyan-700/60 flex items-center justify-center text-cyan-400 text-xl font-bold shrink-0">
                            ⚡
                        </div>
                        <div>
                            <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Active Router Engine</div>
                            <div class="flex items-center gap-2 mt-0.5">
                                <span id="hub-active-provider" class="text-base font-bold text-white">Loading...</span>
                                <span class="text-xs text-slate-400">•</span>
                                <span id="hub-active-model" class="text-sm font-mono text-cyan-400">Loading model...</span>
                                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-1"></span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-3 self-stretch md:self-auto justify-between md:justify-end">
                        <div class="text-right">
                            <div class="text-[10px] text-slate-400 uppercase">Latency Ping</div>
                            <div id="hub-active-latency" class="text-xs font-mono font-semibold text-emerald-400">-</div>
                        </div>
                        <button onclick="testActiveProvider()" class="px-3 py-1.5 bg-apex-dark border border-apex-border hover:border-cyan-500 text-xs text-slate-200 rounded-lg transition-all flex items-center gap-1.5">
                            <i class="fa-solid fa-bolt text-xs text-yellow-400"></i> Tes Latensi
                        </button>
                    </div>
                </div>

                <!-- Search & Category Filter Pills -->
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                        <button onclick="filterProviderCategory('all', this)" class="cat-pill px-3 py-1.5 rounded-lg bg-cyan-600 text-white font-medium transition-all">Semua Provider</button>
                        <button onclick="filterProviderCategory('popular', this)" class="cat-pill px-3 py-1.5 rounded-lg bg-apex-card border border-apex-border text-slate-300 hover:text-white font-medium transition-all">Layanan Populer</button>
                        <button onclick="filterProviderCategory('gateway', this)" class="cat-pill px-3 py-1.5 rounded-lg bg-apex-card border border-apex-border text-slate-300 hover:text-white font-medium transition-all">Cloud Gateways</button>
                        <button onclick="filterProviderCategory('local', this)" class="cat-pill px-3 py-1.5 rounded-lg bg-apex-card border border-apex-border text-slate-300 hover:text-white font-medium transition-all">AI Lokal</button>
                        <button onclick="filterProviderCategory('oauth', this)" class="cat-pill px-3 py-1.5 rounded-lg bg-apex-card border border-apex-border text-slate-300 hover:text-white font-medium transition-all">Langganan (OAuth)</button>
                    </div>
                    <div class="relative w-full sm:w-64">
                        <input type="text" id="provider-search-input" oninput="searchProviders(this.value)" placeholder="Cari provider atau model..." class="w-full bg-apex-card border border-apex-border px-3 py-1.5 pl-8 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
                        <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-xs text-slate-500"></i>
                    </div>
                </div>

                <!-- Providers Grid -->
                <div id="providers-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="col-span-full py-12 text-center text-slate-400">
                        <i class="fa-solid fa-spinner fa-spin text-2xl mb-2 text-cyan-400 block"></i>
                        Memuat daftar AI provider...
                    </div>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 3: ENCRYPTED VAULT SECRETS ======================= -->
        <section id="view-vault" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-5xl mx-auto space-y-6">
                <!-- Header -->
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-apex-card p-6 rounded-2xl border border-apex-border shadow-lg">
                    <div>
                        <h2 class="text-xl font-bold text-white flex items-center gap-2">
                            <i class="fa-solid fa-shield-halved text-cyan-400"></i> Apex Encrypted Secret Vault
                        </h2>
                        <p class="text-xs text-slate-400 mt-1">Brankas enkripsi AES-256-GCM. Gunakan tag <code class="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded">{{vault:NAMA_SECRET}}</code> pada perintah terminal untuk injeksi otomatis tanpa membocorkan kredensial.</p>
                    </div>
                    <button onclick="openAddVaultModal()" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all flex items-center gap-2 shadow-md shrink-0">
                        <i class="fa-solid fa-plus"></i> Tambah Secret Baru
                    </button>
                </div>

                <!-- Vault Inventory Table -->
                <div class="bg-apex-card border border-apex-border rounded-xl overflow-hidden shadow-lg">
                    <table class="w-full text-left text-xs text-slate-200">
                        <thead class="bg-apex-dark text-slate-400 uppercase text-[10px] tracking-wider border-b border-apex-border">
                            <tr>
                                <th class="p-3.5">Secret Key Name</th>
                                <th class="p-3.5">Masked Value</th>
                                <th class="p-3.5">Deskripsi</th>
                                <th class="p-3.5">Placeholder</th>
                                <th class="p-3.5 text-right">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="vault-table-body" class="divide-y divide-apex-border">
                            <tr>
                                <td colspan="5" class="p-6 text-center text-slate-400">Memuat brankas kredensial...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 4: DOC & OCR READER ======================= -->
        <section id="view-docs" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-4xl mx-auto space-y-6">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-file-invoice text-cyan-400"></i> Universal Document & OCR Reader
                    </h2>
                    <p class="text-sm text-slate-400">Dukungan ekstraksi otomatis: PDF, Word (docx), Excel (xlsx), Gambar (OCR Tesseract), SQLite, ZIP/TAR, dan Text.</p>
                </div>

                <!-- Dropzone -->
                <div class="border-2 border-dashed border-apex-border hover:border-cyan-500/60 rounded-2xl p-8 text-center bg-apex-card/50 transition-all cursor-pointer" onclick="document.getElementById('doc-drop-input').click()">
                    <input type="file" id="doc-drop-input" class="hidden" onchange="uploadAndInspect(this.files[0])">
                    <i class="fa-solid fa-cloud-arrow-up text-4xl text-cyan-500 mb-3"></i>
                    <h3 class="text-base font-semibold text-slate-200">Klik atau Seret File ke Sini</h3>
                    <p class="text-xs text-slate-400 mt-1">Format didukung: .pdf, .docx, .xlsx, .png, .jpg, .db, .sqlite, .zip, .txt, .py, .json</p>
                </div>

                <!-- Result Inspector -->
                <div id="doc-result-container" class="hidden bg-apex-card border border-apex-border rounded-xl p-5 shadow-lg space-y-3">
                    <div class="flex items-center justify-between border-b border-apex-border pb-3">
                        <div class="flex items-center gap-2">
                            <i class="fa-solid fa-file-lines text-cyan-400"></i>
                            <span id="doc-result-filename" class="font-mono text-sm font-bold text-slate-200">document.pdf</span>
                        </div>
                        <button onclick="copyDocResult()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition-all flex items-center gap-1">
                            <i class="fa-solid fa-copy"></i> Salin Teks
                        </button>
                    </div>
                    <pre id="doc-result-text" class="text-xs font-mono text-slate-300 bg-apex-dark p-4 rounded-lg overflow-x-auto max-h-96 whitespace-pre-wrap"></pre>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 5: TOOLS EXPLORER ======================= -->
        <section id="view-tools" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-5xl mx-auto space-y-6">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h2 class="text-xl font-bold text-white flex items-center gap-2">
                            <i class="fa-solid fa-toolbox text-cyan-400"></i> Active Tool Registry
                        </h2>
                        <p class="text-sm text-slate-400">Daftar fungsi alat otonom yang dapat dipanggil langsung oleh model AI.</p>
                    </div>
                    <input type="text" id="tool-search" placeholder="Cari tool..." oninput="filterTools(this.value)" class="bg-apex-card border border-apex-border px-3 py-1.5 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500 w-64">
                </div>
                <div id="tools-grid" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Tool Cards populated by JS -->
                </div>
            </div>
        </section>

        <!-- ======================= TAB 6: METRICS & TOKENS ======================= -->
        <section id="view-stats" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-4xl mx-auto space-y-6">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-chart-line text-cyan-400"></i> Token Usage & System Metrics
                    </h2>
                    <p class="text-sm text-slate-400">Pantau konsumsi token, efisiensi kompresi RTK, dan model fallback aktif.</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div class="bg-apex-card border border-apex-border rounded-xl p-5 shadow-lg">
                        <div class="text-xs uppercase text-slate-400 font-semibold mb-1">Total Prompt Tokens</div>
                        <div id="stat-prompt-tokens" class="text-2xl font-bold text-cyan-400 font-mono">0</div>
                    </div>
                    <div class="bg-apex-card border border-apex-border rounded-xl p-5 shadow-lg">
                        <div class="text-xs uppercase text-slate-400 font-semibold mb-1">Total Completion Tokens</div>
                        <div id="stat-comp-tokens" class="text-2xl font-bold text-emerald-400 font-mono">0</div>
                    </div>
                    <div class="bg-apex-card border border-apex-border rounded-xl p-5 shadow-lg">
                        <div class="text-xs uppercase text-slate-400 font-semibold mb-1">Estimated Cost (USD)</div>
                        <div id="stat-cost" class="text-2xl font-bold text-yellow-400 font-mono">$0.0000</div>
                    </div>
                </div>

                <div class="bg-apex-card border border-apex-border rounded-xl p-5 shadow-lg space-y-3">
                    <h3 class="font-bold text-sm text-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-microchip text-cyan-400"></i> Host Environment Specs
                    </h3>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div class="p-3 bg-apex-dark rounded-lg border border-apex-border">
                            <span class="text-slate-400 block mb-0.5">Operating System</span>
                            <span id="spec-os" class="font-semibold text-slate-200 font-mono">-</span>
                        </div>
                        <div class="p-3 bg-apex-dark rounded-lg border border-apex-border">
                            <span class="text-slate-400 block mb-0.5">Python Version</span>
                            <span id="spec-py" class="font-semibold text-slate-200 font-mono">-</span>
                        </div>
                        <div class="p-3 bg-apex-dark rounded-lg border border-apex-border">
                            <span class="text-slate-400 block mb-0.5">Active Model</span>
                            <span id="spec-model" class="font-semibold text-cyan-400 font-mono truncate block">-</span>
                        </div>
                        <div class="p-3 bg-apex-dark rounded-lg border border-apex-border">
                            <span class="text-slate-400 block mb-0.5">Tool Count</span>
                            <span id="spec-tools" class="font-semibold text-emerald-400 font-mono">-</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <!-- ======================= MODAL: TAMBAH / LOGIN PROVIDER ======================= -->
    <div id="modal-add-provider" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-apex-card border border-apex-border rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-apex-border pb-3">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-plug text-cyan-400"></i>
                    <h3 class="font-bold text-base text-white">Tambah / Login Provider AI</h3>
                </div>
                <button onclick="closeAddProviderModal()" class="text-slate-400 hover:text-white transition-all text-sm">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- Quick Presets -->
            <div>
                <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1.5">Pilih Preset Cepat</label>
                <div class="grid grid-cols-3 sm:grid-cols-4 gap-1.5 text-xs">
                    <button type="button" onclick="selectPreset('tokenharbor')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">TokenHarbor</button>
                    <button type="button" onclick="selectPreset('openai')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">OpenAI</button>
                    <button type="button" onclick="selectPreset('anthropic')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">Anthropic</button>
                    <button type="button" onclick="selectPreset('gemini')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">Gemini</button>
                    <button type="button" onclick="selectPreset('groq')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">Groq</button>
                    <button type="button" onclick="selectPreset('openrouter')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">OpenRouter</button>
                    <button type="button" onclick="selectPreset('deepseek')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">DeepSeek</button>
                    <button type="button" onclick="selectPreset('ollama')" class="p-1.5 rounded-lg bg-slate-800 hover:bg-cyan-900/60 border border-slate-700 hover:border-cyan-500 text-center transition-all truncate">Ollama (Local)</button>
                </div>
            </div>

            <!-- Form -->
            <form id="provider-form" onsubmit="handleSaveProvider(event)" class="space-y-3 text-xs">
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Provider ID / Name</label>
                    <input type="text" id="prov-name" required placeholder="misal: tokenharbor, openai, custom-api" class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono">
                </div>
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">API Key / Token Rahasia</label>
                    <div class="relative">
                        <input type="password" id="prov-key" placeholder="sk-..." class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 pr-10 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono">
                        <button type="button" onclick="togglePasswordVisibility('prov-key')" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200">
                            <i class="fa-solid fa-eye text-xs"></i>
                        </button>
                    </div>
                </div>
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Base URL API (Opsional jika standar)</label>
                    <input type="url" id="prov-url" placeholder="https://api.openai.com/v1" class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono text-[11px]">
                </div>
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Model Default / Pilihan</label>
                    <input type="text" id="prov-model" placeholder="misal: gpt-4o, claude-3-7-sonnet, mimo-v2.6-flash" class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono">
                </div>

                <div class="space-y-2 pt-1 border-t border-apex-border">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="prov-make-active" class="rounded bg-slate-800 border-slate-700 text-cyan-600 focus:ring-0">
                        <span class="text-slate-300">Jadikan provider aktif saat ini</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="prov-auto-fetch" checked class="rounded bg-slate-800 border-slate-700 text-cyan-600 focus:ring-0">
                        <span class="text-slate-300">Tarik daftar model live otomatis dari API</span>
                    </label>
                </div>

                <div id="modal-provider-alert" class="hidden p-2.5 rounded-lg text-xs"></div>

                <div class="flex items-center justify-end gap-2 pt-2">
                    <button type="button" onclick="closeAddProviderModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-all">Batal</button>
                    <button type="submit" id="btn-save-provider" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl transition-all shadow-md flex items-center gap-2">
                        <span>Simpan & Verifikasi</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- ======================= MODAL: TAMBAH VAULT SECRET ======================= -->
    <div id="modal-add-vault" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-apex-card border border-apex-border rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-apex-border pb-3">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-lock text-cyan-400"></i>
                    <h3 class="font-bold text-base text-white">Simpan Secret ke Vault</h3>
                </div>
                <button onclick="closeAddVaultModal()" class="text-slate-400 hover:text-white transition-all text-sm">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <form id="vault-form" onsubmit="handleSaveVault(event)" class="space-y-3 text-xs">
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Secret Key Name (UPPERCASE)</label>
                    <input type="text" id="vault-key" required placeholder="misal: DATABASE_PASSWORD, AWS_KEY" class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono">
                </div>
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Secret Value (Plaintext)</label>
                    <input type="password" id="vault-val" required placeholder="Masukkan nilai rahasia..." class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono">
                </div>
                <div>
                    <label class="block text-slate-400 mb-1 font-medium">Deskripsi (Opsional)</label>
                    <input type="text" id="vault-desc" placeholder="misal: Password DB Staging PostgreSQL" class="w-full bg-apex-dark border border-apex-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500">
                </div>

                <div class="flex items-center justify-end gap-2 pt-2">
                    <button type="button" onclick="closeAddVaultModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-all">Batal</button>
                    <button type="submit" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl transition-all shadow-md">
                        Simpan ke Brankas (AES-256)
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Client-Side Scripting -->
    <script>
        let currentSession = "web_session";
        let activeWs = null;
        let cachedTools = [];
        let cachedProviders = [];
        let currentTab = 'chat';
        let currentCategory = 'all';

        // Tab Switching
        function switchTab(tab) {
            currentTab = tab;
            ['chat', 'providers', 'vault', 'docs', 'tools', 'stats'].forEach(t => {
                const view = document.getElementById(`view-${t}`);
                const btn = document.getElementById(`tab-${t}`);
                if (view) view.classList.add('hidden');
                if (btn) {
                    btn.classList.remove('bg-cyan-600', 'text-white');
                    btn.classList.add('text-slate-300');
                }
            });
            const activeView = document.getElementById(`view-${tab}`);
            const activeBtn = document.getElementById(`tab-${tab}`);
            if (activeView) activeView.classList.remove('hidden');
            if (activeBtn) {
                activeBtn.classList.add('bg-cyan-600', 'text-white');
                activeBtn.classList.remove('text-slate-300');
            }
            if (tab === 'providers') loadProviders();
            if (tab === 'vault') loadVault();
            if (tab === 'tools') loadTools();
            if (tab === 'stats') loadStatus();
        }

        // Initialize WebSocket Chat
        function connectWs() {
            const loc = window.location;
            const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${proto}//${loc.host}/ws/chat`;

            activeWs = new WebSocket(wsUrl);

            activeWs.onopen = () => {
                console.log("WebSocket connected to Apex");
            };

            activeWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'tool_start') {
                    showToolStatus(data.tool, data.args);
                } else if (data.type === 'tool_end') {
                    hideToolStatus();
                } else if (data.type === 'response') {
                    hideToolStatus();
                    appendMessage('assistant', data.content, data.elapsed);
                    enableInput(true);
                } else if (data.type === 'error') {
                    hideToolStatus();
                    appendMessage('assistant', `❌ **Error:** ${data.message}`);
                    enableInput(true);
                }
            };

            activeWs.onclose = () => {
                setTimeout(connectWs, 3000);
            };
        }

        function showToolStatus(tool, args) {
            const bar = document.getElementById('live-tool-bar');
            bar.classList.remove('hidden');
            const argsPreview = typeof args === 'object' ? JSON.stringify(args).slice(0, 50) : '';
            document.getElementById('live-tool-text').innerText = `⚡ Menjalankan tool: ${tool}(${argsPreview})...`;
        }

        function hideToolStatus() {
            document.getElementById('live-tool-bar').classList.add('hidden');
        }

        function handleSend(event) {
            if (event) event.preventDefault();
            const input = document.getElementById('prompt-input');
            const text = input.value.trim();
            if (!text) return;

            appendMessage('user', text);
            input.value = '';
            enableInput(false);

            if (activeWs && activeWs.readyState === WebSocket.OPEN) {
                activeWs.send(JSON.stringify({
                    session_id: currentSession,
                    prompt: text
                }));
            } else {
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ session_id: currentSession, prompt: text })
                })
                .then(r => r.json())
                .then(res => {
                    appendMessage('assistant', res.response, res.elapsed);
                    enableInput(true);
                })
                .catch(err => {
                    appendMessage('assistant', `❌ Kesalahan koneksi: ${err}`);
                    enableInput(true);
                });
            }
        }

        function appendMessage(role, content, elapsed = null) {
            const feed = document.getElementById('chat-messages');
            const wrap = document.createElement('div');
            wrap.className = `flex gap-3 max-w-3xl ${role === 'user' ? 'ml-auto justify-end' : 'mr-auto justify-start'}`;

            const isUser = role === 'user';
            const icon = isUser ? '👤' : '●';
            const bubbleBg = isUser ? 'bg-cyan-700/80 text-white rounded-2xl rounded-tr-none' : 'bg-apex-card border border-apex-border text-slate-200 rounded-2xl rounded-tl-none';

            let elapsedTag = elapsed ? `<div class="text-[10px] text-slate-500 mt-2 font-mono">⏱ ${elapsed}s</div>` : '';
            let htmlContent = isUser ? `<div class="whitespace-pre-wrap">${content}</div>` : marked.parse(content);

            wrap.innerHTML = `
                ${!isUser ? `<div class="w-8 h-8 rounded-lg bg-cyan-900/60 border border-cyan-700/50 flex items-center justify-center text-cyan-400 font-bold shrink-0 mt-1">${icon}</div>` : ''}
                <div class="p-4 ${bubbleBg} shadow-md overflow-hidden text-sm">
                    ${htmlContent}
                    ${elapsedTag}
                </div>
                ${isUser ? `<div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 shrink-0 mt-1">${icon}</div>` : ''}
            `;

            feed.appendChild(wrap);
            feed.scrollTop = feed.scrollHeight;

            wrap.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }

        function enableInput(enabled) {
            document.getElementById('send-button').disabled = !enabled;
            document.getElementById('prompt-input').disabled = !enabled;
            if (enabled) document.getElementById('prompt-input').focus();
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        }

        function setPrompt(text) {
            document.getElementById('prompt-input').value = text;
            document.getElementById('prompt-input').focus();
        }

        function newSession() {
            currentSession = `session_${Date.now()}`;
            document.getElementById('chat-messages').innerHTML = '';
            appendMessage('assistant', `✨ **Sesi Baru Dimulai:** \`${currentSession}\``);
        }

        // ======================= 9ROUTER AI PROVIDER HUB JS =======================

        async function loadProviders() {
            try {
                const res = await fetch('/api/providers').then(r => r.json());
                cachedProviders = res.providers || [];
                
                document.getElementById('hub-active-provider').innerText = (res.active_provider || 'tokenharbor').toUpperCase();
                document.getElementById('hub-active-model').innerText = res.active_model || 'mimo-v2.6-flash';
                document.getElementById('active-provider-display').innerText = `${res.active_provider.toUpperCase()} Active`;

                renderProviders(cachedProviders);
            } catch (e) {
                console.error("Gagal memuat provider:", e);
            }
        }

        function renderProviders(providers) {
            const grid = document.getElementById('providers-grid');
            grid.innerHTML = '';

            let list = providers;
            if (currentCategory !== 'all') {
                list = list.filter(p => p.category === currentCategory);
            }

            if (list.length === 0) {
                grid.innerHTML = `
                    <div class="col-span-full py-12 text-center text-slate-400 bg-apex-card border border-apex-border rounded-2xl">
                        <i class="fa-solid fa-ghost text-3xl mb-2 text-slate-600 block"></i>
                        Tidak ada provider yang cocok dengan filter ini.
                    </div>
                `;
                return;
            }

            list.forEach(p => {
                const card = document.createElement('div');
                const isAct = p.is_active;
                const isCfg = p.is_configured;

                card.className = `bg-apex-card border ${isAct ? 'border-cyan-500/80 shadow-cyan-500/10 shadow-lg' : isCfg ? 'border-apex-border hover:border-slate-600' : 'border-apex-border/50 opacity-80'} rounded-2xl p-5 flex flex-col justify-between transition-all space-y-4`;

                let statusBadge = isAct
                    ? `<span class="text-[10px] bg-emerald-950/80 text-emerald-400 border border-emerald-700/80 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> AKTIF SEKARANG</span>`
                    : isCfg
                    ? `<span class="text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded-full font-medium">Terkonfigurasi</span>`
                    : `<span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">Belum Diatur</span>`;

                let modelOptions = (p.models || []).map(m => `<option value="${m}">${m}</option>`).join('');
                if (!modelOptions) modelOptions = `<option value="">(Belum ada model)</option>`;

                card.innerHTML = `
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <div class="flex items-center gap-2.5">
                                <span class="text-2xl">${p.icon || '🤖'}</span>
                                <div>
                                    <h4 class="font-bold text-sm text-white">${p.name}</h4>
                                    <span class="text-[10px] text-slate-400 font-mono">${p.id}</span>
                                </div>
                            </div>
                            ${statusBadge}
                        </div>
                        <p class="text-xs text-slate-300 leading-relaxed mb-3 line-clamp-2">${p.description || '-'}</p>
                        
                        <div class="space-y-1.5 bg-apex-dark/70 p-2.5 rounded-xl border border-apex-border text-[11px] font-mono">
                            <div class="flex items-center justify-between text-slate-400">
                                <span>API Key:</span>
                                <span class="text-slate-200">${p.masked_key || (isCfg ? '••••••••' : '(Kosong)')}</span>
                            </div>
                            <div class="flex items-center justify-between text-slate-400">
                                <span>Tersedia:</span>
                                <span class="text-cyan-400">${p.model_count || 0} Model</span>
                            </div>
                        </div>
                    </div>

                    <div class="space-y-2 pt-2 border-t border-apex-border">
                        <div>
                            <label class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Pilih Model Target</label>
                            <select id="select-model-${p.id}" class="w-full bg-apex-dark border border-apex-border rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500">
                                ${modelOptions}
                            </select>
                        </div>

                        <div class="grid grid-cols-2 gap-1.5 pt-1">
                            <button onclick="handleUseProvider('${p.id}')" class="px-2.5 py-1.5 ${isAct ? 'bg-cyan-700 text-white font-semibold' : 'bg-cyan-600/80 hover:bg-cyan-600 text-white'} rounded-lg text-xs transition-all flex items-center justify-center gap-1 shadow-sm">
                                <i class="fa-solid fa-bolt text-[10px]"></i> ${isAct ? 'Aktif' : 'Gunakan'}
                            </button>
                            <button onclick="handleTestPing('${p.id}', this)" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs transition-all flex items-center justify-center gap-1">
                                <i class="fa-solid fa-satellite-dish text-[10px] text-yellow-400"></i> Tes Ping
                            </button>
                        </div>

                        <div class="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                            <button onclick="openEditProvider('${p.id}')" class="hover:text-cyan-400 transition-all flex items-center gap-1">
                                <i class="fa-solid fa-key"></i> Edit Key
                            </button>
                            <button onclick="handleFetchLiveModels('${p.id}', this)" class="hover:text-cyan-400 transition-all flex items-center gap-1">
                                <i class="fa-solid fa-arrows-rotate"></i> Tarik Model
                            </button>
                            ${isCfg && p.id !== 'antigravity' ? `
                            <button onclick="handleRemoveProvider('${p.id}')" class="hover:text-rose-400 transition-all flex items-center gap-1">
                                <i class="fa-solid fa-trash"></i>
                            </button>` : ''}
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function filterProviderCategory(cat, btn) {
            currentCategory = cat;
            document.querySelectorAll('.cat-pill').forEach(b => {
                b.classList.remove('bg-cyan-600', 'text-white');
                b.classList.add('bg-apex-card', 'text-slate-300');
            });
            btn.classList.add('bg-cyan-600', 'text-white');
            btn.classList.remove('bg-apex-card', 'text-slate-300');
            renderProviders(cachedProviders);
        }

        function searchProviders(query) {
            const q = query.toLowerCase().trim();
            if (!q) {
                renderProviders(cachedProviders);
                return;
            }
            const filtered = cachedProviders.filter(p => 
                p.id.toLowerCase().includes(q) || 
                p.name.toLowerCase().includes(q) || 
                (p.models || []).some(m => m.toLowerCase().includes(q))
            );
            renderProviders(filtered);
        }

        async function handleUseProvider(providerId) {
            const select = document.getElementById(`select-model-${providerId}`);
            const selectedModel = select ? select.value : '';

            try {
                const res = await fetch('/api/providers/use', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ provider: providerId, model: selectedModel })
                }).then(r => r.json());

                if (res.success) {
                    alert(`✅ Sukses beralih ke provider ${providerId.toUpperCase()} dengan model '${res.active_model}'!`);
                    loadProviders();
                    loadStatus();
                } else {
                    alert(`❌ Gagal beralih: ${res.message}`);
                }
            } catch (e) {
                alert(`❌ Kesalahan koneksi: ${e}`);
            }
        }

        async function handleTestPing(providerId, btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-[10px]"></i> Ping...`;
            btn.disabled = true;

            try {
                const res = await fetch('/api/config/test-provider', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ provider: providerId })
                }).then(r => r.json());

                if (res.success) {
                    const lat = res.latency_seconds ? Math.round(res.latency_seconds * 1000) : res.latency_ms;
                    btn.innerHTML = `<span class="text-emerald-400 font-mono font-bold">${lat} ms</span>`;
                } else {
                    btn.innerHTML = `<span class="text-rose-400 font-mono text-[10px]">Error</span>`;
                }
            } catch (e) {
                btn.innerHTML = `<span class="text-rose-400">Offline</span>`;
            } finally {
                setTimeout(() => {
                    btn.innerHTML = orig;
                    btn.disabled = false;
                }, 3000);
            }
        }

        async function testActiveProvider() {
            const cur = document.getElementById('hub-active-provider').innerText.toLowerCase();
            const latDisplay = document.getElementById('hub-active-latency');
            latDisplay.innerText = "Mengukur...";
            try {
                const res = await fetch('/api/config/test-provider', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ provider: cur })
                }).then(r => r.json());
                const lat = res.latency_seconds ? Math.round(res.latency_seconds * 1000) : res.latency_ms;
                latDisplay.innerText = res.success ? `${lat} ms` : 'Gagal';
            } catch (e) {
                latDisplay.innerText = 'Offline';
            }
        }

        async function handleFetchLiveModels(providerId, btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menarik...`;
            try {
                const res = await fetch('/api/providers/fetch-models', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: providerId })
                }).then(r => r.json());

                if (res.success) {
                    alert(`✅ Berhasil menarik ${res.models.length} model terbaru untuk ${providerId}!`);
                    loadProviders();
                } else {
                    alert(`⚠️ ${res.message}`);
                }
            } catch (e) {
                alert(`❌ Gagal: ${e}`);
            } finally {
                btn.innerHTML = orig;
            }
        }

        async function handleRemoveProvider(providerId) {
            if (!confirm(`Yakin ingin menghapus konfigurasi provider '${providerId}'?`)) return;
            try {
                const res = await fetch('/api/providers/remove', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: providerId })
                }).then(r => r.json());
                alert(res.message);
                loadProviders();
            } catch (e) {
                alert(`❌ Gagal: ${e}`);
            }
        }

        async function scanLocalEngines() {
            try {
                const res = await fetch('/api/providers/scan-local', { method: 'POST' }).then(r => r.json());
                if (res.found && res.found.length > 0) {
                    alert(`🎉 Berhasil mendeteksi ${res.found.length} AI lokal: ${res.found.join(', ')}`);
                } else {
                    alert("🔍 Tidak ditemukan server AI lokal aktif di port standar (Ollama 11434 atau vLLM 8000).");
                }
                loadProviders();
            } catch (e) {
                alert(`❌ Gagal scan AI lokal: ${e}`);
            }
        }

        // ======================= PRESET & MODAL HANDLER =======================

        const PRESETS = {
            tokenharbor: { name: 'tokenharbor', url: 'https://api.tokenharbor.com/v1', model: 'mimo-v2.6-flash:free' },
            openai: { name: 'openai', url: 'https://api.openai.com/v1', model: 'gpt-4o' },
            anthropic: { name: 'anthropic', url: 'https://api.anthropic.com/v1', model: 'claude-3-7-sonnet-20250219' },
            gemini: { name: 'gemini', url: 'https://generativelanguage.googleapis.com/v1beta/openai', model: 'gemini-2.5-flash' },
            groq: { name: 'groq', url: 'https://api.groq.com/openai/v1', model: 'llama-3.3-70b-versatile' },
            openrouter: { name: 'openrouter', url: 'https://openrouter.ai/api/v1', model: 'anthropic/claude-3.7-sonnet' },
            deepseek: { name: 'deepseek', url: 'https://api.deepseek.com', model: 'deepseek-chat' },
            ollama: { name: 'ollama', url: 'http://localhost:11434/v1', model: 'llama3:latest' }
        };

        function selectPreset(key) {
            const p = PRESETS[key];
            if (!p) return;
            document.getElementById('prov-name').value = p.name;
            document.getElementById('prov-url').value = p.url;
            document.getElementById('prov-model').value = p.model;
            document.getElementById('prov-key').focus();
        }

        function openAddProviderModal() {
            document.getElementById('provider-form').reset();
            document.getElementById('modal-provider-alert').classList.add('hidden');
            selectPreset('tokenharbor');
            document.getElementById('modal-add-provider').classList.remove('hidden');
        }

        function openEditProvider(providerId) {
            openAddProviderModal();
            const p = cachedProviders.find(x => x.id === providerId);
            if (p) {
                document.getElementById('prov-name').value = p.id;
                document.getElementById('prov-url').value = p.url || '';
                document.getElementById('prov-model').value = (p.models && p.models[0]) || '';
            }
        }

        function closeAddProviderModal() {
            document.getElementById('modal-add-provider').classList.add('hidden');
        }

        function togglePasswordVisibility(id) {
            const input = document.getElementById(id);
            input.type = input.type === 'password' ? 'text' : 'password';
        }

        async function handleSaveProvider(e) {
            e.preventDefault();
            const name = document.getElementById('prov-name').value.trim().toLowerCase();
            const key = document.getElementById('prov-key').value.trim();
            const url = document.getElementById('prov-url').value.trim();
            const model = document.getElementById('prov-model').value.trim();
            const makeActive = document.getElementById('prov-make-active').checked;
            const autoFetch = document.getElementById('prov-auto-fetch').checked;

            const btn = document.getElementById('btn-save-provider');
            const alertBox = document.getElementById('modal-provider-alert');
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menghubungkan...`;

            try {
                const res = await fetch('/api/providers/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: name,
                        api_key: key,
                        base_url: url,
                        models: model ? [model] : null,
                        auto_fetch: autoFetch,
                        verify_now: true,
                        make_active: makeActive
                    })
                }).then(r => r.json());

                if (res.success) {
                    alertBox.className = "p-2.5 rounded-lg text-xs bg-emerald-950/80 text-emerald-300 border border-emerald-700 block";
                    alertBox.innerText = `✅ ${res.message}`;
                    setTimeout(() => {
                        closeAddProviderModal();
                        loadProviders();
                        loadStatus();
                    }, 1200);
                } else {
                    alertBox.className = "p-2.5 rounded-lg text-xs bg-rose-950/80 text-rose-300 border border-rose-700 block";
                    alertBox.innerText = `⚠️ ${res.message}`;
                }
            } catch (err) {
                alertBox.className = "p-2.5 rounded-lg text-xs bg-rose-950/80 text-rose-300 border border-rose-700 block";
                alertBox.innerText = `❌ Kesalahan server: ${err}`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = `Simpan & Verifikasi`;
            }
        }

        // ======================= VAULT WEB MANAGER JS =======================

        async function loadVault() {
            try {
                const res = await fetch('/api/vault').then(r => r.json());
                const tbody = document.getElementById('vault-table-body');
                tbody.innerHTML = '';

                const secrets = res.secrets || [];
                if (secrets.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="5" class="p-6 text-center text-slate-500">
                                <i class="fa-solid fa-box-open text-2xl mb-2 block"></i>
                                Belum ada secret yang tersimpan di Vault.
                            </td>
                        </tr>
                    `;
                    return;
                }

                secrets.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-slate-800/40 transition-all font-mono";
                    tr.innerHTML = `
                        <td class="p-3.5 font-bold text-cyan-400 font-mono">${s.key}</td>
                        <td class="p-3.5 text-slate-300">${s.masked}</td>
                        <td class="p-3.5 text-slate-400 font-sans">${s.description || '-'}</td>
                        <td class="p-3.5 text-slate-400 text-[11px]"><code class="text-cyan-300 bg-slate-900 px-1 py-0.5 rounded">{{vault:${s.key}}}</code></td>
                        <td class="p-3.5 text-right font-sans">
                            <button onclick="handleDeleteVaultSecret('${s.key}')" class="text-rose-400 hover:text-rose-300 transition-all p-1">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                console.error("Gagal memuat vault:", e);
            }
        }

        function openAddVaultModal() {
            document.getElementById('vault-form').reset();
            document.getElementById('modal-add-vault').classList.remove('hidden');
        }

        function closeAddVaultModal() {
            document.getElementById('modal-add-vault').classList.add('hidden');
        }

        async function handleSaveVault(e) {
            e.preventDefault();
            const key = document.getElementById('vault-key').value.trim();
            const val = document.getElementById('vault-val').value.trim();
            const desc = document.getElementById('vault-desc').value.trim();

            try {
                const res = await fetch('/api/vault', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ key, value: val, description: desc })
                }).then(r => r.json());

                if (res.success) {
                    closeAddVaultModal();
                    loadVault();
                } else {
                    alert("❌ Gagal menyimpan secret ke vault.");
                }
            } catch (err) {
                alert(`❌ Kesalahan: ${err}`);
            }
        }

        async function handleDeleteVaultSecret(key) {
            if (!confirm(`Hapus secret '${key}' dari vault?`)) return;
            try {
                await fetch(`/api/vault/${key}`, { method: 'DELETE' });
                loadVault();
            } catch (e) {
                alert(`❌ Gagal menghapus: ${e}`);
            }
        }

        // ======================= METRICS & TOOLS JS =======================

        async function loadStatus() {
            try {
                const res = await fetch('/api/status').then(r => r.json());
                document.getElementById('active-model-display').innerText = res.active_model || 'Unknown';
                document.getElementById('spec-model').innerText = res.active_model || '-';
                document.getElementById('spec-os').innerText = res.system.os || '-';
                document.getElementById('spec-py').innerText = res.system.python || '-';
                document.getElementById('spec-tools').innerText = res.tools_count || '0';

                document.getElementById('stat-prompt-tokens').innerText = (res.token_usage.total_prompt_tokens || 0).toLocaleString();
                document.getElementById('stat-comp-tokens').innerText = (res.token_usage.total_completion_tokens || 0).toLocaleString();
                document.getElementById('stat-cost').innerText = `$${(res.token_usage.total_cost_usd || 0).toFixed(4)}`;
            } catch (e) {
                console.error("Failed to load status", e);
            }
        }

        async function loadTools() {
            try {
                const data = await fetch('/api/tools').then(r => r.json());
                cachedTools = data.tools || [];
                renderTools(cachedTools);
            } catch (e) {
                console.error("Failed to load tools", e);
            }
        }

        function renderTools(tools) {
            const grid = document.getElementById('tools-grid');
            grid.innerHTML = '';
            tools.forEach(t => {
                const card = document.createElement('div');
                card.className = "bg-apex-card border border-apex-border rounded-xl p-4 shadow-md space-y-2";
                const isSafe = t.is_safe ? '<span class="text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full">Safe / Read</span>' : '<span class="text-[10px] bg-amber-950/60 text-amber-400 border border-amber-800 px-2 py-0.5 rounded-full">Mutating / Execute</span>';
                card.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span class="font-mono font-bold text-sm text-cyan-400">${t.name}</span>
                        ${isSafe}
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">${t.description}</p>
                `;
                grid.appendChild(card);
            });
        }

        function filterTools(query) {
            const q = query.toLowerCase();
            const filtered = cachedTools.filter(t => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q));
            renderTools(filtered);
        }

        async function handleDocInspect(file) {
            if (!file) return;
            uploadAndInspect(file);
        }

        async function uploadAndInspect(file) {
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);

            document.getElementById('doc-result-container').classList.remove('hidden');
            document.getElementById('doc-result-filename').innerText = file.name;
            document.getElementById('doc-result-text').innerText = `⏳ Membaca dan mengekstrak isi ${file.name}...`;

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                }).then(r => r.json());

                document.getElementById('doc-result-text').innerText = res.parsed_content || res.error || '(Tanpa output)';
                switchTab('docs');
            } catch (e) {
                document.getElementById('doc-result-text').innerText = `❌ Gagal memproses file: ${e}`;
            }
        }

        function copyDocResult() {
            const txt = document.getElementById('doc-result-text').innerText;
            navigator.clipboard.writeText(txt);
            alert("Hasil inspeksi dokumen disalin ke clipboard!");
        }

        window.addEventListener('DOMContentLoaded', () => {
            loadStatus();
            connectWs();
        });
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> str:
    """Serve the interactive dashboard single page application."""
    return HTML_PAGE


@app.get("/api/status")
async def get_system_status() -> Dict[str, Any]:
    """Retrieve active AI model, host hardware specs, and token ledger summary."""
    active_m = config.default_model
    ledger_stats = token_ledger.get_summary()

    return {
        "status": "online",
        "active_model": active_m,
        "active_provider": config.active_provider,
        "default_model": config.default_model,
        "tools_count": len(tool_registry.get_tools()),
        "token_usage": ledger_stats,
        "system": {
            "os": f"{platform.system()} {platform.release()}",
            "arch": platform.machine(),
            "python": platform.python_version(),
            "user": os.environ.get("USER", "apex_operator")
        }
    }


@app.get("/api/vault")
async def list_vault_endpoint() -> Dict[str, Any]:
    """List masked secret keys from the AES-256-GCM vault."""
    return {"secrets": secret_vault.list_keys()}


@app.post("/api/vault")
async def set_vault_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Store an encrypted credential into the vault."""
    key = payload.get("key", "").strip().upper()
    val = payload.get("value", "").strip()
    desc = payload.get("description", "").strip()
    if not key or not val:
        raise HTTPException(status_code=400, detail="Key and value are required.")
    ok = secret_vault.set(key, val, description=desc)
    return {"success": ok, "key": key}


@app.delete("/api/vault/{key}")
async def delete_vault_endpoint(key: str) -> Dict[str, Any]:
    """Remove a secret from the vault."""
    ok = secret_vault.delete(key.strip().upper())
    return {"success": ok, "key": key}


@app.get("/api/tools")
async def list_registered_tools() -> Dict[str, Any]:
    """List all registered tools available to Apex."""
    tools = tool_registry.get_tools()
    tools_list = []
    for name, data in tools.items():
        tools_list.append({
            "name": name,
            "description": data.get("description", ""),
            "parameters": data.get("parameters", {}),
            "is_safe": data.get("is_safe", False)
        })
    return {"count": len(tools_list), "tools": tools_list}


@app.post("/api/chat")
async def chat_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a chat prompt and return response."""
    prompt = payload.get("prompt", "").strip()
    session_id = payload.get("session_id", "web_default")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong")

    start_t = time.time()
    response = default_agent.run(
        user_prompt=prompt,
        session_id=session_id,
        channel="web_http"
    )
    elapsed = round(time.time() - start_t, 2)
    return {
        "response": response,
        "elapsed": elapsed,
        "session_id": session_id
    }


@app.post("/api/upload")
async def upload_file_and_inspect(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a document or image and parse it with read_any_file."""
    dest_path = UPLOADS_DIR / file.filename
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse with omni-modal document reader
        ok, parsed_text = read_any_file(str(dest_path), offset_lines=0, limit_lines=1500, ocr=True)
        return {
            "success": ok,
            "filename": file.filename,
            "saved_path": str(dest_path),
            "parsed_content": parsed_text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/models")
async def list_available_models() -> Dict[str, Any]:
    """Retrieve list of all discovered and configured AI models."""
    from apex.router.model_switcher import model_switcher
    return {
        "models": model_switcher.get_available_models(),
        "active_model": config.default_model
    }


@app.post("/api/model/switch")
async def switch_model_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Switch active AI model dynamically in real time."""
    model_name = payload.get("model", "").strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="Nama model wajib diisi")
    from apex.router.model_switcher import model_switcher
    ok = model_switcher.switch_model(model_name)
    return {"success": ok, "active_model": config.default_model}


@app.post("/api/rag/index")
async def rag_index_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Index a folder or file into the local RAG knowledge base."""
    path = payload.get("path", ".").strip()
    from apex.memory.rag import rag_engine
    return rag_engine.index_path(path)


@app.get("/api/rag/search")
async def rag_search_endpoint(q: str, limit: int = 5) -> Dict[str, Any]:
    """Search knowledge base chunks."""
    from apex.memory.rag import rag_engine
    results = rag_engine.search(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@app.get("/api/export/{session_id}")
async def export_session_endpoint(session_id: str) -> Dict[str, Any]:
    """Export conversation session history to Markdown."""
    from apex.memory.sessions import session_manager
    session = session_manager.get_or_create(session_id)
    md_lines = [f"# Chat Session Export: {session_id}\n\nExported from Project Apex Dashboard\n"]
    for m in session.messages:
        role = m.get("role", "user").upper()
        content = m.get("content", "")
        md_lines.append(f"### 👤 {role}:\n{content}\n")
    return {"session_id": session_id, "markdown": "\n".join(md_lines)}


@app.get("/api/config")
async def get_config_endpoint() -> Dict[str, Any]:
    """Retrieve system configuration with masked API keys for safe viewing."""
    cfg = json.loads(json.dumps(config.raw))
    cfg["default_model"] = config.default_model
    cfg["active_provider"] = config.active_provider
    providers = cfg.get("providers", {})
    for p_id, p_data in providers.items():
        k = p_data.get("api_key", "")
        if k and k != "none":
            p_data["api_key_masked"] = f"{k[:4]}••••••••{k[-4:]}" if len(k) > 8 else "••••••••"
            p_data["has_key"] = True
            p_data.pop("api_key", None)
        else:
            p_data["api_key_masked"] = "none"
            p_data["has_key"] = False
    return cfg


@app.post("/api/config")
async def update_config_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update system configuration settings."""
    if "key" in payload and "value" in payload:
        config.set(payload["key"], payload["value"])
        return {"success": True, "message": "Konfigurasi berhasil disimpan"}
    for key, val in payload.items():
        if key.startswith("providers.") and key.endswith(".api_key"):
            if not val or "••••" in str(val):
                continue
        config.set(key, val, auto_save=False)
    config.save()
    return {"success": True, "message": "Konfigurasi berhasil disimpan ke disk"}


@app.post("/api/config/test-provider")
async def test_provider_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test connection to a specific provider."""
    p_name = payload.get("provider", "").strip().lower()
    ok, msg, lat = provider_manager.test_provider(p_name)
    return {
        "success": ok,
        "message": msg,
        "latency_seconds": lat,
        "latency_ms": round(lat * 1000, 1)
    }


@app.get("/api/config/profiles")
async def get_profiles_endpoint() -> Dict[str, Any]:
    """List all saved configuration profiles."""
    return {"profiles": config.list_profiles(), "active_profile": config.profile_name}


@app.post("/api/config/profiles/use")
async def switch_profile_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Switch active configuration profile."""
    name = payload.get("name", "").strip()
    if not name:
        return {"success": False, "message": "Nama profil tidak boleh kosong"}
    if config.load_profile(name):
        return {"success": True, "message": f"Berhasil beralih ke profil {name}", "active_profile": name}
    return {"success": False, "message": f"Profil {name} tidak ditemukan"}


@app.post("/api/config/profiles/save")
async def save_profile_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Save current configuration as a new profile."""
    name = payload.get("name", "").strip()
    if not name:
        return {"success": False, "message": "Nama profil tidak boleh kosong"}
    if config.save_profile(name):
        return {"success": True, "message": f"Konfigurasi berhasil disimpan sebagai profil {name}"}
    return {"success": False, "message": f"Gagal menyimpan profil {name}"}


@app.get("/api/setup/check")
async def setup_check_endpoint() -> Dict[str, Any]:
    """Run full setup and environment health check."""
    return config.validate_config()


@app.post("/api/setup/repair")
async def setup_repair_endpoint() -> Dict[str, Any]:
    """Auto-repair system directories and missing configuration keys."""
    actions = config.repair_config()
    return {"success": True, "actions": actions}


@app.post("/api/config/sync-env")
async def sync_env_endpoint() -> Dict[str, Any]:
    """Scan and synchronize API keys from environment variables and .env file."""
    updated = config.sync_environment_keys()
    return {"success": True, "updated": updated, "count": len(updated)}


# ---------------------------------------------------------
# Provider Management REST Endpoints
# ---------------------------------------------------------

@app.get("/api/providers")
async def list_providers_endpoint(category: str = "all") -> Dict[str, Any]:
    """Retrieve all providers (configured + catalog) with active indicators."""
    summary = provider_manager.get_provider_shelf_summary(category=category)
    return {
        "providers": summary,
        "active_provider": config.active_provider,
        "active_model": config.default_model,
        "count": len(summary)
    }


@app.get("/api/providers/search")
async def search_providers_endpoint(q: str = "") -> Dict[str, Any]:
    """Search providers and models by query keyword."""
    matches = provider_manager.search_providers(q)
    return {"query": q, "matches": matches, "count": len(matches)}


@app.post("/api/providers/use")
async def set_active_provider_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Switch active provider and model with live latency test."""
    p_name = payload.get("provider", "").strip().lower()
    m_name = payload.get("model", "").strip() or None
    ok, msg = provider_manager.set_active_provider(p_name, m_name)
    if not ok:
        return {"success": False, "message": msg}
    t_ok, t_msg, t_lat = provider_manager.test_provider(p_name)
    return {
        "success": True,
        "message": msg,
        "active_provider": config.active_provider,
        "active_model": config.default_model,
        "test_success": t_ok,
        "test_message": t_msg,
        "latency_seconds": t_lat
    }


@app.post("/api/providers/add")
async def add_provider_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Add or configure an AI provider with catalog defaults & key verification."""
    p_name = payload.get("name", "").strip().lower()
    key = payload.get("api_key", "").strip()
    url = payload.get("base_url", "").strip()
    models = payload.get("models")
    auto_fetch = payload.get("auto_fetch", True)
    verify_now = payload.get("verify_now", True)
    make_active = payload.get("make_active", False)

    ok, msg, detail = provider_manager.add_provider_smart(
        p_name,
        api_key=key,
        base_url=url,
        models=models,
        auto_fetch=auto_fetch,
        verify_now=verify_now
    )
    if ok and make_active:
        first_m = detail.get("models", [config.default_model])[0]
        provider_manager.set_active_provider(p_name, first_m)
    return {"success": ok, "message": msg, "detail": detail}


@app.post("/api/providers/remove")
async def remove_provider_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a provider from configuration."""
    p_name = payload.get("name", "").strip().lower()
    ok = provider_manager.remove_provider(p_name)
    return {"success": ok, "message": f"Provider '{p_name}' {'berhasil dihapus' if ok else 'tidak ditemukan'}"}


@app.post("/api/providers/scan-local")
async def scan_local_providers_endpoint() -> Dict[str, Any]:
    """Auto-scan host for local AI engines."""
    return provider_manager.scan_and_register_local_engines()


@app.post("/api/providers/fetch-models")
async def fetch_models_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch live models from provider API endpoint."""
    p_name = payload.get("name", "").strip().lower()
    ok, msg, models = provider_manager.fetch_live_models(p_name)
    return {"success": ok, "message": msg, "models": models}


# ---------------------------------------------------------
# WebSocket Real-Time Chat
# ---------------------------------------------------------

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """Real-time bi-directional streaming chat socket."""
    await websocket.accept()
    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            prompt = data.get("prompt", "").strip()
            session_id = data.get("session_id", "web_default")

            if not prompt:
                continue

            start_t = time.time()

            def on_tool_start(fn_name: str, args: Dict[str, Any]) -> None:
                asyncio.run(websocket.send_json({
                    "type": "tool_start",
                    "tool": fn_name,
                    "args": args
                }))

            def on_tool_end(fn_name: str, output: str, is_error: bool) -> None:
                asyncio.run(websocket.send_json({
                    "type": "tool_end",
                    "tool": fn_name,
                    "is_error": is_error
                }))

            # Execute via agent in background thread
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: default_agent.run(
                    user_prompt=prompt,
                    session_id=session_id,
                    channel="web_ws"
                )
            )

            elapsed = round(time.time() - start_t, 2)
            await websocket.send_json({
                "type": "response",
                "content": response_text,
                "elapsed": elapsed
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


def start_web_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run uvicorn ASGI server."""
    print(f"🚀 Project Apex 9Router Pro Web Dashboard berjalan di: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

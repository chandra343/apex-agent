"""Modern Interactive Web Gateway & Dashboard for Project Apex.

Provides:
- FastAPI Web Server + WebSocket Real-Time Chat
- Single-Page Application (SPA) with Dark Mode, Tailwind CSS, marked.js, highlight.js
- Live Tool Execution Monitoring
- Multi-Session Chat Management
- Omni-Modal Document Upload & OCR Inspector
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
    <title>Apex Sovereign AI — Agentic Dashboard</title>
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
                    <span class="text-xs bg-cyan-900/60 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-700/50">v1.0.0</span>
                </div>
                <div class="text-xs text-slate-400">Sovereign Hybrid AI Agent Engine</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <nav class="hidden md:flex items-center gap-2 bg-apex-dark p-1 rounded-xl border border-apex-border">
            <button onclick="switchTab('chat')" id="tab-chat" class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all bg-cyan-600 text-white shadow-sm flex items-center gap-2">
                <i class="fa-solid fa-terminal"></i> Chat Console
            </button>
            <button onclick="switchTab('docs')" id="tab-docs" class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-2">
                <i class="fa-solid fa-file-invoice"></i> Doc & OCR Reader
            </button>
            <button onclick="switchTab('tools')" id="tab-tools" class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-2">
                <i class="fa-solid fa-toolbox"></i> Tools Explorer
            </button>
            <button onclick="switchTab('stats')" id="tab-stats" class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:text-white flex items-center gap-2">
                <i class="fa-solid fa-chart-line"></i> Tokens & Metrics
            </button>
        </nav>

        <!-- Right System Indicators -->
        <div class="flex items-center gap-4">
            <div class="text-right hidden sm:block">
                <div id="active-model-display" class="text-xs font-mono font-semibold text-cyan-400">Loading model...</div>
                <div class="text-[10px] text-emerald-400 flex items-center justify-end gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Host Connected
                </div>
            </div>
            <button onclick="loadStatus()" title="Refresh Status" class="w-8 h-8 rounded-lg bg-apex-border/60 hover:bg-apex-border text-slate-300 flex items-center justify-center transition-all">
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
                            Apex adalah asisten rekayasa otonom dengan akses host lokal, pembaca dokumen omni-modal, sub-agent swarm, database query, dan eksekutor terminal Bash terintegrasi.
                        </p>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Bantu cek spesifikasi sistem host dan ruang disk')">
                                <span class="font-semibold text-cyan-400">🔍 Cek Spesifikasi Host:</span> "Bantu cek spesifikasi sistem host dan ruang disk"
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Tampilkan daftar tabel pada database ~/.apex/memory.db')">
                                <span class="font-semibold text-cyan-400">📊 Query Database:</span> "Tampilkan daftar tabel pada database ~/.apex/memory.db"
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Tuliskan ringkasan dokumen atau file di direktori ini')">
                                <span class="font-semibold text-cyan-400">📄 Baca Dokumen:</span> "Tuliskan ringkasan dokumen atau file di direktori ini"
                            </div>
                            <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 transition-all cursor-pointer" onclick="setPrompt('Jalankan sub-agent swarm untuk riset dan verifikasi arsitektur')">
                                <span class="font-semibold text-cyan-400">👥 Sub-Agent Swarm:</span> "Jalankan sub-agent swarm untuk riset dan verifikasi arsitektur"
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Live Thinking / Tool Chip Bar -->
                <div id="live-tool-bar" class="px-6 py-2 bg-slate-900/90 border-t border-apex-border text-xs hidden flex items-center justify-between text-cyan-300">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-spinner fa-spin text-cyan-400"></i>
                        <span id="live-tool-text">Mengeksekusi operasi...</span>
                    </div>
                    <span id="live-tool-timer" class="text-slate-400 font-mono">0.0s</span>
                </div>

                <!-- Input Footer -->
                <div class="p-4 bg-apex-card border-t border-apex-border">
                    <form onsubmit="handleSend(event)" class="max-w-4xl mx-auto flex items-end gap-2">
                        <div class="flex-1 relative bg-apex-dark border border-apex-border rounded-xl focus-within:border-cyan-500 transition-all shadow-inner">
                            <textarea id="prompt-input" rows="2" placeholder="Ketik perintah atau tugas teknis untuk Apex (misal: 'periksa port terbuka', '$ ls -la', 'baca file')..."
                                class="w-full bg-transparent p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-36"
                                onkeydown="handleKeyDown(event)"></textarea>
                            <div class="flex items-center justify-between px-3 pb-2 text-xs text-slate-500">
                                <span class="flex items-center gap-2">
                                    <i class="fa-solid fa-keyboard"></i> Shift+Enter untuk baris baru · Awalan <b>$</b> untuk shell langsung
                                </span>
                                <label for="file-upload-input" title="Upload & Inspect Document" class="cursor-pointer hover:text-cyan-400 transition-all flex items-center gap-1">
                                    <i class="fa-solid fa-paperclip"></i> Lampirkan File
                                </label>
                                <input type="file" id="file-upload-input" class="hidden" onchange="uploadAndInspect(this.files[0])">
                            </div>
                        </div>
                        <button type="submit" id="send-button" class="h-12 w-12 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white flex items-center justify-center shadow-lg shadow-cyan-600/30 transition-all disabled:opacity-50">
                            <i class="fa-solid fa-paper-plane text-base"></i>
                        </button>
                    </form>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 2: DOC & OCR READER ======================= -->
        <section id="view-docs" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-4xl mx-auto space-y-6">
                <div class="bg-apex-card border border-apex-border rounded-2xl p-6 shadow-xl">
                    <h2 class="text-xl font-bold text-white mb-2 flex items-center gap-2">
                        <i class="fa-solid fa-file-invoice text-cyan-400"></i> Universal Omni-Modal Document & OCR Inspector
                    </h2>
                    <p class="text-sm text-slate-300 mb-4 leading-relaxed">
                        Pilih dokumen atau file apa pun dari komputer Anda (PDF, Word <code>.docx</code>, Excel <code>.xlsx</code>, gambar dengan Tesseract OCR, SQLite <code>.db</code>, atau arsip <code>.zip</code>). Apex akan mengekstrak kontennya secara lokal.
                    </p>
                    <div class="border-2 border-dashed border-apex-border hover:border-cyan-500 rounded-xl p-8 text-center bg-apex-dark/50 transition-all cursor-pointer" onclick="document.getElementById('doc-picker-input').click()">
                        <i class="fa-solid fa-cloud-arrow-up text-3xl text-cyan-400 mb-2"></i>
                        <div class="font-semibold text-slate-200">Klik untuk memilih file atau tarik ke sini</div>
                        <div class="text-xs text-slate-400 mt-1">Mendukung PDF, DOCX, XLSX, PNG, JPG, ZIP, TAR, DB</div>
                        <input type="file" id="doc-picker-input" class="hidden" onchange="handleDocInspect(this.files[0])">
                    </div>
                </div>

                <!-- Results Output -->
                <div id="doc-result-container" class="hidden bg-apex-card border border-apex-border rounded-2xl p-6 shadow-xl">
                    <div class="flex items-center justify-between pb-3 mb-4 border-b border-apex-border">
                        <span id="doc-result-filename" class="font-mono text-sm text-cyan-400 font-bold">output.txt</span>
                        <button onclick="copyDocResult()" class="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded text-slate-300">
                            <i class="fa-regular fa-copy"></i> Salin
                        </button>
                    </div>
                    <pre id="doc-result-text" class="text-xs font-mono text-slate-200 overflow-x-auto whitespace-pre-wrap max-h-96 bg-apex-dark p-4 rounded-xl border border-apex-border"></pre>
                </div>
            </div>
        </section>

        <!-- ======================= TAB 3: TOOLS EXPLORER ======================= -->
        <section id="view-tools" class="flex-1 p-6 overflow-y-auto hidden">
            <div class="max-w-5xl mx-auto space-y-6">
                <div class="flex items-center justify-between">
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

        <!-- ======================= TAB 4: METRICS & TOKENS ======================= -->
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

    <!-- Client-Side Scripting -->
    <script>
        let currentSession = "web_session";
        let activeWs = null;
        let cachedTools = [];

        // Tab Switching
        function switchTab(tab) {
            ['chat', 'docs', 'tools', 'stats'].forEach(t => {
                document.getElementById(`view-${t}`).classList.add('hidden');
                document.getElementById(`tab-${t}`).classList.remove('bg-cyan-600', 'text-white');
                document.getElementById(`tab-${t}`).classList.add('text-slate-300');
            });
            document.getElementById(`view-${tab}`).classList.remove('hidden');
            document.getElementById(`tab-${tab}`).classList.add('bg-cyan-600', 'text-white');
            document.getElementById(`tab-${tab}`).classList.remove('text-slate-300');
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
                console.warn("WebSocket closed, retrying in 3s...");
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
                // Fallback to HTTP API
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

            // Highlight syntax in rendered code
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

        // Status & Metrics
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

        // Tools Explorer
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

        // Document Inspection Handler
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

        // Init on page load
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
        "default_model": config.default_model,
        "tools_count": len(tool_registry.get_tools()),
        "token_usage": ledger_stats,
        "system": {
            "os": f"{platform.system()} {platform.release()}",
            "arch": platform.machine(),
            "python": platform.python_version(),
            "workspace": str(config.workspace)
        }
    }


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
    try:
        response_text = default_agent.run(prompt, session_id=session_id, channel="web")
        elapsed = round(time.time() - start_t, 2)
        return {
            "success": True,
            "session_id": session_id,
            "response": response_text,
            "elapsed": elapsed
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    print(f"🚀 Project Apex Web Dashboard berjalan di: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

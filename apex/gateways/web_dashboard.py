"""Pixel-Perfect Endpoint Proxy & 9Router AI Gateway Web Dashboard for Project Apex.

Provides:
- Exact Dark macOS Theme Matching Endpoint Proxy / 9Router
- Categorized Provider Layout: OAuth Providers, Free Providers, API Key Providers, Compatible Providers
- Card Grid with Brand Icons, Connected Status Dots, Active Toggle Switches
- Interactive Provider Configuration Modal (Key input, Model selector, Live Latency Test)
- Batch 'Test All' Ping Latency Benchmarker
- Integrated Chat Console, Vault Secrets Manager, and Usage Analytics
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


app = FastAPI(title="Apex Endpoint Proxy & AI Gateway", version="1.0.0")

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
# Embedded Pixel-Perfect Endpoint Proxy & 9Router Dashboard
# ---------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Endpoint Proxy — Providers</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Marked.js (Markdown) -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- Highlight.js -->
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
                        dark: {
                            sidebar: '#121316',
                            bg: '#17181c',
                            card: '#1e1f24',
                            cardHover: '#25272e',
                            border: '#282a30',
                            borderLight: '#383a42',
                            activeNav: '#2c1b18'
                        },
                        brand: {
                            orange: '#f97316',
                            orangeDark: '#ea580c',
                            coral: '#ff6b4a'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #121316; }
        ::-webkit-scrollbar-thumb { background: #282a30; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #383a42; }
        .nav-item-active { background-color: #2c1b18; color: #f97316; border-color: rgba(249, 115, 22, 0.3); }
    </style>
</head>
<body class="bg-dark-bg text-[#e4e4e7] min-h-screen flex font-sans antialiased select-none">

    <!-- LEFT SIDEBAR -->
    <aside class="w-64 bg-dark-sidebar border-r border-dark-border flex flex-col justify-between shrink-0 h-screen sticky top-0 p-4">
        <div class="space-y-6">
            <!-- macOS Window Controls & Branding -->
            <div class="space-y-4">
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-[#ff5f56] inline-block shadow-sm"></span>
                    <span class="w-3 h-3 rounded-full bg-[#ffbd2e] inline-block shadow-sm"></span>
                    <span class="w-3 h-3 rounded-full bg-[#27c93f] inline-block shadow-sm"></span>
                </div>
                <div class="flex items-center gap-3 pt-1">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-orange-500/20">
                        <i class="fa-solid fa-network-wired text-sm"></i>
                    </div>
                    <div>
                        <div class="font-bold text-sm tracking-wide text-white flex items-center gap-1.5">
                            <span>Endpoint Proxy</span>
                        </div>
                        <div class="text-[11px] text-[#71717a] font-mono">PROJECT APEX <span class="text-orange-400 font-semibold">v0.3.40</span></div>
                    </div>
                </div>
            </div>

            <!-- Main Nav Items -->
            <nav class="space-y-1">
                <button onclick="switchTab('endpoint')" id="nav-endpoint" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-terminal text-sm w-4 text-center"></i> Chat Console
                </button>
                <button onclick="switchTab('providers')" id="nav-providers" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium nav-item-active transition-all">
                    <i class="fa-solid fa-cubes text-sm w-4 text-center text-brand-orange"></i> Providers
                </button>
                <button onclick="switchTab('vault')" id="nav-vault" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-key text-sm w-4 text-center"></i> Proxy Pools & Vault
                </button>
                <button onclick="switchTab('stats')" id="nav-stats" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-chart-simple text-sm w-4 text-center"></i> Usage
                </button>
                <button onclick="switchTab('docs')" id="nav-docs" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-file-invoice text-sm w-4 text-center"></i> CLI Tools & OCR
                </button>
                <button onclick="switchTab('tools')" id="nav-tools" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-toolbox text-sm w-4 text-center"></i> Active Tools
                </button>
            </nav>

            <!-- Debug & System Sections -->
            <div class="space-y-3 pt-3 border-t border-dark-border/60">
                <div class="text-[10px] font-bold uppercase tracking-wider text-[#71717a] px-3">System</div>
                <div class="space-y-1">
                    <button onclick="switchTab('settings')" id="nav-settings" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                        <i class="fa-solid fa-gear text-sm w-4 text-center"></i> Settings
                    </button>
                </div>
            </div>
        </div>

        <!-- Sidebar Footer Warning & Shutdown -->
        <div class="bg-dark-card/50 border border-dark-border rounded-xl p-3 space-y-2.5 text-[11px]">
            <div class="flex items-start gap-2 text-[#a1a1aa] leading-relaxed">
                <i class="fa-solid fa-circle-info text-cyan-400 mt-0.5 shrink-0"></i>
                <span>Service is running in terminal. You can close this web page. Shutdown will stop the service.</span>
            </div>
            <button onclick="handleShutdown()" class="w-full py-1.5 rounded-lg border border-dark-border hover:border-rose-500/60 bg-dark-bg/80 text-slate-300 hover:text-rose-400 font-medium transition-all flex items-center justify-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-power-off text-xs text-rose-500"></i> Shutdown
            </button>
        </div>
    </aside>

    <!-- RIGHT MAIN CONTENT AREA -->
    <div class="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">

        <!-- Top Header Bar -->
        <header class="h-14 border-b border-dark-border px-8 flex items-center justify-between sticky top-0 bg-dark-bg/95 backdrop-blur z-20">
            <div>
                <span id="breadcrumb-title" class="text-xs font-medium text-[#a1a1aa]">Endpoint Proxy / Providers</span>
            </div>
            <div class="flex items-center gap-5 text-xs text-[#a1a1aa]">
                <div class="flex items-center gap-1.5 cursor-pointer hover:text-white transition-all">
                    <i class="fa-solid fa-globe"></i>
                    <span>English</span>
                    <i class="fa-solid fa-chevron-down text-[10px] ml-0.5"></i>
                </div>
                <button title="Toggle Theme" class="hover:text-white transition-all">
                    <i class="fa-regular fa-sun text-sm"></i>
                </button>
                <button onclick="handleShutdown()" title="Exit / Shutdown" class="hover:text-rose-400 transition-all">
                    <i class="fa-solid fa-arrow-right-from-bracket text-sm"></i>
                </button>
            </div>
        </header>

        <!-- MAIN VIEW: PROVIDERS (Pixel-Perfect Matching Screenshot) -->
        <main id="view-providers" class="p-8 space-y-8 flex-1 max-w-7xl">
            <!-- Page Title Header -->
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Providers</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Manage your AI provider connections</p>
            </div>

            <!-- SECTION 1: OAuth Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">OAuth Providers</h2>
                    <button onclick="testCategoryProviders('oauth', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-oauth" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <!-- Populated via JS -->
                </div>
            </section>

            <!-- SECTION 2: Free Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">Free Providers</h2>
                    <button onclick="testCategoryProviders('free', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-free" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <!-- Populated via JS -->
                </div>
            </section>

            <!-- SECTION 3: API Key Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">API Key Providers</h2>
                    <button onclick="testCategoryProviders('api_key', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-api-key" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <!-- Populated via JS -->
                </div>
            </section>

            <!-- SECTION 4: API Key Compatible Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between flex-wrap gap-2">
                    <h2 class="text-sm font-semibold text-white tracking-wide">API Key Compatible Providers</h2>
                    <div class="flex items-center gap-2">
                        <button onclick="openCompatibleModal('anthropic')" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#f97316] hover:bg-[#ea580c] text-white transition-all flex items-center gap-1.5 shadow-sm">
                            <i class="fa-solid fa-plus text-[10px]"></i> Add Anthropic Compatible
                        </button>
                        <button onclick="openCompatibleModal('openai')" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-white hover:bg-slate-200 text-slate-900 transition-all flex items-center gap-1.5 shadow-sm">
                            <i class="fa-solid fa-plus text-[10px]"></i> Add OpenAI Compatible
                        </button>
                    </div>
                </div>
                <div id="grid-compatible" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <!-- Populated via JS -->
                </div>
            </section>
        </main>

        <!-- OTHER TABS (Chat Console, Vault, Stats, Docs, Tools) -->
        <!-- TAB: Chat Console -->
        <section id="view-endpoint" class="p-8 hidden flex-1 flex flex-col h-full overflow-hidden">
            <div class="flex-1 flex flex-col bg-dark-sidebar border border-dark-border rounded-2xl overflow-hidden shadow-2xl max-w-5xl mx-auto w-full">
                <div class="p-4 border-b border-dark-border flex items-center justify-between bg-dark-card/60">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span class="font-bold text-xs text-white">Interactive Chat Console</span>
                        <span id="chat-active-model-badge" class="text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800/60 px-2 py-0.5 rounded font-mono">Loading model...</span>
                    </div>
                    <button onclick="newSession()" class="text-xs text-[#a1a1aa] hover:text-white px-2.5 py-1 rounded-md border border-dark-border bg-dark-bg/80 transition-all">
                        <i class="fa-solid fa-plus text-[10px]"></i> New Session
                    </button>
                </div>
                <div id="chat-messages" class="flex-1 overflow-y-auto p-6 space-y-4 text-sm">
                    <div class="p-4 bg-dark-card border border-dark-border rounded-xl text-xs text-slate-300 max-w-2xl">
                        🚀 <b>Apex Endpoint Proxy Console</b> siap melayani instruksi Anda. Gunakan tab <b>Providers</b> untuk menghubungkan API Key atau login akun AI Anda.
                    </div>
                </div>
                <div class="p-4 border-t border-dark-border bg-dark-card/40">
                    <div class="flex items-center gap-2 bg-dark-bg border border-dark-border rounded-xl p-2 focus-within:border-orange-500 transition-all">
                        <textarea id="prompt-input" rows="1" onkeydown="handleKeyDown(event)" placeholder="Ketik instruksi atau perintah terminal untuk Apex... (Shift+Enter untuk baris baru)" class="w-full bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1.5"></textarea>
                        <button id="send-button" onclick="handleSend()" class="bg-orange-600 hover:bg-orange-500 text-white w-8 h-8 rounded-lg flex items-center justify-center transition-all shrink-0">
                            <i class="fa-solid fa-arrow-up text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB: Proxy Pools & Vault -->
        <section id="view-vault" class="p-8 hidden space-y-6 max-w-5xl mx-auto w-full">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-white">Proxy Pools & Vault Secrets</h2>
                    <p class="text-xs text-[#8e8e93] mt-1">Brankas AES-256-GCM untuk kredensial terenkripsi & pool kunci cadangan.</p>
                </div>
                <button onclick="openAddVaultModal()" class="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5">
                    <i class="fa-solid fa-plus text-[10px]"></i> Add Secret
                </button>
            </div>
            <div class="bg-dark-card border border-dark-border rounded-xl overflow-hidden shadow-xl">
                <table class="w-full text-left text-xs text-slate-200">
                    <thead class="bg-dark-sidebar text-slate-400 uppercase text-[10px] tracking-wider border-b border-dark-border">
                        <tr>
                            <th class="p-3.5">Secret Key</th>
                            <th class="p-3.5">Masked Preview</th>
                            <th class="p-3.5">Deskripsi</th>
                            <th class="p-3.5">Template Tag</th>
                            <th class="p-3.5 text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody id="vault-table-body" class="divide-y divide-dark-border">
                        <tr><td colspan="5" class="p-6 text-center text-slate-500">Memuat brankas...</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- TAB: Usage Metrics -->
        <section id="view-stats" class="p-8 hidden space-y-6 max-w-5xl mx-auto w-full">
            <div>
                <h2 class="text-xl font-bold text-white">Usage & System Metrics</h2>
                <p class="text-xs text-[#8e8e93] mt-1">Audit token realtime dan konsumsi resource per provider.</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Total Prompt Tokens</div>
                    <div id="stat-prompt-tokens" class="text-2xl font-bold text-orange-400 font-mono">0</div>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Total Completion Tokens</div>
                    <div id="stat-comp-tokens" class="text-2xl font-bold text-emerald-400 font-mono">0</div>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Estimated Cost (USD)</div>
                    <div id="stat-cost" class="text-2xl font-bold text-yellow-400 font-mono">$0.0000</div>
                </div>
            </div>
        </section>

        <!-- TAB: CLI Tools & OCR -->
        <section id="view-docs" class="p-8 hidden space-y-6 max-w-4xl mx-auto w-full">
            <div>
                <h2 class="text-xl font-bold text-white">CLI Tools & Universal OCR Reader</h2>
                <p class="text-xs text-[#8e8e93] mt-1">Ekstraksi dokumen omni-modal (PDF, DOCX, XLSX, Image OCR, SQLite).</p>
            </div>
            <div class="border-2 border-dashed border-dark-border hover:border-orange-500/60 rounded-2xl p-8 text-center bg-dark-card/40 transition-all cursor-pointer" onclick="document.getElementById('doc-drop-input').click()">
                <input type="file" id="doc-drop-input" class="hidden" onchange="uploadAndInspect(this.files[0])">
                <i class="fa-solid fa-cloud-arrow-up text-3xl text-orange-400 mb-3"></i>
                <h3 class="text-sm font-semibold text-slate-200">Klik atau Seret Dokumen ke Sini</h3>
                <p class="text-[11px] text-slate-400 mt-1">Didukung: .pdf, .docx, .xlsx, .png, .jpg, .db, .txt</p>
            </div>
            <div id="doc-result-container" class="hidden bg-dark-card border border-dark-border rounded-xl p-4 shadow-lg space-y-2">
                <div class="flex items-center justify-between border-b border-dark-border pb-2 text-xs">
                    <span id="doc-result-filename" class="font-mono font-bold text-slate-200">file.txt</span>
                    <button onclick="copyDocResult()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-copy"></i> Copy</button>
                </div>
                <pre id="doc-result-text" class="text-xs font-mono text-slate-300 bg-dark-sidebar p-3 rounded-lg overflow-x-auto max-h-80 whitespace-pre-wrap"></pre>
            </div>
        </section>

        <!-- TAB: Tools -->
        <section id="view-tools" class="p-8 hidden space-y-6 max-w-5xl mx-auto w-full">
            <div>
                <h2 class="text-xl font-bold text-white">Active Registered Tools</h2>
                <p class="text-xs text-[#8e8e93] mt-1">Daftar fungsi sistem yang dapat dipanggil ReAct Agent.</p>
            </div>
            <div id="tools-grid" class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs"></div>
        </section>

    </div>

    <!-- MODAL: CONFIGURE PROVIDER / ADD KEY -->
    <div id="modal-provider" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-dark-card border border-dark-borderLight rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 text-xs">
            <div class="flex items-center justify-between border-b border-dark-border pb-3">
                <div class="flex items-center gap-3">
                    <div id="modal-prov-icon" class="w-8 h-8 rounded-lg flex items-center justify-center text-base">🤖</div>
                    <div>
                        <h3 id="modal-prov-name" class="font-bold text-sm text-white">Configure Provider</h3>
                        <span id="modal-prov-status-tag" class="text-[10px] text-slate-400 font-mono">OAuth / API Key</span>
                    </div>
                </div>
                <button onclick="closeModalProvider()" class="text-slate-400 hover:text-white text-base">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <form id="form-provider-config" onsubmit="handleSaveProviderConfig(event)" class="space-y-3.5">
                <input type="hidden" id="input-prov-id">

                <div>
                    <label class="block text-slate-300 mb-1 font-medium">API Key / Token Rahasia</label>
                    <div class="relative">
                        <input type="password" id="input-prov-key" placeholder="Paste API Key di sini (sk-...)..." class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 pr-10 text-slate-100 focus:outline-none focus:border-orange-500 font-mono">
                        <button type="button" onclick="togglePass('input-prov-key')" class="absolute right-3 top-2.5 text-slate-400 hover:text-white">
                            <i class="fa-solid fa-eye text-xs"></i>
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Base URL (Opsional jika standar)</label>
                    <input type="url" id="input-prov-url" placeholder="https://api.openai.com/v1" class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-orange-500 font-mono text-[11px]">
                </div>

                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Pilih Model Default</label>
                    <div class="flex gap-2">
                        <select id="select-prov-models" class="flex-1 bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                            <!-- Populated via JS -->
                        </select>
                        <button type="button" onclick="handleFetchModelsInModal()" class="px-3 py-2 bg-dark-border hover:bg-dark-borderLight text-slate-200 rounded-lg transition-all" title="Tarik model live dari API">
                            <i class="fa-solid fa-arrows-rotate"></i>
                        </button>
                    </div>
                </div>

                <div class="p-3 bg-dark-sidebar/60 border border-dark-border rounded-xl space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-slate-300">Set sebagai Provider Utama Saat Ini</span>
                        <input type="checkbox" id="check-make-active" class="rounded bg-slate-800 border-slate-700 text-orange-600 focus:ring-0 w-4 h-4 cursor-pointer">
                    </div>
                    <div class="flex items-center justify-between pt-1 border-t border-dark-border/40">
                        <span class="text-slate-300">Latency Test: <span id="modal-latency-display" class="font-mono text-emerald-400 font-bold ml-1">-</span></span>
                        <button type="button" onclick="handleTestPingInModal()" class="text-[11px] text-orange-400 hover:text-orange-300 font-medium">
                            <i class="fa-solid fa-bolt mr-1"></i> Ping Sekarang
                        </button>
                    </div>
                </div>

                <div id="modal-alert-box" class="hidden p-2.5 rounded-lg text-xs"></div>

                <div class="flex items-center justify-between pt-2">
                    <button type="button" onclick="handleDeleteProviderInModal()" id="btn-delete-prov" class="text-rose-400 hover:text-rose-300 transition-all flex items-center gap-1">
                        <i class="fa-solid fa-trash text-xs"></i> Hapus Konfigurasi
                    </button>
                    <div class="flex items-center gap-2">
                        <button type="button" onclick="closeModalProvider()" class="px-4 py-2 bg-dark-sidebar hover:bg-dark-border text-slate-300 rounded-xl transition-all">Batal</button>
                        <button type="submit" id="btn-save-prov" class="px-5 py-2 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-xl transition-all shadow-md">
                            Simpan & Hubungkan
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL: ADD SECRET VAULT -->
    <div id="modal-add-vault" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-dark-card border border-dark-borderLight rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 text-xs">
            <div class="flex items-center justify-between border-b border-dark-border pb-3">
                <h3 class="font-bold text-sm text-white">Add Encrypted Secret</h3>
                <button onclick="closeAddVaultModal()" class="text-slate-400 hover:text-white text-base">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <form onsubmit="handleSaveVault(event)" class="space-y-3">
                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Secret Key Name (UPPERCASE)</label>
                    <input type="text" id="vault-key" required placeholder="AWS_SECRET_KEY, DATABASE_PASSWORD" class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                </div>
                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Secret Value</label>
                    <input type="password" id="vault-val" required placeholder="Paste plaintext secret..." class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                </div>
                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Deskripsi (Opsional)</label>
                    <input type="text" id="vault-desc" placeholder="Keterangan singkat secret..." class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-orange-500">
                </div>
                <div class="flex items-center justify-end gap-2 pt-2">
                    <button type="button" onclick="closeAddVaultModal()" class="px-4 py-2 bg-dark-sidebar hover:bg-dark-border text-slate-300 rounded-xl transition-all">Batal</button>
                    <button type="submit" class="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-xl transition-all shadow-md">Simpan Secret</button>
                </div>
            </form>
        </div>
    </div>

    <!-- CLIENT SCRIPT -->
    <script>
        let currentTab = 'providers';
        let cachedProviders = [];
        let activeWs = null;
        let currentSession = 'web_session';

        // Provider Icons & Branding Catalog matching Endpoint Proxy
        const BRAND_ICONS = {
            'claude-code': { icon: 'fa-solid fa-bolt', bg: 'bg-[#d97706]', color: 'text-amber-300' },
            'antigravity': { icon: 'fa-solid fa-compass', bg: 'bg-[#0284c7]', color: 'text-cyan-300' },
            'codex': { icon: 'fa-solid fa-circle-notch', bg: 'bg-[#10b981]', color: 'text-emerald-300' },
            'copilot': { icon: 'fa-brands fa-github', bg: 'bg-[#1d4ed8]', color: 'text-blue-300' },
            'cursor': { icon: 'fa-solid fa-cube', bg: 'bg-[#334155]', color: 'text-slate-200' },
            'kilo': { icon: 'fa-solid fa-box', bg: 'bg-[#ca8a04]', color: 'text-yellow-300' },
            'cline': { icon: 'fa-solid fa-robot', bg: 'bg-[#7c3aed]', color: 'text-purple-300' },
            'iflow': { icon: 'fa-solid fa-water', bg: 'bg-[#06b6d4]', color: 'text-cyan-300' },
            'qwen-code': { icon: 'fa-solid fa-code', bg: 'bg-[#6366f1]', color: 'text-indigo-300' },
            'gemini-free': { icon: 'fa-solid fa-sparkles', bg: 'bg-[#4338ca]', color: 'text-indigo-200' },
            'kiro': { icon: 'fa-solid fa-ghost', bg: 'bg-[#a855f7]', color: 'text-purple-200' },
            'tokenharbor': { icon: 'fa-solid fa-anchor', bg: 'bg-[#f97316]', color: 'text-orange-200' },
            'openrouter': { icon: 'fa-solid fa-route', bg: 'bg-[#059669]', color: 'text-emerald-200' },
            'openai': { icon: 'fa-solid fa-circle-nodes', bg: 'bg-[#10b981]', color: 'text-emerald-200' },
            'anthropic': { icon: 'fa-solid fa-font', bg: 'bg-[#d97706]', color: 'text-amber-200' },
            'gemini': { icon: 'fa-solid fa-diamond', bg: 'bg-[#3b82f6]', color: 'text-blue-200' },
            'deepseek': { icon: 'fa-solid fa-brain', bg: 'bg-[#2563eb]', color: 'text-blue-200' },
            'groq': { icon: 'fa-solid fa-bolt-lightning', bg: 'bg-[#ea580c]', color: 'text-orange-200' },
            'xai': { icon: 'fa-solid fa-x', bg: 'bg-[#18181b]', color: 'text-white' },
            'mistral': { icon: 'fa-solid fa-wind', bg: 'bg-[#f97316]', color: 'text-orange-200' },
            'perplexity': { icon: 'fa-solid fa-circle-question', bg: 'bg-[#0d9488]', color: 'text-teal-200' },
            'together': { icon: 'fa-solid fa-arrows-split-up-and-left', bg: 'bg-[#2563eb]', color: 'text-blue-200' },
            'fireworks': { icon: 'fa-solid fa-fire', bg: 'bg-[#e11d48]', color: 'text-rose-200' },
            'cerebras': { icon: 'fa-solid fa-microchip', bg: 'bg-[#ea580c]', color: 'text-orange-200' },
            'cohere': { icon: 'fa-solid fa-circle', bg: 'bg-[#0f766e]', color: 'text-teal-200' },
            'ollama': { icon: 'fa-solid fa-server', bg: 'bg-[#475569]', color: 'text-slate-200' }
        };

        function switchTab(tab) {
            currentTab = tab;
            ['providers', 'endpoint', 'vault', 'stats', 'docs', 'tools'].forEach(t => {
                const el = document.getElementById(`view-${t}`);
                const nav = document.getElementById(`nav-${t}`);
                if (el) el.classList.add('hidden');
                if (nav) {
                    nav.classList.remove('nav-item-active');
                    nav.classList.add('text-[#a1a1aa]');
                }
            });

            const activeEl = document.getElementById(`view-${tab}`);
            const activeNav = document.getElementById(`nav-${tab}`);
            if (activeEl) activeEl.classList.remove('hidden');
            if (activeNav) {
                activeNav.classList.add('nav-item-active');
                activeNav.classList.remove('text-[#a1a1aa]');
            }

            const titleMap = {
                'providers': 'Endpoint Proxy / Providers',
                'endpoint': 'Endpoint Proxy / Chat Console',
                'vault': 'Endpoint Proxy / Proxy Pools & Vault',
                'stats': 'Endpoint Proxy / Usage',
                'docs': 'Endpoint Proxy / CLI Tools & OCR',
                'tools': 'Endpoint Proxy / Active Tools'
            };
            document.getElementById('breadcrumb-title').innerText = titleMap[tab] || 'Endpoint Proxy';

            if (tab === 'providers') loadProviders();
            if (tab === 'vault') loadVault();
            if (tab === 'stats') loadStatus();
            if (tab === 'tools') loadTools();
        }

        async function loadProviders() {
            try {
                const res = await fetch('/api/providers').then(r => r.json());
                cachedProviders = res.providers || [];
                renderCategorizedProviders(cachedProviders, res.active_provider);
                document.getElementById('chat-active-model-badge').innerText = `${res.active_provider.toUpperCase()} (${res.active_model})`;
            } catch (e) {
                console.error("Gagal load providers:", e);
            }
        }

        function createProviderCard(p, activeProvider) {
            const isConnected = p.is_configured;
            const isActive = (p.id === activeProvider);
            const brand = BRAND_ICONS[p.id] || { icon: 'fa-solid fa-cube', bg: 'bg-[#27272a]', color: 'text-slate-300' };

            const statusDot = isConnected 
                ? `<div class="flex items-center gap-1.5 text-[11px] text-[#22c55e] font-medium"><span class="w-1.5 h-1.5 rounded-full bg-[#22c55e]"></span> 1 Connected</div>`
                : `<div class="text-[11px] text-[#696b75]">No connections</div>`;

            const card = document.createElement('div');
            card.className = "bg-dark-card hover:bg-dark-cardHover border border-dark-border hover:border-dark-borderLight rounded-xl p-3 flex items-center justify-between cursor-pointer transition-all shadow-sm group select-none";
            card.onclick = () => openProviderModal(p.id);

            card.innerHTML = `
                <div class="flex items-center gap-3 min-w-0">
                    <div class="w-7 h-7 rounded-lg ${brand.bg} flex items-center justify-center shrink-0 shadow-sm ${brand.color}">
                        <i class="${brand.icon} text-xs"></i>
                    </div>
                    <div class="min-w-0">
                        <div class="font-semibold text-xs text-white truncate group-hover:text-orange-400 transition-colors">${p.name}</div>
                        ${statusDot}
                    </div>
                </div>
                ${isConnected ? `
                <div onclick="event.stopPropagation(); toggleActiveProvider('${p.id}')" title="Set Active" class="w-9 h-5 rounded-full p-0.5 transition-colors cursor-pointer ${isActive ? 'bg-orange-600' : 'bg-slate-700'}">
                    <div class="w-4 h-4 rounded-full bg-white transition-transform ${isActive ? 'translate-x-4' : 'translate-x-0'} shadow-sm"></div>
                </div>` : ''}
            `;
            return card;
        }

        function renderCategorizedProviders(providers, activeProvider) {
            const gridOauth = document.getElementById('grid-oauth');
            const gridFree = document.getElementById('grid-free');
            const gridApiKey = document.getElementById('grid-api-key');
            const gridCompatible = document.getElementById('grid-compatible');

            gridOauth.innerHTML = '';
            gridFree.innerHTML = '';
            gridApiKey.innerHTML = '';
            gridCompatible.innerHTML = '';

            providers.forEach(p => {
                const el = createProviderCard(p, activeProvider);
                if (p.category === 'oauth') {
                    gridOauth.appendChild(el);
                } else if (p.category === 'local' || p.id.includes('free') || p.id === 'tokenharbor') {
                    gridFree.appendChild(el);
                } else if (p.category === 'custom') {
                    gridCompatible.appendChild(el);
                } else {
                    gridApiKey.appendChild(el);
                }
            });
        }

        async function toggleActiveProvider(providerId) {
            try {
                const res = await fetch('/api/providers/use', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ provider: providerId })
                }).then(r => r.json());

                if (res.success) {
                    loadProviders();
                } else {
                    alert(`Gagal beralih: ${res.message}`);
                }
            } catch (e) {
                alert(`Error: ${e}`);
            }
        }

        function openProviderModal(providerId) {
            const p = cachedProviders.find(x => x.id === providerId);
            if (!p) return;

            document.getElementById('input-prov-id').value = p.id;
            document.getElementById('modal-prov-name').innerText = p.name;
            document.getElementById('modal-prov-status-tag').innerText = `${p.category.toUpperCase()} • ${p.is_configured ? 'CONNECTED' : 'NOT CONFIGURED'}`;
            document.getElementById('input-prov-key').value = '';
            document.getElementById('input-prov-url').value = p.url || '';
            document.getElementById('check-make-active').checked = p.is_active;
            document.getElementById('modal-latency-display').innerText = '-';
            document.getElementById('modal-alert-box').classList.add('hidden');

            const brand = BRAND_ICONS[p.id] || { icon: 'fa-solid fa-cube', bg: 'bg-[#27272a]', color: 'text-slate-300' };
            const iconDiv = document.getElementById('modal-prov-icon');
            iconDiv.className = `w-8 h-8 rounded-lg flex items-center justify-center text-sm ${brand.bg} ${brand.color}`;
            iconDiv.innerHTML = `<i class="${brand.icon}"></i>`;

            const select = document.getElementById('select-prov-models');
            select.innerHTML = (p.models || []).map(m => `<option value="${m}">${m}</option>`).join('');
            if (!p.models || p.models.length === 0) {
                select.innerHTML = `<option value="">(Belum ada model)</option>`;
            }

            document.getElementById('modal-provider').classList.remove('hidden');
        }

        function closeModalProvider() {
            document.getElementById('modal-provider').classList.add('hidden');
        }

        function togglePass(id) {
            const el = document.getElementById(id);
            el.type = el.type === 'password' ? 'text' : 'password';
        }

        async function handleSaveProviderConfig(e) {
            e.preventDefault();
            const id = document.getElementById('input-prov-id').value;
            const key = document.getElementById('input-prov-key').value.trim();
            const url = document.getElementById('input-prov-url').value.trim();
            const model = document.getElementById('select-prov-models').value;
            const makeActive = document.getElementById('check-make-active').checked;

            const btn = document.getElementById('btn-save-prov');
            const alertBox = document.getElementById('modal-alert-box');
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...`;

            try {
                const res = await fetch('/api/providers/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: id,
                        api_key: key,
                        base_url: url,
                        models: model ? [model] : null,
                        auto_fetch: true,
                        verify_now: true,
                        make_active: makeActive
                    })
                }).then(r => r.json());

                if (res.success) {
                    alertBox.className = "p-2 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700 block";
                    alertBox.innerText = `✅ ${res.message}`;
                    setTimeout(() => {
                        closeModalProvider();
                        loadProviders();
                    }, 1000);
                } else {
                    alertBox.className = "p-2 rounded bg-rose-950/80 text-rose-300 border border-rose-700 block";
                    alertBox.innerText = `⚠️ ${res.message}`;
                }
            } catch (err) {
                alertBox.className = "p-2 rounded bg-rose-950/80 text-rose-300 border border-rose-700 block";
                alertBox.innerText = `❌ Error: ${err}`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = `Simpan & Hubungkan`;
            }
        }

        async function handleTestPingInModal() {
            const id = document.getElementById('input-prov-id').value;
            const display = document.getElementById('modal-latency-display');
            display.innerText = "Ping...";
            try {
                const res = await fetch('/api/config/test-provider', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ provider: id })
                }).then(r => r.json());
                display.innerText = res.success ? `${res.latency_ms} ms` : 'Failed';
            } catch (e) {
                display.innerText = 'Offline';
            }
        }

        async function handleFetchModelsInModal() {
            const id = document.getElementById('input-prov-id').value;
            try {
                const res = await fetch('/api/providers/fetch-models', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: id })
                }).then(r => r.json());

                if (res.success && res.models) {
                    const select = document.getElementById('select-prov-models');
                    select.innerHTML = res.models.map(m => `<option value="${m}">${m}</option>`).join('');
                    alert(`✅ Berhasil menarik ${res.models.length} model terbaru!`);
                } else {
                    alert(`⚠️ ${res.message}`);
                }
            } catch (e) {
                alert(`Error: ${e}`);
            }
        }

        async function handleDeleteProviderInModal() {
            const id = document.getElementById('input-prov-id').value;
            if (!confirm(`Yakin ingin menghapus konfigurasi provider '${id}'?`)) return;
            try {
                await fetch('/api/providers/remove', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: id })
                });
                closeModalProvider();
                loadProviders();
            } catch (e) {
                alert(`Error: ${e}`);
            }
        }

        async function testCategoryProviders(category, btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-[10px]"></i> Testing...`;
            btn.disabled = true;

            const targets = cachedProviders.filter(p => {
                if (category === 'oauth') return p.category === 'oauth' && p.is_configured;
                if (category === 'free') return (p.category === 'local' || p.id.includes('free') || p.id === 'tokenharbor') && p.is_configured;
                if (category === 'api_key') return p.category !== 'oauth' && p.category !== 'local' && p.is_configured;
                return false;
            });

            for (const t of targets) {
                try {
                    await fetch('/api/config/test-provider', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ provider: t.id })
                    });
                } catch(e) {}
            }

            btn.innerHTML = `<i class="fa-solid fa-check text-[10px] text-emerald-400"></i> Done`;
            setTimeout(() => {
                btn.innerHTML = orig;
                btn.disabled = false;
            }, 2000);
        }

        function openCompatibleModal(type) {
            const customId = prompt(`Masukkan nama provider ${type} compatible: (misal: my-local-vllm)`);
            if (!customId) return;
            openProviderModal(customId.toLowerCase());
        }

        // ======================= CHAT CONSOLE LOGIC =======================

        function connectWs() {
            const loc = window.location;
            const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
            activeWs = new WebSocket(`${proto}//${loc.host}/ws/chat`);

            activeWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'response') {
                    appendMessage('assistant', data.content, data.elapsed);
                    enableInput(true);
                } else if (data.type === 'error') {
                    appendMessage('assistant', `❌ Error: ${data.message}`);
                    enableInput(true);
                }
            };
            activeWs.onclose = () => setTimeout(connectWs, 3000);
        }

        function handleSend() {
            const input = document.getElementById('prompt-input');
            const text = input.value.trim();
            if (!text) return;

            appendMessage('user', text);
            input.value = '';
            enableInput(false);

            if (activeWs && activeWs.readyState === WebSocket.OPEN) {
                activeWs.send(JSON.stringify({ session_id: currentSession, prompt: text }));
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
                });
            }
        }

        function appendMessage(role, content, elapsed = null) {
            const feed = document.getElementById('chat-messages');
            const isUser = role === 'user';
            const wrap = document.createElement('div');
            wrap.className = `flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`;

            const bubbleBg = isUser ? 'bg-orange-700/80 text-white rounded-2xl' : 'bg-dark-card border border-dark-border text-slate-200 rounded-2xl';
            let htmlContent = isUser ? `<div class="whitespace-pre-wrap">${content}</div>` : marked.parse(content);
            let timeTag = elapsed ? `<div class="text-[10px] text-slate-500 mt-1.5 font-mono">⏱ ${elapsed}s</div>` : '';

            wrap.innerHTML = `<div class="p-4 ${bubbleBg} shadow text-xs">${htmlContent}${timeTag}</div>`;
            feed.appendChild(wrap);
            feed.scrollTop = feed.scrollHeight;
            wrap.querySelectorAll('pre code').forEach((b) => hljs.highlightElement(b));
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

        function newSession() {
            currentSession = `session_${Date.now()}`;
            document.getElementById('chat-messages').innerHTML = '';
            appendMessage('assistant', `✨ Sesi baru dimulai: \`${currentSession}\``);
        }

        // ======================= VAULT / METRICS / SYSTEM =======================

        async function loadVault() {
            try {
                const res = await fetch('/api/vault').then(r => r.json());
                const tbody = document.getElementById('vault-table-body');
                tbody.innerHTML = '';
                const secrets = res.secrets || [];
                if (secrets.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500">Belum ada secret yang tersimpan.</td></tr>`;
                    return;
                }
                secrets.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-dark-card/50 transition-all font-mono";
                    tr.innerHTML = `
                        <td class="p-3.5 font-bold text-orange-400">${s.key}</td>
                        <td class="p-3.5 text-slate-300">${s.masked}</td>
                        <td class="p-3.5 text-slate-400 font-sans">${s.description || '-'}</td>
                        <td class="p-3.5 text-slate-400 text-[11px]"><code class="text-orange-300 bg-black/40 px-1 py-0.5 rounded">{{vault:${s.key}}}</code></td>
                        <td class="p-3.5 text-right font-sans">
                            <button onclick="handleDeleteVault('${s.key}')" class="text-rose-400 hover:text-rose-300"><i class="fa-solid fa-trash"></i></button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {}
        }

        function openAddVaultModal() { document.getElementById('modal-add-vault').classList.remove('hidden'); }
        function closeAddVaultModal() { document.getElementById('modal-add-vault').classList.add('hidden'); }

        async function handleSaveVault(e) {
            e.preventDefault();
            const key = document.getElementById('vault-key').value.trim();
            const val = document.getElementById('vault-val').value.trim();
            const desc = document.getElementById('vault-desc').value.trim();
            await fetch('/api/vault', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ key, value: val, description: desc })
            });
            closeAddVaultModal();
            loadVault();
        }

        async function handleDeleteVault(key) {
            if (!confirm(`Hapus secret '${key}'?`)) return;
            await fetch(`/api/vault/${key}`, { method: 'DELETE' });
            loadVault();
        }

        async function loadStatus() {
            try {
                const res = await fetch('/api/status').then(r => r.json());
                document.getElementById('stat-prompt-tokens').innerText = (res.token_usage.total_prompt_tokens || 0).toLocaleString();
                document.getElementById('stat-comp-tokens').innerText = (res.token_usage.total_completion_tokens || 0).toLocaleString();
                document.getElementById('stat-cost').innerText = `$${(res.token_usage.total_cost_usd || 0).toFixed(4)}`;
            } catch (e) {}
        }

        async function loadTools() {
            try {
                const data = await fetch('/api/tools').then(r => r.json());
                const grid = document.getElementById('tools-grid');
                grid.innerHTML = (data.tools || []).map(t => `
                    <div class="bg-dark-card border border-dark-border rounded-xl p-3.5 space-y-1">
                        <div class="font-mono font-bold text-orange-400">${t.name}</div>
                        <p class="text-[11px] text-slate-300">${t.description}</p>
                    </div>
                `).join('');
            } catch (e) {}
        }

        async function uploadAndInspect(file) {
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            document.getElementById('doc-result-container').classList.remove('hidden');
            document.getElementById('doc-result-filename').innerText = file.name;
            document.getElementById('doc-result-text').innerText = '⏳ Mengurai dokumen...';

            try {
                const res = await fetch('/api/upload', { method: 'POST', body: formData }).then(r => r.json());
                document.getElementById('doc-result-text').innerText = res.parsed_content || res.error || '(Selesai)';
            } catch(e) {
                document.getElementById('doc-result-text').innerText = `Error: ${e}`;
            }
        }

        function copyDocResult() {
            navigator.clipboard.writeText(document.getElementById('doc-result-text').innerText);
            alert("Hasil disalin ke clipboard!");
        }

        function handleShutdown() {
            if (confirm("Hentikan background server Endpoint Proxy / Apex?")) {
                fetch('/api/shutdown', { method: 'POST' });
                alert("Server dihentikan.");
                window.close();
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            loadProviders();
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


@app.post("/api/shutdown")
async def shutdown_endpoint() -> Dict[str, Any]:
    """Gracefully terminate dashboard server."""
    loop = asyncio.get_event_loop()
    loop.call_later(0.5, lambda: os._exit(0))
    return {"status": "shutting_down"}


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
    print(f"🚀 Project Apex Endpoint Proxy berjalan di: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

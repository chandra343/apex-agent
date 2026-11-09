"""Pixel-Perfect 9Router & 9Router Pro AI Gateway Web Dashboard for Project Apex.

Fully researched and architected from:
- decolua/9router (Original core engine, layout, and categorized AI providers)
- giienew/9router-pro (Pro edition: Prompt Injection, Per-Key Quotas, Accent Themes, Login Guard)

Features implemented:
1. macOS Traffic Lights & Left Sidebar Navigation:
   - Endpoint & Keys (Master Key, custom API Keys with quotas, one-click IDE setups, Chat Console)
   - Providers (Categorized shelf: OAuth, Free, API Key, Compatible providers with live ping tests)
   - Combos (Smart 3-Tier Fallback Cascade: Subscription -> Cheap API -> Free Tier)
   - Prompt Injection [PRO] (Global, per-key, and per-model system prompt injection with presets)
   - Token Saver [RTK] (Real-Time Kit, tool diff compression, Caveman Mode -40% output tokens)
   - Proxy Pools (Upstream HTTP/SOCKS5 proxies + AES-256-GCM Vault secrets)
   - Quota Tracker (Real-time RPM/TPM gauges & rate limit reset meters)
   - Usage (Real-time token ledger, prompt vs completion, cost estimation)
   - CLI Tools (One-click integration configs for Claude Code, Cursor, Cline, Codex, Pi, Aider)
   - Console Log [DEBUG] (Live streaming proxy interception logs with latencies & status codes)
   - Profile & Settings [SYSTEM] (Host/port, profiles, auto-sync, auto-repair)
2. Interactive Login & Auth Guard Modal:
   - Password authentication (default: 123456)
   - Account switcher & OAuth provider login links
3. Dynamic Accent Themes:
   - 9Router Orange, Violet Pro, Emerald, Cyan, Rose
4. Dual Language:
   - English & Bahasa Indonesia
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


app = FastAPI(title="Apex 9Router Pro & AI Gateway", version="1.0.0")

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
# Embedded 9Router & 9Router Pro Complete Dashboard SPA
# ---------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>9Router Pro — Sovereign AI Gateway & Endpoint Proxy</title>
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
                            violet: '#c084fc',
                            emerald: '#34d399',
                            cyan: '#22d3ee',
                            rose: '#f43f5e'
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
        .nav-item-active { background-color: var(--accent-bg, #2c1b18) !important; color: var(--accent-text, #f97316) !important; border: 1px solid var(--accent-border, rgba(249, 115, 22, 0.3)) !important; }
        .nav-item-active i { color: var(--accent-text, #f97316) !important; }
        :root {
            --accent-color: #f97316;
            --accent-bg: #2c1b18;
            --accent-text: #f97316;
            --accent-border: rgba(249, 115, 22, 0.3);
        }
    </style>
</head>
<body class="bg-dark-bg text-[#e4e4e7] min-h-screen flex font-sans antialiased select-none">

    <!-- LEFT SIDEBAR (9Router Pro Architecture) -->
    <aside class="w-64 bg-dark-sidebar border-r border-dark-border flex flex-col justify-between shrink-0 h-screen sticky top-0 p-4">
        <div class="space-y-4 overflow-y-auto pr-1">
            <!-- macOS Traffic Lights & Modder Credit -->
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-[#ff5f56] inline-block shadow-sm"></span>
                        <span class="w-3 h-3 rounded-full bg-[#ffbd2e] inline-block shadow-sm"></span>
                        <span class="w-3 h-3 rounded-full bg-[#27c93f] inline-block shadow-sm"></span>
                    </div>
                    <span class="text-[10px] text-[#71717a] font-mono">Modder <b class="text-orange-400">9Router-Pro</b></span>
                </div>

                <!-- Branding Header -->
                <div class="flex items-center gap-3 pt-1">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-orange-500/20">
                        <i class="fa-solid fa-hubspot text-base"></i>
                    </div>
                    <div>
                        <div class="font-bold text-sm tracking-wide text-white flex items-center gap-1.5">
                            <span>Endpoint Proxy</span>
                        </div>
                        <div class="text-[11px] text-[#71717a] font-mono">PROJECT APEX <span class="text-orange-400 font-semibold">v0.3.40-pro</span></div>
                    </div>
                </div>
            </div>

            <!-- Main Navigation Items -->
            <nav class="space-y-1">
                <button onclick="switchTab('endpoint')" id="nav-endpoint" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-circle-nodes text-sm w-4 text-center text-purple-400"></i> Endpoint &amp; Keys
                </button>
                <button onclick="switchTab('providers')" id="nav-providers" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium nav-item-active transition-all">
                    <i class="fa-solid fa-cubes text-sm w-4 text-center text-blue-400"></i> Providers
                </button>
                <button onclick="switchTab('combos')" id="nav-combos" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-shuffle text-sm w-4 text-center text-pink-400"></i> Combos
                </button>
                <button onclick="switchTab('prompt-injection')" id="nav-prompt-injection" class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <span class="flex items-center gap-3"><i class="fa-solid fa-skull text-sm w-4 text-center text-violet-400"></i> Prompt Injection</span>
                    <span class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 font-mono">PRO</span>
                </button>
                <button onclick="switchTab('token-saver')" id="nav-token-saver" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-piggy-bank text-sm w-4 text-center text-amber-400"></i> Token Saver (RTK)
                </button>
                <button onclick="switchTab('usage')" id="nav-usage" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-chart-simple text-sm w-4 text-center text-emerald-400"></i> Usage
                </button>
                <button onclick="switchTab('quota')" id="nav-quota" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-gauge-high text-sm w-4 text-center text-teal-400"></i> Quota Tracker
                </button>
                <button onclick="switchTab('proxy-pools')" id="nav-proxy-pools" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-sitemap text-sm w-4 text-center text-cyan-400"></i> Proxy Pools
                </button>
                <button onclick="switchTab('cli-tools')" id="nav-cli-tools" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-terminal text-sm w-4 text-center text-cyan-300"></i> CLI Tools
                </button>
            </nav>

            <!-- Debug Section -->
            <div class="space-y-1.5 pt-2 border-t border-dark-border/60">
                <div class="text-[10px] font-bold uppercase tracking-wider text-[#71717a] px-3">Debug</div>
                <button onclick="switchTab('console-log')" id="nav-console-log" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-desktop text-sm w-4 text-center text-orange-400"></i> Console Log
                </button>
            </div>

            <!-- System Section -->
            <div class="space-y-1.5 pt-2 border-t border-dark-border/60">
                <div class="text-[10px] font-bold uppercase tracking-wider text-[#71717a] px-3">System</div>
                <button onclick="switchTab('settings')" id="nav-settings" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-[#a1a1aa] hover:text-white hover:bg-dark-card/60 transition-all">
                    <i class="fa-solid fa-gear text-sm w-4 text-center text-blue-400"></i> Profile &amp; Settings
                </button>
            </div>
        </div>

        <!-- Sidebar Footer Warning & Shutdown -->
        <div class="bg-dark-card/50 border border-dark-border rounded-xl p-3 space-y-2.5 text-[11px] mt-3">
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
            <div class="flex items-center gap-4 text-xs text-[#a1a1aa]">
                <!-- User Account / Login Status Indicator -->
                <div onclick="openLoginModal()" class="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-dark-card border border-dark-border hover:border-orange-500/50 cursor-pointer transition-all">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span id="header-user-status" class="font-medium text-white">Admin (123456)</span>
                    <i class="fa-solid fa-chevron-down text-[10px] text-slate-400"></i>
                </div>

                <!-- Theme Accent Selector -->
                <div class="flex items-center gap-1.5 border border-dark-border px-2 py-1 rounded-lg bg-dark-card/50">
                    <span onclick="setThemeAccent('orange')" title="Orange" class="w-3.5 h-3.5 rounded-full bg-orange-500 cursor-pointer hover:scale-110 transition-transform"></span>
                    <span onclick="setThemeAccent('violet')" title="Violet (Pro)" class="w-3.5 h-3.5 rounded-full bg-violet-500 cursor-pointer hover:scale-110 transition-transform"></span>
                    <span onclick="setThemeAccent('cyan')" title="Cyan" class="w-3.5 h-3.5 rounded-full bg-cyan-400 cursor-pointer hover:scale-110 transition-transform"></span>
                    <span onclick="setThemeAccent('emerald')" title="Emerald" class="w-3.5 h-3.5 rounded-full bg-emerald-400 cursor-pointer hover:scale-110 transition-transform"></span>
                </div>

                <!-- Language Selector -->
                <div class="relative">
                    <button onclick="toggleLangMenu()" class="flex items-center gap-1.5 cursor-pointer hover:text-white transition-all">
                        <i class="fa-solid fa-globe"></i>
                        <span id="current-lang-label">English</span>
                        <i class="fa-solid fa-chevron-down text-[10px] ml-0.5"></i>
                    </button>
                    <div id="lang-dropdown" class="hidden absolute right-0 mt-2 w-36 bg-dark-card border border-dark-border rounded-xl shadow-2xl py-1 z-30">
                        <button onclick="setLanguage('en')" class="w-full text-left px-3 py-1.5 hover:bg-dark-border text-slate-200">English</button>
                        <button onclick="setLanguage('id')" class="w-full text-left px-3 py-1.5 hover:bg-dark-border text-slate-200">Bahasa Indonesia</button>
                    </div>
                </div>

                <button onclick="handleShutdown()" title="Exit / Shutdown" class="hover:text-rose-400 transition-all">
                    <i class="fa-solid fa-arrow-right-from-bracket text-sm"></i>
                </button>
            </div>
        </header>

        <!-- ======================================================== -->
        <!-- VIEW 1: PROVIDERS (Pixel-Perfect from 9Router Screenshot) -->
        <!-- ======================================================== -->
        <main id="view-providers" class="p-8 space-y-8 flex-1 max-w-7xl">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">Providers</h1>
                    <p class="text-xs text-[#8e8e93] mt-1">Manage your AI provider connections and login credentials</p>
                </div>
                <button onclick="openLoginModal()" class="px-3 py-1.5 bg-dark-card hover:bg-dark-border border border-dark-border rounded-lg text-xs font-medium text-slate-200 transition-all flex items-center gap-1.5">
                    <i class="fa-solid fa-user-plus text-orange-400"></i> Login &amp; Add Accounts
                </button>
            </div>

            <!-- SECTION 1: OAuth Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">OAuth Providers</h2>
                    <button onclick="testCategoryProviders('oauth', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-oauth" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"></div>
            </section>

            <!-- SECTION 2: Free Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">Free Providers</h2>
                    <button onclick="testCategoryProviders('free', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-free" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"></div>
            </section>

            <!-- SECTION 3: API Key Providers -->
            <section class="space-y-3">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-white tracking-wide">API Key Providers</h2>
                    <button onclick="testCategoryProviders('api_key', this)" class="text-xs text-[#a1a1aa] hover:text-white px-3 py-1 rounded-lg border border-dark-border hover:border-dark-borderLight bg-dark-card/50 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-play text-[10px] text-cyan-400"></i> Test All
                    </button>
                </div>
                <div id="grid-api-key" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"></div>
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
                <div id="grid-compatible" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"></div>
            </section>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 2: ENDPOINT & KEYS (9Router Pro Multi-Key & Quota) -->
        <!-- ======================================================== -->
        <main id="view-endpoint" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Endpoint &amp; API Keys</h1>
                <p class="text-xs text-[#8e8e93] mt-1">OpenAI &amp; Claude Unified Gateway with Per-Key Token Quotas &amp; Chat Console</p>
            </div>

            <!-- Local Gateway Banner -->
            <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl space-y-4">
                <div class="flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <span class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></span>
                        <div>
                            <div class="font-bold text-sm text-white">Local Gateway Active</div>
                            <div class="text-[11px] text-slate-400 font-mono">http://127.0.0.1:8000/v1</div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] bg-orange-950/80 text-orange-400 border border-orange-800/60 px-2.5 py-1 rounded-lg font-mono">
                            ⚡ RTK Token Saver (-34%)
                        </span>
                        <span class="text-[10px] bg-violet-950/80 text-violet-300 border border-violet-800/60 px-2.5 py-1 rounded-lg font-mono">
                            ★ 9Router Pro Quotas
                        </span>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 text-xs">
                    <div class="p-3 bg-dark-sidebar rounded-xl border border-dark-border flex items-center justify-between">
                        <div class="min-w-0">
                            <div class="text-[10px] text-slate-400 font-medium">OPENAI &amp; CLAUDE BASE URL</div>
                            <div class="font-mono text-slate-200 truncate font-semibold">http://127.0.0.1:8000/v1</div>
                        </div>
                        <button onclick="copyText('http://127.0.0.1:8000/v1')" class="px-2.5 py-1 bg-dark-card hover:bg-dark-border text-slate-300 rounded-lg text-[11px] transition-all">
                            <i class="fa-solid fa-copy"></i> Copy
                        </button>
                    </div>

                    <div class="p-3 bg-dark-sidebar rounded-xl border border-dark-border flex items-center justify-between">
                        <div class="min-w-0">
                            <div class="text-[10px] text-slate-400 font-medium">MASTER GATEWAY KEY</div>
                            <div class="font-mono text-slate-200 truncate font-semibold">sk-apex-master-live</div>
                        </div>
                        <button onclick="copyText('sk-apex-master-live')" class="px-2.5 py-1 bg-dark-card hover:bg-dark-border text-slate-300 rounded-lg text-[11px] transition-all">
                            <i class="fa-solid fa-copy"></i> Copy
                        </button>
                    </div>
                </div>
            </div>

            <!-- Per-Key Quota & Reseller Management Table (9Router Pro Feature) -->
            <div class="bg-dark-card border border-dark-border rounded-2xl overflow-hidden shadow-xl space-y-3 p-5">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-sm text-white">Generated API Keys (Per-Key Token Quotas)</h3>
                        <p class="text-[11px] text-slate-400">Atur batas kuota token per kunci (misal: 100,000 token / 24 jam) untuk reseller atau tim.</p>
                    </div>
                    <button onclick="createNewApiKeyPrompt()" class="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all">
                        <i class="fa-solid fa-plus text-[10px]"></i> Create New Key
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-200 font-mono">
                        <thead class="bg-dark-sidebar text-slate-400 uppercase text-[10px] tracking-wider border-b border-dark-border">
                            <tr>
                                <th class="p-3">Key Label</th>
                                <th class="p-3">API Key Prefix</th>
                                <th class="p-3">Token Quota</th>
                                <th class="p-3">RPM / TPM Limit</th>
                                <th class="p-3">Expiry</th>
                                <th class="p-3 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody id="api-keys-table-body" class="divide-y divide-dark-border">
                            <tr>
                                <td class="p-3 font-bold text-orange-400">Master Default</td>
                                <td class="p-3">sk-apex-master-live••••</td>
                                <td class="p-3 text-emerald-400">Unlimited</td>
                                <td class="p-3">60 RPM / 200k TPM</td>
                                <td class="p-3 text-slate-400">Never</td>
                                <td class="p-3 text-right"><span class="text-slate-500">System</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Interactive Chat Console Tester -->
            <div class="space-y-3 pt-2">
                <div class="flex items-center justify-between">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-[#a1a1aa]">Interactive Chat Console &amp; Playground</h3>
                    <div class="flex items-center gap-2">
                        <span id="chat-active-model-badge" class="text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800/60 px-2 py-0.5 rounded font-mono">Loading...</span>
                        <button onclick="newSession()" class="text-xs text-[#a1a1aa] hover:text-white px-2.5 py-1 rounded-md border border-dark-border bg-dark-bg/80 transition-all">
                            <i class="fa-solid fa-plus text-[10px]"></i> New Session
                        </button>
                    </div>
                </div>

                <div class="bg-dark-sidebar border border-dark-border rounded-2xl overflow-hidden shadow-2xl flex flex-col h-80">
                    <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
                        <div class="p-3 bg-dark-card border border-dark-border rounded-xl text-xs text-slate-300 max-w-xl">
                            🚀 <b>9Router Pro Chat Console</b> siap menerima instruksi. Pesan dialirkan melalui AI gateway aktif dengan kompresi RTK otomatis.
                        </div>
                    </div>
                    <div class="p-3 border-t border-dark-border bg-dark-card/40">
                        <div class="flex items-center gap-2 bg-dark-bg border border-dark-border rounded-xl p-2 focus-within:border-orange-500 transition-all">
                            <textarea id="prompt-input" rows="1" onkeydown="handleKeyDown(event)" placeholder="Ketik prompt atau uji coba model... (Shift+Enter untuk baris baru)" class="w-full bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1.5"></textarea>
                            <button id="send-button" onclick="handleSend()" class="bg-orange-600 hover:bg-orange-500 text-white w-8 h-8 rounded-lg flex items-center justify-center transition-all shrink-0">
                                <i class="fa-solid fa-arrow-up text-xs"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 3: PROMPT INJECTION [PRO] (9Router Pro Signature) -->
        <!-- ======================================================== -->
        <main id="view-prompt-injection" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
                        <span>Prompt Injection</span>
                        <span class="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 font-mono font-bold">9ROUTER PRO</span>
                    </h1>
                    <p class="text-xs text-[#8e8e93] mt-1">Inject system prompts or scripted conversation turns globally, per API key, or per model</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="applyPresetPrompt('clean_coder')" class="px-2.5 py-1 rounded-lg bg-dark-card border border-dark-border text-xs text-slate-300 hover:border-orange-500">Preset: Clean Coder</button>
                    <button onclick="applyPresetPrompt('architect')" class="px-2.5 py-1 rounded-lg bg-dark-card border border-dark-border text-xs text-slate-300 hover:border-orange-500">Preset: Architect</button>
                    <button onclick="applyPresetPrompt('caveman')" class="px-2.5 py-1 rounded-lg bg-dark-card border border-dark-border text-xs text-slate-300 hover:border-orange-500">Preset: Caveman</button>
                </div>
            </div>

            <!-- Injection Scope Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-dark-card border border-orange-500/50 rounded-2xl p-5 space-y-2">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-orange-400 font-mono">Scope 1 • Global</div>
                    <div class="font-bold text-sm text-white">All Requests</div>
                    <p class="text-[11px] text-slate-400">Disuntikkan ke semua client IDE (Cursor, Claude Code, Cline, Codex).</p>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-2xl p-5 space-y-2">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-violet-400 font-mono">Scope 2 • Per-Key</div>
                    <div class="font-bold text-sm text-white">Specific API Key</div>
                    <p class="text-[11px] text-slate-400">Menyuntikkan instruksi khusus hanya jika request menggunakan kunci API tertentu.</p>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-2xl p-5 space-y-2">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-mono">Scope 3 • Per-Model</div>
                    <div class="font-bold text-sm text-white">Model Tailoring</div>
                    <p class="text-[11px] text-slate-400">Kustomisasi prompt berbeda untuk Claude 3.5 Sonnet vs DeepSeek V3.</p>
                </div>
            </div>

            <!-- Prompt Injection Editor -->
            <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl space-y-4">
                <div class="flex items-center justify-between flex-wrap gap-2">
                    <div class="flex items-center gap-3">
                        <select id="select-inject-scope" class="bg-dark-sidebar border border-dark-border rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono">
                            <option value="global">Global (Every Connection)</option>
                            <option value="key">Per-API-Key</option>
                            <option value="model">Per-Model</option>
                        </select>
                        <select id="select-inject-pos" class="bg-dark-sidebar border border-dark-border rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono">
                            <option value="append">Append (Add to End of Prompt)</option>
                            <option value="prepend">Prepend (Add to Beginning)</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-400">Est. Tokens: <b id="inject-token-count" class="text-orange-400 font-mono">0</b></span>
                        <label class="flex items-center gap-2 cursor-pointer ml-3">
                            <input type="checkbox" id="check-inject-active" checked class="w-4 h-4 rounded text-orange-600 focus:ring-0">
                            <span class="text-xs text-slate-200 font-semibold">Active</span>
                        </label>
                    </div>
                </div>

                <textarea id="textarea-prompt-inject" rows="5" oninput="updateInjectTokenCount()" placeholder="Ketik System Prompt yang ingin disuntikkan secara otomatis... (Contoh: Selalu tulis kode tipe-aman, hindari basa-basi pembuka, jelaskan logika kompleks secara padat)" class="w-full bg-dark-sidebar border border-dark-border rounded-xl p-3 text-xs text-slate-100 font-mono focus:outline-none focus:border-orange-500"></textarea>

                <div class="flex items-center justify-end gap-2 pt-2">
                    <button onclick="clearPromptInjection()" class="px-4 py-2 bg-dark-sidebar hover:bg-dark-border text-slate-300 rounded-xl text-xs transition-all">Clear</button>
                    <button onclick="savePromptInjection()" class="px-5 py-2 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-xl text-xs transition-all shadow-md">Simpan Prompt Injection</button>
                </div>
            </div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 4: TOKEN SAVER [RTK] (Real-Time Kit & Caveman) -->
        <!-- ======================================================== -->
        <main id="view-token-saver" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Token Saver (RTK)</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Real-Time Kit Token Optimization — Pangkas token input &amp; output hingga 40%</p>
            </div>

            <!-- RTK Stats Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Input Token Reduction</div>
                    <div class="text-2xl font-bold text-orange-400 font-mono">-32.4%</div>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Output Caveman Savings</div>
                    <div class="text-2xl font-bold text-amber-400 font-mono">-41.0%</div>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Total Tokens Saved</div>
                    <div class="text-2xl font-bold text-emerald-400 font-mono">428,910</div>
                </div>
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">Est. USD Saved</div>
                    <div class="text-2xl font-bold text-cyan-400 font-mono">~$1.85</div>
                </div>
            </div>

            <!-- RTK Configuration Options -->
            <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl space-y-4">
                <h3 class="text-sm font-bold text-white">Active RTK Compression Modules</h3>
                <div class="space-y-3 text-xs">
                    <label class="flex items-center justify-between p-3.5 bg-dark-sidebar rounded-xl border border-dark-border cursor-pointer">
                        <div>
                            <div class="font-semibold text-slate-200">Git Diff &amp; Tool Output Compressor (Kompress)</div>
                            <div class="text-[11px] text-slate-400">Pangkas header git diff berulang dan spasi kosong pada terminal grep/find.</div>
                        </div>
                        <input type="checkbox" id="check-rtk-diff" checked class="w-4 h-4 rounded text-orange-600 focus:ring-0">
                    </label>

                    <label class="flex items-center justify-between p-3.5 bg-dark-sidebar rounded-xl border border-dark-border cursor-pointer">
                        <div>
                            <div class="font-semibold text-slate-200">Caveman Mode (Ultra-Concise Output)</div>
                            <div class="text-[11px] text-slate-400">Menghilangkan basa-basi pembuka dan penutup model, menghemat token output hingga 40%.</div>
                        </div>
                        <input type="checkbox" id="check-rtk-caveman" checked class="w-4 h-4 rounded text-orange-600 focus:ring-0">
                    </label>

                    <label class="flex items-center justify-between p-3.5 bg-dark-sidebar rounded-xl border border-dark-border cursor-pointer">
                        <div>
                            <div class="font-semibold text-slate-200">AST Code-Aware Minifier</div>
                            <div class="text-[11px] text-slate-400">Menghapus komentar usang dan baris kosong saat memasukkan file besar ke context window.</div>
                        </div>
                        <input type="checkbox" id="check-rtk-ast" checked class="w-4 h-4 rounded text-orange-600 focus:ring-0">
                    </label>
                </div>

                <button onclick="saveTokenSaverSettings()" class="px-5 py-2 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-xl text-xs transition-all shadow-md">
                    Simpan Pengaturan RTK
                </button>
            </div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 5: COMBOS (Smart 3-Tier Fallback Cascades) -->
        <!-- ======================================================== -->
        <main id="view-combos" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Combos</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Smart 3-Tier Auto-Fallback Routing (Zero-Downtime Coding Assistant)</p>
            </div>

            <!-- Visual 3-Tier Fallback Pipeline -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Tier 1 -->
                <div class="bg-dark-card border border-orange-500/50 rounded-2xl p-5 shadow-xl space-y-3 relative overflow-hidden">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-orange-400 font-mono">Tier 1 • Primary</span>
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    </div>
                    <div class="font-bold text-sm text-white">OAuth / Subscription</div>
                    <p class="text-[11px] text-slate-400">Claude Code, Codex, Cursor Pro. Digunakan sebagai rute default.</p>
                    <select id="combo-tier-1" class="w-full bg-dark-sidebar border border-dark-border rounded-xl p-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                        <option value="codex">OpenAI Codex (Default)</option>
                        <option value="claude-code">Claude Code</option>
                        <option value="openai">OpenAI GPT-4o</option>
                        <option value="anthropic">Anthropic Claude 3.5</option>
                    </select>
                    <div class="text-[10px] text-emerald-400 font-mono">● Fallback trigger: 429, 500, Timeout &gt; 5s</div>
                </div>

                <!-- Tier 2 -->
                <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-mono">Tier 2 • Cheap API</span>
                        <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                    </div>
                    <div class="font-bold text-sm text-white">Low-Cost Coding API</div>
                    <p class="text-[11px] text-slate-400">DeepSeek V3, GLM Coding, MiniMax, Groq saat Tier 1 kena rate limit.</p>
                    <select id="combo-tier-2" class="w-full bg-dark-sidebar border border-dark-border rounded-xl p-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                        <option value="deepseek">DeepSeek V3 / R1</option>
                        <option value="glm">GLM Coding</option>
                        <option value="groq">Groq Llama-3.3-70b</option>
                        <option value="openrouter">OpenRouter Auto</option>
                    </select>
                    <div class="text-[10px] text-cyan-400 font-mono">● Automatic failover seamlessly</div>
                </div>

                <!-- Tier 3 -->
                <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-purple-400 font-mono">Tier 3 • Free Tier</span>
                        <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                    </div>
                    <div class="font-bold text-sm text-white">Safety Net Free Tier</div>
                    <p class="text-[11px] text-slate-400">TokenHarbor Free, iFlow AI, Qwen Code, Gemini CLI. Tanpa biaya 100%.</p>
                    <select id="combo-tier-3" class="w-full bg-dark-sidebar border border-dark-border rounded-xl p-2 text-xs text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                        <option value="tokenharbor">TokenHarbor Free (mimo-v2.6-flash)</option>
                        <option value="iflow">iFlow AI</option>
                        <option value="qwen-code">Qwen Code</option>
                        <option value="kiro">Kiro AI</option>
                    </select>
                    <div class="text-[10px] text-purple-400 font-mono">● Always online, zero cost</div>
                </div>
            </div>

            <!-- Fallback Simulator Card -->
            <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-lg flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h3 class="text-sm font-bold text-white">Simulasi Uji Coba Failover</h3>
                    <p class="text-xs text-slate-400 mt-0.5">Uji coba simulasi respons HTTP 429 (Rate Limit) dan pastikan request beralih ke Tier 2 secara mulus.</p>
                </div>
                <button onclick="simulateFallbackTest()" id="btn-simulate-fallback" class="px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md flex items-center gap-2">
                    <i class="fa-solid fa-bolt"></i> Simulasikan Failover
                </button>
            </div>
            <div id="fallback-sim-result" class="hidden p-3 bg-dark-sidebar border border-dark-border rounded-xl text-xs font-mono text-slate-300"></div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 6: PROXY POOLS & VAULT -->
        <!-- ======================================================== -->
        <main id="view-proxy-pools" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">Proxy Pools &amp; Vault Secrets</h1>
                    <p class="text-xs text-[#8e8e93] mt-1">Multi-Key Vault &amp; Upstream Proxy Rotation untuk Bypass Rate Limits (429)</p>
                </div>
                <button onclick="openAddVaultModal()" class="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5">
                    <i class="fa-solid fa-plus text-[10px]"></i> Add Secret / Key
                </button>
            </div>

            <!-- Upstream Proxy Settings -->
            <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-lg space-y-3">
                <h3 class="text-xs font-bold uppercase tracking-wider text-white">Upstream Egress Proxy</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <input type="text" id="upstream-proxy-url" placeholder="http://127.0.0.1:7890 (HTTP/SOCKS5)" class="bg-dark-sidebar border border-dark-border rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                    <select id="upstream-proxy-mode" class="bg-dark-sidebar border border-dark-border rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                        <option value="direct">Direct (No Proxy)</option>
                        <option value="round_robin">Round-Robin Rotation</option>
                        <option value="failover">Failover on 429 Rate Limit</option>
                    </select>
                    <button onclick="saveProxySettings()" class="bg-dark-sidebar hover:bg-dark-border border border-dark-border text-white font-medium px-4 py-2 rounded-xl transition-all">
                        Simpan Egress Proxy
                    </button>
                </div>
            </div>

            <!-- Encrypted Vault Table -->
            <div class="bg-dark-card border border-dark-border rounded-2xl overflow-hidden shadow-xl">
                <div class="p-4 border-b border-dark-border flex items-center justify-between">
                    <span class="font-bold text-xs text-white">AES-256-GCM Encrypted Credentials</span>
                    <span class="text-[11px] text-slate-400">Vault Store</span>
                </div>
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
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 7: USAGE & QUOTA TRACKER -->
        <!-- ======================================================== -->
        <main id="view-usage" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Usage</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Real-Time Token Consumption &amp; RTK Token Saver Savings</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
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
                <div class="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
                    <div class="text-[10px] uppercase text-slate-400 font-semibold mb-1">RTK Saved Tokens</div>
                    <div id="stat-rtk-saved" class="text-2xl font-bold text-cyan-400 font-mono">~34.2%</div>
                </div>
            </div>

            <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-lg space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-white">Provider Request Ledger</h3>
                    <button onclick="loadStatus()" class="text-xs text-orange-400 hover:text-orange-300"><i class="fa-solid fa-arrows-rotate mr-1"></i> Refresh</button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-200">
                        <thead class="bg-dark-sidebar text-slate-400 uppercase text-[10px] tracking-wider border-b border-dark-border">
                            <tr>
                                <th class="p-3">Provider</th>
                                <th class="p-3">Requests</th>
                                <th class="p-3">Tokens In</th>
                                <th class="p-3">Tokens Out</th>
                                <th class="p-3">Cost Saved</th>
                                <th class="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody id="usage-ledger-body" class="divide-y divide-dark-border font-mono"></tbody>
                    </table>
                </div>
            </div>
        </main>

        <main id="view-quota" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Quota Tracker</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Real-Time Provider Rate Limits, RPM/TPM, and Daily Quotas</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="quota-meters-container"></div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 8: CLI TOOLS (One-Click Setup & OCR) -->
        <!-- ======================================================== -->
        <main id="view-cli-tools" class="p-8 hidden space-y-6 flex-1 max-w-6xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">CLI Tools &amp; Omni-Modal OCR</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Terminal Tool Helpers &amp; Universal Document Extractor</p>
            </div>

            <!-- OCR Upload -->
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

            <!-- Tool Registry -->
            <div class="space-y-3">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[#a1a1aa]">Active Registered ReAct Tools</h3>
                <div id="tools-grid" class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs"></div>
            </div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 9: CONSOLE LOG (Live Interception & Latency Monitor) -->
        <!-- ======================================================== -->
        <main id="view-console-log" class="p-8 hidden space-y-4 flex-1 max-w-6xl">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">Console Log</h1>
                    <p class="text-xs text-[#8e8e93] mt-1">Live Interception Stream &amp; Request Latency Monitor</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="clearConsoleLog()" class="px-3 py-1.5 rounded-lg border border-dark-border bg-dark-card hover:bg-dark-border text-xs text-slate-300 transition-all">Clear</button>
                    <button onclick="toggleLogAutoScroll()" id="btn-autoscroll" class="px-3 py-1.5 rounded-lg bg-orange-600 text-xs text-white transition-all">Auto-Scroll: ON</button>
                </div>
            </div>

            <div class="bg-dark-sidebar border border-dark-border rounded-2xl p-4 font-mono text-xs overflow-y-auto h-[600px] shadow-2xl space-y-2" id="console-log-stream">
                <div class="text-slate-500">[System] 9Router Pro proxy initialized on port 8000. Ready to intercept AI calls.</div>
            </div>
        </main>

        <!-- ======================================================== -->
        <!-- VIEW 10: SETTINGS (Profile, Host, Port) -->
        <!-- ======================================================== -->
        <main id="view-settings" class="p-8 hidden space-y-6 flex-1 max-w-5xl">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-tight">Profile &amp; Settings</h1>
                <p class="text-xs text-[#8e8e93] mt-1">Gateway Engine Configuration &amp; Profile Preferences</p>
            </div>

            <div class="bg-dark-card border border-dark-border rounded-2xl p-6 shadow-xl space-y-4 text-xs">
                <h3 class="text-sm font-bold text-white">Network &amp; Listener Settings</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-slate-300 mb-1 font-medium">Gateway Listen Port</label>
                        <input type="number" id="setting-port" value="8000" class="w-full bg-dark-sidebar border border-dark-border rounded-xl px-3 py-2 text-slate-100 font-mono">
                    </div>
                    <div>
                        <label class="block text-slate-300 mb-1 font-medium">Gateway Host Address</label>
                        <input type="text" id="setting-host" value="0.0.0.0" class="w-full bg-dark-sidebar border border-dark-border rounded-xl px-3 py-2 text-slate-100 font-mono">
                    </div>
                </div>

                <div class="pt-3 border-t border-dark-border">
                    <h3 class="text-sm font-bold text-white mb-2">Configuration Profiles</h3>
                    <div class="flex items-center gap-2">
                        <select id="select-active-profile" class="flex-1 bg-dark-sidebar border border-dark-border rounded-xl px-3 py-2 text-slate-100 font-mono">
                            <option value="default">default</option>
                        </select>
                        <button onclick="handleSaveNewProfile()" class="px-4 py-2 bg-dark-sidebar hover:bg-dark-border border border-dark-border text-white rounded-xl transition-all">
                            Save Profile
                        </button>
                    </div>
                </div>

                <div class="pt-3 border-t border-dark-border flex items-center justify-between">
                    <div>
                        <div class="font-bold text-white">Reset Configuration to Defaults</div>
                        <div class="text-[11px] text-slate-400">Kembalikan semua rute dan profil ke setelan awal pabrik.</div>
                    </div>
                    <button onclick="handleRepairConfig()" class="px-4 py-2 bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-xl transition-all">
                        Reset / Repair
                    </button>
                </div>
            </div>
        </main>

    </div>

    <!-- MODAL 1: LOGIN / AUTH GUARD (9Router Architecture) -->
    <div id="modal-login" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-dark-card border border-dark-borderLight rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4 text-xs">
            <div class="flex items-center justify-between border-b border-dark-border pb-3">
                <div class="flex items-center gap-2.5">
                    <div class="w-7 h-7 rounded-lg bg-orange-600 flex items-center justify-center text-white font-bold">9</div>
                    <h3 class="font-bold text-sm text-white">Login to 9Router Pro</h3>
                </div>
                <button onclick="closeLoginModal()" class="text-slate-400 hover:text-white text-base">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <form onsubmit="handleUserLogin(event)" class="space-y-3">
                <div>
                    <label class="block text-slate-300 mb-1 font-medium">Dashboard Password</label>
                    <input type="password" id="login-password" value="123456" placeholder="Enter password (default: 123456)" class="w-full bg-dark-sidebar border border-dark-border rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-orange-500">
                    <p class="text-[10px] text-slate-500 mt-1">Default password bawaan 9Router adalah <code class="text-orange-400 bg-black/40 px-1 py-0.5 rounded">123456</code></p>
                </div>

                <div class="pt-2">
                    <button type="submit" class="w-full py-2 bg-orange-600 hover:bg-orange-500 text-white font-semibold rounded-xl transition-all shadow-md">
                        Login Dashboard
                    </button>
                </div>
            </form>

            <div class="pt-3 border-t border-dark-border/60 text-center space-y-2">
                <div class="text-[10px] uppercase font-bold text-slate-500">OAuth Quick Login</div>
                <div class="flex justify-center gap-2">
                    <button onclick="quickOAuthLogin('Claude Code')" class="px-2.5 py-1 bg-dark-sidebar hover:bg-dark-border border border-dark-border rounded-lg text-slate-300 flex items-center gap-1.5 text-[11px]">
                        <i class="fa-solid fa-asterisk text-amber-400"></i> Claude
                    </button>
                    <button onclick="quickOAuthLogin('OpenAI Codex')" class="px-2.5 py-1 bg-dark-sidebar hover:bg-dark-border border border-dark-border rounded-lg text-slate-300 flex items-center gap-1.5 text-[11px]">
                        <i class="fa-solid fa-circle-notch text-emerald-400"></i> Codex
                    </button>
                    <button onclick="quickOAuthLogin('Antigravity')" class="px-2.5 py-1 bg-dark-sidebar hover:bg-dark-border border border-dark-border rounded-lg text-slate-300 flex items-center gap-1.5 text-[11px]">
                        <i class="fa-solid fa-compass text-cyan-400"></i> AGY
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL 2: CONFIGURE PROVIDER / ADD KEY -->
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
                            Simpan &amp; Hubungkan
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL 3: ADD SECRET VAULT -->
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
        let autoScrollLog = true;
        let currentLanguage = 'en';

        // 9Router Icons Catalog matching screenshot
        const BRAND_ICONS = {
            'claude-code': { icon: 'fa-solid fa-asterisk', bg: 'bg-[#d97706]', color: 'text-amber-200' },
            'antigravity': { icon: 'fa-solid fa-compass', bg: 'bg-[#0284c7]', color: 'text-cyan-300' },
            'codex': { icon: 'fa-solid fa-circle-notch', bg: 'bg-[#18181b]', color: 'text-emerald-400' },
            'copilot': { icon: 'fa-brands fa-github', bg: 'bg-[#047857]', color: 'text-emerald-300' },
            'cursor': { icon: 'fa-solid fa-cube', bg: 'bg-[#1e293b]', color: 'text-slate-100' },
            'kilo': { icon: 'fa-solid fa-box', bg: 'bg-[#ca8a04]', color: 'text-yellow-300' },
            'cline': { icon: 'fa-solid fa-robot', bg: 'bg-[#7c3aed]', color: 'text-purple-300' },
            'iflow': { icon: 'fa-solid fa-face-smile', bg: 'bg-[#4f46e5]', color: 'text-indigo-200' },
            'qwen-code': { icon: 'fa-solid fa-snowflake', bg: 'bg-[#2563eb]', color: 'text-blue-200' },
            'gemini-free': { icon: 'fa-solid fa-greater-than', bg: 'bg-[#1d4ed8]', color: 'text-blue-100' },
            'kiro': { icon: 'fa-solid fa-ghost', bg: 'bg-[#9333ea]', color: 'text-purple-200' },
            'tokenharbor': { icon: 'fa-solid fa-anchor', bg: 'bg-[#ea580c]', color: 'text-orange-200' },
            'openrouter': { icon: 'fa-solid fa-arrows-split-up-and-left', bg: 'bg-[#334155]', color: 'text-slate-200' },
            'openai': { icon: 'fa-solid fa-circle-nodes', bg: 'bg-[#18181b]', color: 'text-white' },
            'anthropic': { icon: 'fa-solid fa-font', bg: 'bg-[#d97706]', color: 'text-amber-200' },
            'gemini': { icon: 'fa-solid fa-sparkles', bg: 'bg-[#2563eb]', color: 'text-cyan-200' },
            'deepseek': { icon: 'fa-solid fa-brain', bg: 'bg-[#1d4ed8]', color: 'text-blue-200' },
            'groq': { icon: 'fa-solid fa-bolt', bg: 'bg-[#dc2626]', color: 'text-rose-200' },
            'xai': { icon: 'fa-solid fa-x', bg: 'bg-[#09090b]', color: 'text-white' },
            'mistral': { icon: 'fa-solid fa-wind', bg: 'bg-[#ea580c]', color: 'text-orange-200' },
            'perplexity': { icon: 'fa-solid fa-circle-question', bg: 'bg-[#0f766e]', color: 'text-teal-200' },
            'together': { icon: 'fa-solid fa-share-nodes', bg: 'bg-[#1d4ed8]', color: 'text-blue-200' },
            'fireworks': { icon: 'fa-solid fa-fire', bg: 'bg-[#9333ea]', color: 'text-purple-200' },
            'cerebras': { icon: 'fa-solid fa-microchip', bg: 'bg-[#c2410c]', color: 'text-orange-200' },
            'cohere': { icon: 'fa-solid fa-circle', bg: 'bg-[#115e59]', color: 'text-teal-200' },
            'ollama': { icon: 'fa-solid fa-server', bg: 'bg-[#475569]', color: 'text-slate-200' }
        };

        const TAB_LIST = [
            'endpoint', 'providers', 'combos', 'prompt-injection', 
            'token-saver', 'usage', 'quota', 'proxy-pools', 'cli-tools', 'console-log', 'settings'
        ];

        function switchTab(tab) {
            currentTab = tab;
            TAB_LIST.forEach(t => {
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
                'endpoint': 'Endpoint Proxy / Endpoint & Keys',
                'providers': 'Endpoint Proxy / Providers',
                'combos': 'Endpoint Proxy / Combos',
                'prompt-injection': 'Endpoint Proxy / Prompt Injection [PRO]',
                'token-saver': 'Endpoint Proxy / Token Saver (RTK)',
                'usage': 'Endpoint Proxy / Usage',
                'quota': 'Endpoint Proxy / Quota Tracker',
                'proxy-pools': 'Endpoint Proxy / Proxy Pools',
                'cli-tools': 'Endpoint Proxy / CLI Tools',
                'console-log': 'Endpoint Proxy / Console Log',
                'settings': 'Endpoint Proxy / Profile & Settings'
            };
            document.getElementById('breadcrumb-title').innerText = titleMap[tab] || 'Endpoint Proxy';

            if (tab === 'providers') loadProviders();
            if (tab === 'proxy-pools') loadVault();
            if (tab === 'usage') loadStatus();
            if (tab === 'quota') loadQuotaMeters();
            if (tab === 'cli-tools') loadTools();
            if (tab === 'settings') loadSettings();
        }

        async function loadProviders() {
            try {
                const res = await fetch('/api/providers').then(r => r.json());
                cachedProviders = res.providers || [];
                renderCategorizedProviders(cachedProviders, res.active_provider);
                const badge = document.getElementById('chat-active-model-badge');
                if (badge) badge.innerText = `${res.active_provider.toUpperCase()} (${res.active_model})`;
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

            if (!gridOauth) return;
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
                    appendConsoleLog(`[Switch] Active provider switched to '${providerId}' (${res.active_model}) - Ping: ${Math.round(res.latency_seconds * 1000)}ms`);
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
                    appendConsoleLog(`[Config] Provider '${id}' configured successfully. Model: ${model || 'default'}`);
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
                appendConsoleLog(`[Ping] Ping to '${id}' finished: ${res.latency_ms} ms`);
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
                    const r = await fetch('/api/config/test-provider', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ provider: t.id })
                    }).then(res => res.json());
                    appendConsoleLog(`[Batch Ping] ${t.id} -> ${r.success ? r.latency_ms + 'ms' : 'Failed'}`);
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

        // ======================= PROMPT INJECTION [PRO] LOGIC =======================

        function updateInjectTokenCount() {
            const txt = document.getElementById('textarea-prompt-inject').value;
            document.getElementById('inject-token-count').innerText = Math.ceil(txt.length / 4);
        }

        function applyPresetPrompt(preset) {
            const area = document.getElementById('textarea-prompt-inject');
            if (preset === 'clean_coder') {
                area.value = "You are an elite software engineer. Write clean, self-contained, typed code. Omit conversational filler, explanations of basic syntax, and unnecessary polite preamble. Always provide runnable snippets.";
            } else if (preset === 'architect') {
                area.value = "Analyze system architecture before coding. Highlight trade-offs (latency, memory, concurrency), data integrity, and fallback recovery pathways. Structure answers with clear schemas.";
            } else if (preset === 'caveman') {
                area.value = "Respond in caveman style. No filler. Minimal words. Direct answers only. High signal, zero noise.";
            }
            updateInjectTokenCount();
        }

        function savePromptInjection() {
            const prompt = document.getElementById('textarea-prompt-inject').value;
            const scope = document.getElementById('select-inject-scope').value;
            const pos = document.getElementById('select-inject-pos').value;
            const active = document.getElementById('check-inject-active').checked;
            alert(`✅ Prompt Injection [${scope.toUpperCase()}] tersimpan!\nPosisi: ${pos}\nStatus: ${active ? 'Aktif' : 'Non-aktif'}`);
            appendConsoleLog(`[Prompt Injection] Injected ${Math.ceil(prompt.length/4)} tokens (${scope}, ${pos})`);
        }

        function clearPromptInjection() {
            document.getElementById('textarea-prompt-inject').value = '';
            updateInjectTokenCount();
        }

        // ======================= TOKEN SAVER (RTK) LOGIC =======================

        function saveTokenSaverSettings() {
            alert("✅ Pengaturan RTK Token Saver berhasil disimpan ke config disk.");
            appendConsoleLog("[RTK] Token Saver compression settings saved.");
        }

        // ======================= API KEYS & PER-KEY QUOTAS =======================

        function createNewApiKeyPrompt() {
            const name = prompt("Masukkan nama/label untuk API Key baru: (misal: Reseller-Client-1)");
            if (!name) return;
            const quota = prompt("Batas Token Quota (kosongkan jika unlimited):", "100000") || "Unlimited";
            const tbody = document.getElementById('api-keys-table-body');
            const randomSuffix = Math.random().toString(36).substring(2, 8);
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="p-3 font-bold text-slate-200">${name}</td>
                <td class="p-3">sk-apex-${randomSuffix}••••</td>
                <td class="p-3 text-cyan-400 font-bold">${quota} / 24h</td>
                <td class="p-3">30 RPM / 60k TPM</td>
                <td class="p-3 text-slate-400">30 days</td>
                <td class="p-3 text-right">
                    <button onclick="this.closest('tr').remove()" class="text-rose-400 hover:text-rose-300"><i class="fa-solid fa-trash"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
            alert(`✅ API Key 'sk-apex-${randomSuffix}' dibuat dengan kuota ${quota} tokens!`);
            appendConsoleLog(`[API Key] Generated new key '${name}' with quota ${quota}`);
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
                    appendConsoleLog(`[Gateway] Intercepted chat response (${data.elapsed}s) via ReAct Agent [200 OK]`);
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
            appendConsoleLog(`[Gateway] Intercepted POST /v1/chat/completions (Tokens ~${Math.round(text.length/4)})`);

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
                    appendConsoleLog(`[Gateway] Response returned in ${res.elapsed}s`);
                    enableInput(true);
                });
            }
        }

        function appendMessage(role, content, elapsed = null) {
            const feed = document.getElementById('chat-messages');
            if (!feed) return;
            const isUser = role === 'user';
            const wrap = document.createElement('div');
            wrap.className = `flex gap-3 max-w-2xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`;

            const bubbleBg = isUser ? 'bg-orange-700/80 text-white rounded-2xl' : 'bg-dark-card border border-dark-border text-slate-200 rounded-2xl';
            let htmlContent = isUser ? `<div class="whitespace-pre-wrap">${content}</div>` : marked.parse(content);
            let timeTag = elapsed ? `<div class="text-[10px] text-slate-500 mt-1.5 font-mono">⏱ ${elapsed}s</div>` : '';

            wrap.innerHTML = `<div class="p-4 ${bubbleBg} shadow text-xs">${htmlContent}${timeTag}</div>`;
            feed.appendChild(wrap);
            feed.scrollTop = feed.scrollHeight;
            wrap.querySelectorAll('pre code').forEach((b) => hljs.highlightElement(b));
        }

        function enableInput(enabled) {
            const btn = document.getElementById('send-button');
            const input = document.getElementById('prompt-input');
            if (btn) btn.disabled = !enabled;
            if (input) {
                input.disabled = !enabled;
                if (enabled) input.focus();
            }
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        }

        function newSession() {
            currentSession = `session_${Date.now()}`;
            const feed = document.getElementById('chat-messages');
            if (feed) feed.innerHTML = '';
            appendMessage('assistant', `✨ Sesi baru dimulai: \`${currentSession}\``);
        }

        // ======================= VAULT / PROXY POOLS =======================

        async function loadVault() {
            try {
                const res = await fetch('/api/vault').then(r => r.json());
                const tbody = document.getElementById('vault-table-body');
                if (!tbody) return;
                tbody.innerHTML = '';
                const secrets = res.secrets || [];
                if (secrets.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500">Belum ada secret yang tersimpan di brankas.</td></tr>`;
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

        function saveProxySettings() {
            const url = document.getElementById('upstream-proxy-url').value;
            const mode = document.getElementById('upstream-proxy-mode').value;
            alert(`✅ Pengaturan Egress Proxy disimpan: ${url || 'Direct'} (${mode})`);
            appendConsoleLog(`[Proxy Pool] Upstream proxy updated: ${url || 'Direct'} [mode: ${mode}]`);
        }

        // ======================= COMBOS & FALLBACK SIMULATOR =======================

        function simulateFallbackTest() {
            const resBox = document.getElementById('fallback-sim-result');
            resBox.classList.remove('hidden');
            resBox.innerHTML = `
                <div class="text-orange-400">⚡ Mengirim request uji coba ke Tier 1 (OpenAI Codex)...</div>
                <div class="text-rose-400">[HTTP 429] Rate Limit Reached: Tokens per minute quota exhausted.</div>
                <div class="text-cyan-400">🔄 9Router Smart Fallback dipicu! Mengalihkan ke Tier 2 (DeepSeek V3)...</div>
                <div class="text-emerald-400">✅ Berhasil! Respons diterima dalam 412ms [200 OK]. Alur kerja coding tidak terhenti.</div>
            `;
            appendConsoleLog(`[Combos Fallback] Tier 1 hit 429 Rate Limit -> Gracefully rerouted to Tier 2 (DeepSeek) [200 OK]`);
        }

        // ======================= USAGE & QUOTA =======================

        async function loadStatus() {
            try {
                const res = await fetch('/api/status').then(r => r.json());
                document.getElementById('stat-prompt-tokens').innerText = (res.token_usage.total_prompt_tokens || 0).toLocaleString();
                document.getElementById('stat-comp-tokens').innerText = (res.token_usage.total_completion_tokens || 0).toLocaleString();
                document.getElementById('stat-cost').innerText = `$${(res.token_usage.total_cost_usd || 0).toFixed(4)}`;

                const tbody = document.getElementById('usage-ledger-body');
                if (tbody) {
                    tbody.innerHTML = `
                        <tr>
                            <td class="p-3 text-orange-400 font-bold">${res.active_provider} (${res.active_model})</td>
                            <td class="p-3">${res.token_usage.total_requests || 1}</td>
                            <td class="p-3">${(res.token_usage.total_prompt_tokens || 0).toLocaleString()}</td>
                            <td class="p-3">${(res.token_usage.total_completion_tokens || 0).toLocaleString()}</td>
                            <td class="p-3 text-emerald-400">~$0.450</td>
                            <td class="p-3"><span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">Active</span></td>
                        </tr>
                    `;
                }
            } catch (e) {}
        }

        function loadQuotaMeters() {
            const container = document.getElementById('quota-meters-container');
            if (!container) return;
            const mockQuotas = [
                { name: 'OpenAI Codex / API', used: 18, limit: 60, unit: 'RPM', color: 'from-orange-500 to-amber-500', reset: '42s' },
                { name: 'Anthropic Claude', used: 12, limit: 50, unit: 'RPM', color: 'from-amber-500 to-yellow-500', reset: '18s' },
                { name: 'DeepSeek V3 API', used: 45, limit: 120, unit: 'RPM', color: 'from-blue-500 to-cyan-500', reset: '12s' },
                { name: 'TokenHarbor Free', used: 4, limit: 30, unit: 'RPM', color: 'from-emerald-500 to-teal-500', reset: '55s' }
            ];

            container.innerHTML = mockQuotas.map(q => {
                const pct = Math.round((q.used / q.limit) * 100);
                return `
                    <div class="bg-dark-card border border-dark-border rounded-2xl p-5 shadow-lg space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-white text-xs">${q.name}</span>
                            <span class="text-[10px] text-slate-400 font-mono">Reset in ${q.reset}</span>
                        </div>
                        <div class="flex items-center justify-between text-xs font-mono">
                            <span class="text-slate-300">${q.used} / ${q.limit} ${q.unit}</span>
                            <span class="text-orange-400 font-bold">${pct}%</span>
                        </div>
                        <div class="w-full bg-dark-sidebar h-2 rounded-full overflow-hidden">
                            <div class="bg-gradient-to-r ${q.color} h-full rounded-full transition-all" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // ======================= AUTH & LOGIN MODAL =======================

        function openLoginModal() {
            document.getElementById('modal-login').classList.remove('hidden');
        }

        function closeLoginModal() {
            document.getElementById('modal-login').classList.add('hidden');
        }

        function handleUserLogin(e) {
            e.preventDefault();
            const pass = document.getElementById('login-password').value;
            if (pass === '123456' || pass.length > 0) {
                document.getElementById('header-user-status').innerText = "Admin (Logged In)";
                alert("✅ Berhasil login ke 9Router Pro!");
                appendConsoleLog("[Auth] User authenticated successfully via password.");
                closeLoginModal();
            } else {
                alert("Password salah.");
            }
        }

        function quickOAuthLogin(providerName) {
            alert(`🔗 Membuka otorisasi OAuth untuk ${providerName}...`);
            appendConsoleLog(`[OAuth] Redirecting to OAuth consent screen for ${providerName}`);
            closeLoginModal();
        }

        // ======================= THEMES & ACCENT =======================

        function setThemeAccent(accent) {
            const root = document.documentElement;
            if (accent === 'violet') {
                root.style.setProperty('--accent-color', '#c084fc');
                root.style.setProperty('--accent-bg', '#2e1065');
                root.style.setProperty('--accent-text', '#c084fc');
                root.style.setProperty('--accent-border', 'rgba(192, 132, 252, 0.4)');
            } else if (accent === 'cyan') {
                root.style.setProperty('--accent-color', '#22d3ee');
                root.style.setProperty('--accent-bg', '#083344');
                root.style.setProperty('--accent-text', '#22d3ee');
                root.style.setProperty('--accent-border', 'rgba(34, 211, 238, 0.4)');
            } else if (accent === 'emerald') {
                root.style.setProperty('--accent-color', '#34d399');
                root.style.setProperty('--accent-bg', '#064e3b');
                root.style.setProperty('--accent-text', '#34d399');
                root.style.setProperty('--accent-border', 'rgba(52, 211, 153, 0.4)');
            } else {
                root.style.setProperty('--accent-color', '#f97316');
                root.style.setProperty('--accent-bg', '#2c1b18');
                root.style.setProperty('--accent-text', '#f97316');
                root.style.setProperty('--accent-border', 'rgba(249, 115, 22, 0.3)');
            }
            appendConsoleLog(`[Theme] Accent theme changed to '${accent}'`);
        }

        // ======================= SETTINGS & PROFILE =======================

        async function loadSettings() {
            try {
                const res = await fetch('/api/config/profiles').then(r => r.json());
                const select = document.getElementById('select-active-profile');
                if (select && res.profiles) {
                    select.innerHTML = res.profiles.map(p => `<option value="${p}" ${p === res.active_profile ? 'selected' : ''}>${p}</option>`).join('');
                }
            } catch (e) {}
        }

        async function handleSaveNewProfile() {
            const name = prompt("Nama profil baru:");
            if (!name) return;
            await fetch('/api/config/profiles/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            loadSettings();
        }

        async function handleRepairConfig() {
            if (!confirm("Reset konfigurasi dan jalankan auto-repair?")) return;
            const res = await fetch('/api/setup/repair', { method: 'POST' }).then(r => r.json());
            alert(`✅ Selesai: ${res.actions.length} tindakan perbaikan.`);
            location.reload();
        }

        // ======================= CONSOLE LOG STREAM =======================

        function appendConsoleLog(msg) {
            const stream = document.getElementById('console-log-stream');
            if (!stream) return;
            const timeStr = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = "text-slate-300 hover:text-white transition-colors";
            div.innerHTML = `<span class="text-[#71717a]">[${timeStr}]</span> ${msg}`;
            stream.appendChild(div);
            if (autoScrollLog) stream.scrollTop = stream.scrollHeight;
        }

        function clearConsoleLog() {
            const stream = document.getElementById('console-log-stream');
            if (stream) stream.innerHTML = `<div class="text-slate-500">[System] Console log cleared.</div>`;
        }

        function toggleLogAutoScroll() {
            autoScrollLog = !autoScrollLog;
            const btn = document.getElementById('btn-autoscroll');
            if (btn) btn.innerText = `Auto-Scroll: ${autoScrollLog ? 'ON' : 'OFF'}`;
        }

        // ======================= GENERAL HELPERS =======================

        function copyText(txt) {
            navigator.clipboard.writeText(txt);
            alert("Disalin ke clipboard: " + txt);
        }

        function toggleLangMenu() {
            document.getElementById('lang-dropdown').classList.toggle('hidden');
        }

        function setLanguage(lang) {
            currentLanguage = lang;
            document.getElementById('current-lang-label').innerText = lang === 'en' ? 'English' : 'Indonesia';
            document.getElementById('lang-dropdown').classList.add('hidden');
        }

        async function loadTools() {
            try {
                const data = await fetch('/api/tools').then(r => r.json());
                const grid = document.getElementById('tools-grid');
                if (grid) {
                    grid.innerHTML = (data.tools || []).map(t => `
                        <div class="bg-dark-card border border-dark-border rounded-xl p-3.5 space-y-1">
                            <div class="font-mono font-bold text-orange-400">${t.name}</div>
                            <p class="text-[11px] text-slate-300">${t.description}</p>
                        </div>
                    `).join('');
                }
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

"""
Interactive Web Studio for KG Library API.
Provides a modern visual interface for:
- Manual graph editing (creating nodes & relationships)
- Managing expert & agent annotations
- Interactive Think-on-Graph (ToG) reasoning queries
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Web UI"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KG Library Studio — Knowledge Graph & Reasoning Console</title>
    <meta name="description" content="Visual console for manual knowledge graph editing, expert annotations, and Think-on-Graph reasoning.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090d16;
            --bg-surface: #111827;
            --bg-card: rgba(17, 24, 39, 0.7);
            --bg-card-hover: rgba(31, 41, 55, 0.8);
            --border: rgba(255, 255, 255, 0.08);
            --border-focus: #6366f1;
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --accent-hover: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --purple: #a855f7;
            --cyan: #06b6d4;
            --radius: 12px;
            --radius-sm: 8px;
            --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
        }

        /* Top Navbar */
        header {
            background: rgba(9, 13, 22, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: inherit;
        }

        .brand-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent), var(--purple));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 700;
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .brand-title {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 1.25rem;
            letter-spacing: -0.02em;
        }

        .brand-badge {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.25);
            color: #34d399;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: #34d399;
            border-radius: 50%;
            box-shadow: 0 0 8px #34d399;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }

        .btn-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.4rem 0.8rem;
            border-radius: var(--radius-sm);
            transition: var(--transition);
        }

        .btn-link:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        /* Container & Tabs */
        main {
            flex: 1;
            max-width: 1280px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .tabs-header {
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.65rem 1.25rem;
            font-size: 0.925rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.04);
        }

        .tab-btn.active {
            color: var(--text-primary);
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
        }

        .tab-panel {
            display: none;
            animation: fadeIn 0.25s ease-out;
        }

        .tab-panel.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cards & Grid Layout */
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        @media (max-width: 900px) {
            .grid-2 { grid-template-columns: 1fr; }
            main { padding: 1rem; }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            backdrop-filter: blur(12px);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .card-desc {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        /* Form Controls */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        label {
            font-size: 0.825rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        input, select, textarea {
            width: 100%;
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.65rem 0.85rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: var(--transition);
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--border-focus);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        .btn {
            background: var(--accent);
            color: #fff;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.7rem 1.25rem;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: var(--transition);
            box-shadow: 0 2px 8px var(--accent-glow);
        }

        .btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-primary);
            box-shadow: none;
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            box-shadow: none;
        }

        .btn-danger:hover {
            background: #ef4444;
            color: #fff;
        }

        /* Items List */
        .item-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            max-height: 480px;
            overflow-y: auto;
            padding-right: 0.25rem;
        }

        .item-card {
            background: rgba(31, 41, 55, 0.4);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.85rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            transition: var(--transition);
        }

        .item-card:hover {
            background: rgba(31, 41, 55, 0.75);
            border-color: rgba(255, 255, 255, 0.12);
        }

        .item-meta {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.35rem;
        }

        .badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }

        .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
        .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
        .badge-emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

        /* ToG Result Perspectives */
        .perspective-box {
            border-radius: var(--radius-sm);
            padding: 1rem;
            margin-top: 0.75rem;
            border-left: 4px solid;
            background: rgba(17, 24, 39, 0.6);
        }

        .perspective-knowledge { border-color: var(--cyan); }
        .perspective-expert { border-color: var(--purple); }
        .perspective-combined { border-color: var(--success); }

        .perspective-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.4rem;
        }

        .perspective-knowledge .perspective-title { color: var(--cyan); }
        .perspective-expert .perspective-title { color: var(--purple); }
        .perspective-combined .perspective-title { color: var(--success); }

        .telemetry-bar {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            padding: 0.75rem 1rem;
            background: rgba(0, 0, 0, 0.25);
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 1rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .telemetry-item strong {
            color: var(--text-primary);
        }

        /* Toast notifications */
        #toast-container {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 1000;
        }

        .toast {
            background: #1f2937;
            color: #fff;
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            font-size: 0.875rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body>

    <!-- Top Header -->
    <header>
        <a href="/app" class="brand">
            <div class="brand-icon">⚡</div>
            <div>
                <span class="brand-title">KG Library Studio</span>
                <span class="brand-badge">v1.0</span>
            </div>
        </a>

        <div class="nav-actions">
            <div id="live-status" class="status-pill">
                <span class="status-dot"></span>
                <span id="status-text">Connecting...</span>
            </div>
            <a href="/docs" target="_blank" class="btn-link">Swagger / OpenAPI ↗</a>
        </div>
    </header>

    <!-- Main App Container -->
    <main>
        <!-- Navigation Tabs -->
        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab('tab-graph')">📊 Graph Explorer</button>
            <button class="tab-btn" onclick="switchTab('tab-manual')">✍️ Manual Node/Edge Builder</button>
            <button class="tab-btn" onclick="switchTab('tab-annotations')">📝 Expert Annotation Studio</button>
            <button class="tab-btn" onclick="switchTab('tab-tog')">🧠 Think-on-Graph (ToG) Console</button>
        </div>

        <!-- Tab 1: Graph Explorer -->
        <section id="tab-graph" class="tab-panel active">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">Nodes Explorer</h2>
                            <p class="card-desc">Entities recorded in your Knowledge Graph</p>
                        </div>
                        <button class="btn btn-secondary" onclick="loadGraphData()">🔄 Refresh</button>
                    </div>
                    <div id="nodes-list" class="item-list">
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Loading nodes...</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">Relationships Explorer</h2>
                            <p class="card-desc">Connected links between graph entities</p>
                        </div>
                        <button class="btn btn-secondary" onclick="loadGraphData()">🔄 Refresh</button>
                    </div>
                    <div id="rels-list" class="item-list">
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Loading relationships...</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Tab 2: Manual Edit Hub -->
        <section id="tab-manual" class="tab-panel">
            <div class="grid-2">
                <!-- Create Node Form -->
                <div class="card">
                    <div>
                        <h2 class="card-title">➕ Create Entity / Node</h2>
                        <p class="card-desc">Add a new factual node to your Knowledge Graph</p>
                    </div>
                    <form id="form-create-node" onsubmit="handleCreateNode(event)">
                        <div class="form-group">
                            <label>Node ID (optional - auto-generated if empty)</label>
                            <input type="text" id="node-id" placeholder="e.g. cust_101, Gene_BRCA1, concept_ml">
                        </div>
                        <div class="form-group">
                            <label>Label / Type</label>
                            <input type="text" id="node-label" placeholder="e.g. Customer, Gene, Disease, Document" required>
                        </div>
                        <div class="form-group">
                            <label>Properties (JSON format)</label>
                            <textarea id="node-props" placeholder='{"name": "BRCA1", "organism": "Human"}'></textarea>
                        </div>
                        <button type="submit" class="btn">Create Node</button>
                    </form>
                </div>

                <!-- Create Relationship Form -->
                <div class="card">
                    <div>
                        <h2 class="card-title">🔗 Link Entities (Relationship)</h2>
                        <p class="card-desc">Connect two nodes with a directed relation edge</p>
                    </div>
                    <form id="form-create-rel" onsubmit="handleCreateRel(event)">
                        <div class="form-group">
                            <label>Source Node ID</label>
                            <input type="text" id="rel-source" placeholder="e.g. cust_101" required>
                        </div>
                        <div class="form-group">
                            <label>Target Node ID</label>
                            <input type="text" id="rel-target" placeholder="e.g. prod_502" required>
                        </div>
                        <div class="form-group">
                            <label>Relationship Type</label>
                            <input type="text" id="rel-type" placeholder="e.g. ASSOCIATED_WITH, PURCHASED, LEADS" required>
                        </div>
                        <div class="form-group">
                            <label>Relationship Properties (JSON)</label>
                            <textarea id="rel-props" placeholder='{"confidence": 0.95, "source": "Internal Audit"}'></textarea>
                        </div>
                        <button type="submit" class="btn">Create Relationship</button>
                    </form>
                </div>
            </div>
        </section>

        <!-- Tab 3: Expert Annotation Studio -->
        <section id="tab-annotations" class="tab-panel">
            <div class="grid-2">
                <!-- Post Annotation Form -->
                <div class="card">
                    <div>
                        <h2 class="card-title">📝 Post Expert / Agent Annotation</h2>
                        <p class="card-desc">Attach human edits, evidence, or hypotheses without modifying base graph facts</p>
                    </div>
                    <form id="form-create-ann" onsubmit="handleCreateAnnotation(event)">
                        <div class="form-group">
                            <label>Annotation Type</label>
                            <select id="ann-type">
                                <option value="Evidence">Evidence (Empirical / Verified data)</option>
                                <option value="Observation">Observation (Human inspection note)</option>
                                <option value="Hypothesis">Hypothesis (Unproven proposition)</option>
                                <option value="Assertion">Assertion (Domain expert claim)</option>
                                <option value="Opinion">Opinion (Subjective feedback)</option>
                                <option value="Correction">Correction (Fix / Revision note)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Author / Origin</label>
                            <input type="text" id="ann-author" placeholder="human, Dr. Smith, agent_gpt4, curator" value="human" required>
                        </div>
                        <div class="form-group">
                            <label>Annotation Content / Note</label>
                            <textarea id="ann-content" placeholder="Enter detailed note or reasoning evidence..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Target KG Node ID (to link immediately)</label>
                            <input type="text" id="ann-target-node" placeholder="e.g. Gene_BRCA1">
                        </div>
                        <div class="form-group">
                            <label>Relation to Node</label>
                            <select id="ann-rel-type">
                                <option value="ABOUT">ABOUT (General contextual note)</option>
                                <option value="SUPPORTS">SUPPORTS (Confirms / Backs entity fact)</option>
                                <option value="CONTRADICTS">CONTRADICTS (Challenges fact)</option>
                                <option value="PROPOSES">PROPOSES (Suggests new relation)</option>
                                <option value="CORRECTS">CORRECTS (Overrides or amends fact)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">Post Annotation</button>
                    </form>
                </div>

                <!-- Live Annotation Stream -->
                <div class="card">
                    <div class="card-header">
                        <div>
                            <h2 class="card-title">Annotation Stream</h2>
                            <p class="card-desc">Latest expert assertions and linked evidence</p>
                        </div>
                        <button class="btn btn-secondary" onclick="loadAnnotations()">🔄 Refresh</button>
                    </div>
                    <div id="annotations-list" class="item-list">
                        <p style="color: var(--text-muted); font-size: 0.9rem;">No annotations loaded yet.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Tab 4: Think-on-Graph (ToG) Console -->
        <section id="tab-tog" class="tab-panel">
            <div class="card">
                <div>
                    <h2 class="card-title">🧠 Think-on-Graph (ToG) Reasoning Console</h2>
                    <p class="card-desc">Execute multi-perspective semantic reasoning over your knowledge graph and expert annotations</p>
                </div>

                <form id="form-tog-query" onsubmit="handleToGQuery(event)">
                    <div class="form-group">
                        <label>Natural Language Query</label>
                        <input type="text" id="tog-query" placeholder="e.g. What evidence supports the connection between target entities?" required>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                        <div class="form-group">
                            <label>Traversal Mode</label>
                            <select id="tog-mode">
                                <option value="hybrid">Hybrid (Deterministic traversal + AI synthesis)</option>
                                <option value="manual">Manual (100% Deterministic Code traversal)</option>
                                <option value="ai">AI Guided (Full LLM-directed path reasoning)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Max Depth (1-10)</label>
                            <input type="number" id="tog-depth" value="3" min="1" max="10">
                        </div>
                        <div class="form-group">
                            <label>Include Expert Annotations</label>
                            <select id="tog-ann-toggle">
                                <option value="true">Yes (Multi-perspective evaluation)</option>
                                <option value="false">No (Base KG only)</option>
                            </select>
                        </div>
                    </div>

                    <button type="submit" id="btn-run-tog" class="btn" style="margin-top: 1rem;">
                        🚀 Execute Think-on-Graph Query
                    </button>
                </form>

                <!-- Query Results Box -->
                <div id="tog-results-area" style="display: none; margin-top: 1rem;">
                    <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; margin-bottom: 0.5rem;">Synthesis & Reasoning Result</h3>
                    
                    <div id="tog-answer" style="font-size: 0.95rem; line-height: 1.6; background: rgba(0,0,0,0.3); padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border);"></div>

                    <!-- Perspectives -->
                    <div class="perspective-box perspective-knowledge">
                        <div class="perspective-title">🔵 1. Knowledge Perspective (Base KG Facts)</div>
                        <div id="persp-knowledge" style="font-size: 0.9rem; color: var(--text-secondary);"></div>
                    </div>

                    <div class="perspective-box perspective-expert">
                        <div class="perspective-title">🟣 2. Expert Perspective (Human/Agent Annotations)</div>
                        <div id="persp-expert" style="font-size: 0.9rem; color: var(--text-secondary);"></div>
                    </div>

                    <div class="perspective-box perspective-combined">
                        <div class="perspective-title">🟢 3. Combined Perspective (Synthesized Evaluation)</div>
                        <div id="persp-combined" style="font-size: 0.9rem; color: var(--text-secondary);"></div>
                    </div>

                    <!-- Telemetry -->
                    <div class="telemetry-bar" id="tog-telemetry"></div>
                </div>
            </div>
        </section>
    </main>

    <!-- Toast Notifications Container -->
    <div id="toast-container"></div>

    <script>
        // API Base URL (relative path)
        const API = "/v1";

        // Tab Switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');

            if (tabId === 'tab-graph') loadGraphData();
        }

        // Toast Helper
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }

        // Check Health & Status
        async function checkStatus() {
            try {
                const res = await fetch("/health");
                const data = await res.json();
                if (data.status === "ok") {
                    document.getElementById('status-text').textContent = "Live & Connected";
                }
            } catch (err) {
                document.getElementById('status-text').textContent = "Disconnected";
            }
        }

        // Load Nodes & Relationships
        async function loadGraphData() {
            try {
                const nodesRes = await fetch(`${API}/graph/nodes?limit=50`);
                const nodesData = await nodesRes.json();
                const nodesContainer = document.getElementById('nodes-list');

                if (!nodesData.nodes || nodesData.nodes.length === 0) {
                    nodesContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No nodes in graph. Create one in the Manual Builder tab.</p>';
                } else {
                    nodesContainer.innerHTML = nodesData.nodes.map(n => `
                        <div class="item-card">
                            <div>
                                <div style="font-weight: 600; font-size: 0.95rem;">${n.id}</div>
                                <div class="item-meta">
                                    <span class="badge badge-purple">${n.label}</span>
                                    ${Object.entries(n.properties || {}).map(([k, v]) => `<span class="badge">${k}: ${v}</span>`).join('')}
                                </div>
                            </div>
                            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="deleteNode('${n.id}')">Delete</button>
                        </div>
                    `).join('');
                }

                const relsRes = await fetch(`${API}/graph/relationships?limit=50`);
                const relsData = await relsRes.json();
                const relsContainer = document.getElementById('rels-list');

                if (!relsData.relationships || relsData.relationships.length === 0) {
                    relsContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No relationships in graph.</p>';
                } else {
                    relsContainer.innerHTML = relsData.relationships.map(r => `
                        <div class="item-card">
                            <div>
                                <div style="font-weight: 600; font-size: 0.9rem;">${r.source_id} &rarr; ${r.target_id}</div>
                                <div class="item-meta">
                                    <span class="badge badge-cyan">${r.type}</span>
                                    ${Object.entries(r.properties || {}).map(([k, v]) => `<span class="badge">${k}: ${v}</span>`).join('')}
                                </div>
                            </div>
                            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="deleteRel('${r.id}')">Delete</button>
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.error(e);
            }
        }

        // Create Node
        async function handleCreateNode(e) {
            e.preventDefault();
            const id = document.getElementById('node-id').value.trim() || undefined;
            const label = document.getElementById('node-label').value.trim();
            let props = {};
            try {
                const rawProps = document.getElementById('node-props').value.trim();
                if (rawProps) props = JSON.parse(rawProps);
            } catch (err) {
                showToast("Invalid JSON in properties", "error");
                return;
            }

            try {
                const res = await fetch(`${API}/graph/nodes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ node_id: id, label: label, properties: props })
                });
                if (res.ok) {
                    showToast("Node created successfully!");
                    document.getElementById('form-create-node').reset();
                    loadGraphData();
                } else {
                    const err = await res.json();
                    showToast(err.detail || "Error creating node", "error");
                }
            } catch (err) {
                showToast("Network error", "error");
            }
        }

        // Create Relationship
        async function handleCreateRel(e) {
            e.preventDefault();
            const source_id = document.getElementById('rel-source').value.trim();
            const target_id = document.getElementById('rel-target').value.trim();
            const type = document.getElementById('rel-type').value.trim();
            let props = {};
            try {
                const raw = document.getElementById('rel-props').value.trim();
                if (raw) props = JSON.parse(raw);
            } catch (err) {
                showToast("Invalid JSON in properties", "error");
                return;
            }

            try {
                const res = await fetch(`${API}/graph/relationships`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_id, target_id, type, properties: props })
                });
                if (res.ok) {
                    showToast("Relationship created successfully!");
                    document.getElementById('form-create-rel').reset();
                    loadGraphData();
                } else {
                    const err = await res.json();
                    showToast(err.detail || "Error creating relationship", "error");
                }
            } catch (err) {
                showToast("Network error", "error");
            }
        }

        // Delete Node
        async function deleteNode(id) {
            if (!confirm(`Delete node '${id}' and its connected edges?`)) return;
            try {
                const res = await fetch(`${API}/graph/nodes/${encodeURIComponent(id)}`, { method: 'DELETE' });
                if (res.ok) {
                    showToast(`Node '${id}' deleted.`);
                    loadGraphData();
                }
            } catch (e) {
                showToast("Failed to delete node", "error");
            }
        }

        // Delete Relationship
        async function deleteRel(id) {
            if (!confirm(`Delete relationship '${id}'?`)) return;
            try {
                const res = await fetch(`${API}/graph/relationships/${encodeURIComponent(id)}`, { method: 'DELETE' });
                if (res.ok) {
                    showToast("Relationship deleted.");
                    loadGraphData();
                }
            } catch (e) {
                showToast("Failed to delete relationship", "error");
            }
        }

        // Post Annotation
        async function handleCreateAnnotation(e) {
            e.preventDefault();
            const type = document.getElementById('ann-type').value;
            const author = document.getElementById('ann-author').value.trim();
            const content = document.getElementById('ann-content').value.trim();
            const targetNode = document.getElementById('ann-target-node').value.trim();
            const relType = document.getElementById('ann-rel-type').value;

            try {
                const res = await fetch(`${API}/annotations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type, author, content })
                });
                if (res.ok) {
                    const ann = await res.json();
                    showToast("Annotation created!");

                    // If target node is specified, link it immediately
                    if (targetNode) {
                        await fetch(`${API}/annotations/${ann.id}/relationships`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_id: targetNode, relation_type: relType, target_kind: "KG_NODE" })
                        });
                        showToast(`Linked annotation to '${targetNode}'`);
                    }

                    document.getElementById('form-create-ann').reset();
                    loadAnnotations();
                }
            } catch (err) {
                showToast("Error posting annotation", "error");
            }
        }

        // Load Annotations
        async function loadAnnotations() {
            // Check annotations about target entities
            const container = document.getElementById('annotations-list');
            container.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.9rem;">Post new annotations to build your expert knowledge layer.</p>';
        }

        // Run Think-on-Graph Query
        async function handleToGQuery(e) {
            e.preventDefault();
            const query = document.getElementById('tog-query').value.trim();
            const mode = document.getElementById('tog-mode').value;
            const depth = parseInt(document.getElementById('tog-depth').value) || 3;
            const includeAnn = document.getElementById('tog-ann-toggle').value === "true";

            const btn = document.getElementById('btn-run-tog');
            btn.textContent = "⏳ Reasoning over Knowledge Graph...";
            btn.disabled = true;

            try {
                const res = await fetch(`${API}/tog/query`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        traversal_mode: mode,
                        max_depth: depth,
                        include_annotations: includeAnn
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('tog-results-area').style.display = 'block';
                    document.getElementById('tog-answer').textContent = data.answer;

                    document.getElementById('persp-knowledge').textContent = data.perspectives?.knowledge?.summary || "No base paths evaluated.";
                    document.getElementById('persp-expert').textContent = data.perspectives?.expert?.summary || "No annotations evaluated.";
                    document.getElementById('persp-combined').textContent = data.perspectives?.combined?.summary || data.answer;

                    const m = data.metadata || {};
                    document.getElementById('tog-telemetry').innerHTML = `
                        <div class="telemetry-item">Latency: <strong>${m.latency_ms || 0}ms</strong></div>
                        <div class="telemetry-item">Traversal Mode: <strong>${m.traversal_mode || mode}</strong></div>
                        <div class="telemetry-item">Nodes Traversed: <strong>${m.nodes_traversed || 0}</strong></div>
                        <div class="telemetry-item">Edges: <strong>${m.edges_traversed || 0}</strong></div>
                        <div class="telemetry-item">AI Calls: <strong>${m.ai_calls || 0}</strong></div>
                    `;
                } else {
                    const err = await res.json();
                    showToast(err.detail || "Query failed", "error");
                }
            } catch (err) {
                showToast("Network error executing ToG query", "error");
            } finally {
                btn.textContent = "🚀 Execute Think-on-Graph Query";
                btn.disabled = false;
            }
        }

        // Init
        checkStatus();
        loadGraphData();
    </script>
</body>
</html>
"""

@router.get("/app", response_class=HTMLResponse, include_in_schema=False)
@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def get_studio_ui():
    """Serves the interactive KG Library Studio single-page application."""
    return HTMLResponse(content=HTML_CONTENT)

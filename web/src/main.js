import './style.css';
import { CanvasRenderer } from './CanvasRenderer.js';

let renderer;
let segmentsData = {};

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize UI
    const loader = document.getElementById('canvas-loader');
    loader.classList.add('visible');
    
    const canvas = document.getElementById('seismic-canvas');
    renderer = new CanvasRenderer(canvas, handleHover);
    
    // Setup Top Navigation
    const nav = document.getElementById('segment-selector');
    
    // Load index
    try {
        const res = await fetch('/data/index.json');
        const indexList = await res.json();
        
        indexList.forEach((segmentInfo, i) => {
            const btn = document.createElement('button');
            btn.className = 'btn-segment';
            // Capitalize label
            btn.textContent = segmentInfo.label.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            btn.dataset.id = segmentInfo.id;
            btn.onclick = () => loadSegment(segmentInfo.id);
            nav.appendChild(btn);
        });
        
        // Auto load first
        if (indexList.length > 0) {
            loadSegment(indexList[0].id);
        }
    } catch (e) {
        console.error("Failed to load dataset", e);
        loader.textContent = "Error loading data!";
    }
    
    // Setup Toggles
    document.getElementById('toggle-manual').addEventListener('change', (e) => {
        renderer.toggleLayer('manual', e.target.checked);
    });
    document.getElementById('toggle-baseline').addEventListener('change', (e) => {
        renderer.toggleLayer('baseline', e.target.checked);
    });
    document.getElementById('toggle-corrected').addEventListener('change', (e) => {
        renderer.toggleLayer('corrected', e.target.checked);
    });
});

async function loadSegment(segmentId) {
    const loader = document.getElementById('canvas-loader');
    loader.classList.add('visible');
    
    // Update active nav button
    document.querySelectorAll('.btn-segment').forEach(b => b.classList.remove('active'));
    document.querySelector(`.btn-segment[data-id="${segmentId}"]`)?.classList.add('active');
    
    // Fetch if needed
    if (!segmentsData[segmentId]) {
        const res = await fetch(`/data/${segmentId}.json`);
        segmentsData[segmentId] = await res.json();
    }
    
    const data = segmentsData[segmentId];
    
    // Update text
    document.getElementById('segment-id-display').textContent = data.id;
    document.getElementById('metric-baseline').textContent = data.metrics.baseline_mae.toFixed(3) + ' ms';
    document.getElementById('metric-corrected').textContent = data.metrics.corrected_mae.toFixed(3) + ' ms';
    
    const improvement = data.metrics.improvement_mae;
    const impEl = document.getElementById('metric-improvement');
    impEl.textContent = (improvement > 0 ? '+' : '') + improvement.toFixed(3) + ' ms';
    impEl.style.color = improvement > 0 ? 'var(--accent-lime)' : 'var(--accent-manual)';
    
    // Give time for UI composite before expensive canvas draw
    setTimeout(() => {
        renderer.setData(data);
        loader.classList.remove('visible');
    }, 50);
}

function handleHover(traceIdx, data) {
    const inspector = document.getElementById('hover-inspector');
    
    if (traceIdx < 0 || !data) {
        inspector.className = 'hover-inspector empty';
        inspector.innerHTML = '<span class="trace-id">Hover over trace</span>';
        return;
    }
    
    const isValid = data.valid[traceIdx];
    const sampleMs = data.sample_ms;
    
    if (!isValid) {
        inspector.className = 'hover-inspector active';
        inspector.innerHTML = `
            <span class="trace-id">Trace ${traceIdx} (Invalid Label)</span>
        `;
        return;
    }
    
    const gt = data.fb_idx[traceIdx];
    const base = data.baseline_idx[traceIdx];
    const corr = data.corrected_idx[traceIdx];
    
    const baseErr = Math.abs(base - gt) * sampleMs;
    const corrErr = Math.abs(corr - gt) * sampleMs;
    
    inspector.className = 'hover-inspector active';
    inspector.innerHTML = `
        <span class="trace-id">Trace ${traceIdx} Logs</span>
        <div class="err-row err-baseline">
            <span>Baseline Error:</span>
            <span>${baseErr.toFixed(2)} ms</span>
        </div>
        <div class="err-row err-corrected">
            <span>Corrected Error:</span>
            <span>${corrErr.toFixed(2)} ms</span>
        </div>
    `;
}

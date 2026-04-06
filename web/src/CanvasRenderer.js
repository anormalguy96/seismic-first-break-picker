export class CanvasRenderer {
  constructor(canvasElement, onHover) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.onHover = onHover; // Callback for hover inspector
    
    this.data = null;
    this.visibility = {
      manual: true,
      baseline: true,
      corrected: true
    };
    
    // Scale for rendering (logical vs physical)
    this.canvasWidth = 0;
    this.canvasHeight = 0;
    
    this.bindEvents();
  }
  
  bindEvents() {
    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.data) return;
      const rect = this.canvas.getBoundingClientRect();
      // map mouse X to trace index
      const x = e.clientX - rect.left;
      const width = rect.width;
      const traces = this.data.shape[1];
      const traceIdx = Math.floor((x / width) * traces);
      
      if (traceIdx >= 0 && traceIdx < traces) {
         this.onHover(traceIdx, this.data);
      }
    });
    
    this.canvas.addEventListener('mouseleave', () => {
      this.onHover(-1, null); // Hide
    });
    
    window.addEventListener('resize', () => this.resizeCanvas());
  }
  
  setData(segmentData) {
    this.data = segmentData;
    this.resizeCanvas();
  }
  
  toggleLayer(layer, isVisible) {
    this.visibility[layer] = isVisible;
    this.render();
  }
  
  resizeCanvas() {
    if (!this.data) return;
    const parent = this.canvas.parentElement;
    this.canvas.width = parent.clientWidth;
    this.canvas.height = parent.clientHeight;
    this.canvasWidth = this.canvas.width;
    this.canvasHeight = this.canvas.height;
    this.render();
  }
  
  render() {
    if (!this.data) return;
    
    this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
    
    // 1. Draw image panel
    this.drawPanel();
    
    // 2. Draw lines
    if (this.visibility.manual) this.drawLineSegment(this.data.fb_idx, 'rgba(239, 68, 68, 0.9)', 1.5, true);
    if (this.visibility.baseline) this.drawLineSegment(this.data.baseline_idx, 'rgba(6, 182, 212, 0.9)', 1.2, false);
    if (this.visibility.corrected) this.drawLineSegment(this.data.corrected_idx, 'rgba(16, 185, 129, 1.0)', 1.5, false);
  }
  
  drawPanel() {
    // panel is a 2D array [height][width] from Python JSON export
    const [height, width] = this.data.shape;
    const imgData = this.ctx.createImageData(width, height);
    const panel = this.data.panel;
    
    for (let row = 0; row < height; row++) {
        const rowData = panel[row];
        for (let col = 0; col < width; col++) {
            const val = rowData[col];
            const idx = (row * width + col) * 4;
            const isValid = this.data.valid[col];

            if (isValid) {
                imgData.data[idx]     = val;  // R
                imgData.data[idx + 1] = val;  // G
                imgData.data[idx + 2] = val;  // B
            } else {
                // Subtle warm red tint for traces with no ground-truth label
                imgData.data[idx]     = Math.min(255, val + 40); // R
                imgData.data[idx + 1] = Math.max(0,   val - 15); // G
                imgData.data[idx + 2] = Math.max(0,   val - 15); // B
            }
            imgData.data[idx + 3] = 255; // Alpha fully opaque
        }
    }

    // Offscreen canvas to allow GPU-accelerated scaling via drawImage
    const offscreen = document.createElement('canvas');
    offscreen.width  = width;
    offscreen.height = height;
    offscreen.getContext('2d').putImageData(imgData, 0, 0);
    this.ctx.drawImage(offscreen, 0, 0, this.canvasWidth, this.canvasHeight);
  }
  
  drawLineSegment(indices, color, lineWidth, checkValid) {
    const [height, width] = this.data.shape;
    const scaleX = this.canvasWidth / width;
    const scaleY = this.canvasHeight / height;
    
    this.ctx.beginPath();
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    
    let isDrawing = false;
    for (let x = 0; x < width; x++) {
      // If checkValid is true (for manual picks), skip invalid traces
      if (checkValid && !this.data.valid[x]) {
         isDrawing = false;
         continue;
      }
      
      const px = x * scaleX;
      const py = indices[x] * scaleY;
      
      if (!isDrawing) {
        this.ctx.moveTo(px, py);
        isDrawing = true;
      } else {
        this.ctx.lineTo(px, py);
      }
    }
    this.ctx.stroke();
  }
}

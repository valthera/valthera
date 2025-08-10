#!/usr/bin/env python3

import asyncio
import json
import os
from typing import Optional

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

try:
    import pyrealsense2 as rs  # type: ignore
    REALSENSE_AVAILABLE = True
except Exception:
    REALSENSE_AVAILABLE = False
    rs = None  # type: ignore


# Configuration
API_TOKEN = "valthera-dev-password"
HTTP_PORT = int(os.environ.get("CAMERA_HTTP_PORT", "8000"))
STREAM_W, STREAM_H, FPS = 640, 480, 15

app = FastAPI()

# CORS for easy local testing from browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


pipeline: Optional["rs.pipeline"] = None  # type: ignore
intrinsics_cache: Optional[dict] = None
depth_scale_m: Optional[float] = None


def start_camera_if_needed() -> None:
    global pipeline, intrinsics_cache, depth_scale_m
    if pipeline is not None:
        return
    if not REALSENSE_AVAILABLE:
        raise RuntimeError("pyrealsense2 not available in this environment")

    cfg = rs.config()  # type: ignore
    cfg.enable_stream(rs.stream.depth, STREAM_W, STREAM_H, rs.format.z16, FPS)  # type: ignore
    pipeline = rs.pipeline()  # type: ignore
    profile = pipeline.start(cfg)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale_m = float(depth_sensor.get_depth_scale())

    depth_stream = profile.get_stream(rs.stream.depth)
    intr = depth_stream.as_video_stream_profile().get_intrinsics()
    intrinsics_cache = {
        "width": int(intr.width),
        "height": int(intr.height),
        "fx": float(intr.fx),
        "fy": float(intr.fy),
        "cx": float(intr.ppx),
        "cy": float(intr.ppy),
        "depth_scale_m": depth_scale_m,
    }


@app.on_event("startup")
def on_startup() -> None:
    # Do not auto-start camera on startup to avoid blocking when no device is present.
    # Camera will be started lazily on first intrinsics request or websocket connect.
    return None


@app.get("/health")
def health() -> JSONResponse:
    status = {
        "realsense_available": REALSENSE_AVAILABLE,
        "camera_started": pipeline is not None,
        "intrinsics_ready": intrinsics_cache is not None,
    }
    return JSONResponse(status)


@app.get("/v1/intrinsics")
def get_intrinsics(authorization: str = Header(default="")):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if intrinsics_cache is None:
        # Try starting camera on-demand
        start_camera_if_needed()
    if intrinsics_cache is None:
        raise HTTPException(status_code=503, detail="Camera not ready")
    return intrinsics_cache


@app.websocket("/v1/ws/depth")
async def ws_depth(ws: WebSocket):
    token_ok = (
        ws.headers.get("authorization") == f"Bearer {API_TOKEN}" or
        ws.query_params.get("token") == API_TOKEN
    )
    if not token_ok:
        await ws.close(code=4401)
        return

    await ws.accept()
    try:
        start_camera_if_needed()
    except Exception:
        await ws.close(code=1011)
        return

    try:
        assert pipeline is not None
        while True:
            frames = pipeline.wait_for_frames()  # type: ignore
            d = frames.get_depth_frame()
            if not d:
                await asyncio.sleep(0)
                continue
            depth_np = np.asanyarray(d.get_data()).astype(np.uint16)
            header = {
                "type": "frame",
                "fmt": "z16_le",
                "width": int(depth_np.shape[1]),
                "height": int(depth_np.shape[0]),
                "ts_ms": float(d.get_timestamp()),
            }
            if depth_scale_m is not None:
                header["depth_scale_m"] = depth_scale_m
            await ws.send_text(json.dumps(header))
            await ws.send_bytes(depth_np.tobytes(order="C"))
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        return


VIEWER_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Valthera Depth Viewer</title>
    <style>
      body { font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\"; margin: 0; padding: 0; background: #0b0d12; color: #e5e7eb; }
      header { padding: 12px 16px; background: #111827; border-bottom: 1px solid #1f2937; display:flex; justify-content:space-between; align-items:center }
      .muted { color: #9ca3af; font-size: 12px }
      main { padding: 16px; display:flex; gap:16px; flex-wrap: wrap; }
      canvas { background: #000; image-rendering: pixelated; border: 1px solid #1f2937 }
      .panel { padding: 12px; background: #111827; border: 1px solid #1f2937; border-radius: 8px; }
      input { background:#0b0d12; color:#e5e7eb; border:1px solid #374151; border-radius:6px; padding:6px 8px }
      button { background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 10px; cursor:pointer }
    </style>
  </head>
  <body>
    <header>
      <div>
        <strong>Valthera Depth Viewer</strong>
        <div class=\"muted\">WebSocket depth stream</div>
      </div>
      <div class=\"muted\" id=\"status\">disconnected</div>
    </header>
    <main>
      <div class=\"panel\">
        <div style=\"display:flex; gap:8px; align-items:center; flex-wrap:wrap\">
          <label>Token</label>
          <input id=\"token\" value=\"valthera-dev-password\" style=\"min-width:240px\" />
          <button id=\"connect\">Connect</button>
        </div>
      </div>
      <div class=\"panel\">
        <canvas id=\"c\" width=640 height=480></canvas>
      </div>
    </main>
    <script>
      const statusEl = document.getElementById('status');
      const canvas = document.getElementById('c');
      const ctx = canvas.getContext('2d');
      const tokenInput = document.getElementById('token');
      const connectBtn = document.getElementById('connect');

      let expectingBinary = false;
      let header = null;
      let ws = null;

      function setStatus(text) { statusEl.textContent = text; }

      function renderDepth(buffer, width, height) {
        const depth = new Uint16Array(buffer);
        const img = ctx.createImageData(width, height);
        // Simple scaling: assume up to ~5m, map to 0..255
        const scale = 5000 / 255; // mm per 8-bit level (approx)
        for (let i = 0, j = 0; i < depth.length; i++, j += 4) {
          const v16 = depth[i];
          const v = Math.min(255, Math.floor(v16 / scale));
          img.data[j] = v;
          img.data[j+1] = v;
          img.data[j+2] = v;
          img.data[j+3] = 255;
        }
        ctx.putImageData(img, 0, 0);
      }

      function connect() {
        if (ws) { try { ws.close(); } catch(e){} }
        const token = tokenInput.value.trim();
        const url = `ws://${location.host}/v1/ws/depth?token=${encodeURIComponent(token)}`;
        ws = new WebSocket(url);
        ws.binaryType = 'arraybuffer';
        ws.onopen = () => setStatus('connected');
        ws.onclose = () => setStatus('disconnected');
        ws.onerror = () => setStatus('error');
        ws.onmessage = (ev) => {
          if (typeof ev.data === 'string') {
            header = JSON.parse(ev.data);
            expectingBinary = true;
            canvas.width = header.width;
            canvas.height = header.height;
          } else if (expectingBinary) {
            renderDepth(ev.data, header.width, header.height);
            expectingBinary = false;
          }
        };
      }

      connectBtn.addEventListener('click', connect);
    </script>
  </body>
</html>
"""


@app.get("/viewer")
def viewer() -> HTMLResponse:
    return HTMLResponse(content=VIEWER_HTML)


def main() -> None:
    # Optional local run: uvicorn camera.server:app --host 0.0.0.0 --port 8000
    import uvicorn  # type: ignore
    uvicorn.run("camera.server:app", host="0.0.0.0", port=HTTP_PORT, reload=False)


if __name__ == "__main__":
    main()


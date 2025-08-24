import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert'

type DepthHeader = {
  type: 'frame'
  fmt: 'z16_le'
  width: number
  height: number
  ts_ms: number
  depth_scale_m?: number
}

export function DepthViewer() {
  const [searchParams, setSearchParams] = useSearchParams()
  const defaultIp = searchParams.get('ip') ?? ''
  const defaultToken = searchParams.get('token') ?? ''

  const [ipAddress, setIpAddress] = useState<string>(defaultIp)
  const [token, setToken] = useState<string>(defaultToken)
  const [status, setStatus] = useState<string>('disconnected')
  const [error, setError] = useState<string>('')
  const [header, setHeader] = useState<DepthHeader | null>(null)
  const [fps, setFps] = useState<number>(0)
  const [lastTimestampMs, setLastTimestampMs] = useState<number | null>(null)
  const [lastMessageAt, setLastMessageAt] = useState<number>(0)

  const containerRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const websocketRef = useRef<WebSocket | null>(null)
  const expectingBinaryRef = useRef<boolean>(false)
  const latestHeaderRef = useRef<DepthHeader | null>(null)
  const latestBufferRef = useRef<ArrayBuffer | null>(null)
  const lastDrawnSizeRef = useRef<{ w: number; h: number } | null>(null)
  const cachedImageDataRef = useRef<ImageData | null>(null)
  const rafRef = useRef<number | null>(null)
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const offscreenCtxRef = useRef<CanvasRenderingContext2D | null>(null)

  const wsUrl = useMemo(() => {
    if (!ipAddress || !token) return ''
    return `ws://${ipAddress}:8000/v1/ws/depth?token=${encodeURIComponent(token)}`
  }, [ipAddress, token])

  const isOnline = useMemo(() => {
    if (status !== 'connected') return false
    return Date.now() - lastMessageAt < 1500
  }, [status, lastMessageAt])

  const updateFps = (tsMs: number) => {
    if (lastTimestampMs !== null) {
      const delta = tsMs - lastTimestampMs
      if (delta > 0) setFps(1000 / delta)
    }
    setLastTimestampMs(tsMs)
  }

  const renderLoop = () => {
    const displayCanvas = canvasRef.current
    const container = containerRef.current
    const hdr = latestHeaderRef.current
    const buf = latestBufferRef.current
    if (displayCanvas && container && hdr && buf) {
      // Prepare offscreen canvas once
      if (!offscreenCanvasRef.current) {
        offscreenCanvasRef.current = document.createElement('canvas')
      }
      const offscreen = offscreenCanvasRef.current
      if (!offscreenCtxRef.current) {
        offscreenCtxRef.current = offscreen.getContext('2d')
      }
      const offctx = offscreenCtxRef.current
      if (!offctx) {
        rafRef.current = window.requestAnimationFrame(renderLoop)
        return
      }

      // Ensure offscreen matches frame dims
      if (!lastDrawnSizeRef.current || lastDrawnSizeRef.current.w !== hdr.width || lastDrawnSizeRef.current.h !== hdr.height) {
        offscreen.width = hdr.width
        offscreen.height = hdr.height
        lastDrawnSizeRef.current = { w: hdr.width, h: hdr.height }
        cachedImageDataRef.current = null
      }

      // Build or reuse ImageData and write grayscale
      let img = cachedImageDataRef.current
      if (!img) {
        img = new ImageData(hdr.width, hdr.height)
        cachedImageDataRef.current = img
      }
      const u16 = new Uint16Array(buf)
      const data = img.data
      const clampMax = 5000
      const scale = clampMax / 255
      let j = 0
      for (let i = 0; i < u16.length; i++) {
        const v16 = u16[i]
        const v = v16 > 0 ? Math.min(255, (v16 / scale) | 0) : 0
        data[j++] = v
        data[j++] = v
        data[j++] = v
        data[j++] = 255
      }
      offctx.putImageData(img, 0, 0)

      // Compute display size to fully fit width without cropping
      const dpr = window.devicePixelRatio || 1
      const containerWidth = container.clientWidth || hdr.width
      const displayWidthCss = containerWidth
      const displayHeightCss = Math.round((hdr.height / hdr.width) * displayWidthCss)
      const displayWidthPx = Math.floor(displayWidthCss * dpr)
      const displayHeightPx = Math.floor(displayHeightCss * dpr)

      const ctx = displayCanvas.getContext('2d')
      if (ctx) {
        // Resize visible canvas backing store to match CSS size * DPR
        if (displayCanvas.width !== displayWidthPx || displayCanvas.height !== displayHeightPx) {
          displayCanvas.width = displayWidthPx
          displayCanvas.height = displayHeightPx
        }
        // Set CSS size explicitly to prevent layout-induced cropping
        displayCanvas.style.width = `${displayWidthCss}px`
        displayCanvas.style.height = `${displayHeightCss}px`

        // Disable smoothing and draw scaled image to fill canvas (letterboxed by container if needed)
        // @ts-expect-error vendor-specific flags may exist
        ctx.imageSmoothingEnabled = false
        // @ts-expect-error vendor-specific flags may exist
        ctx.mozImageSmoothingEnabled = false
        // @ts-expect-error vendor-specific flags may exist
        ctx.webkitImageSmoothingEnabled = false
        ctx.clearRect(0, 0, displayCanvas.width, displayCanvas.height)
        ctx.drawImage(offscreen, 0, 0, displayCanvas.width, displayCanvas.height)
      }
    }
    rafRef.current = window.requestAnimationFrame(renderLoop)
  }

  const connect = () => {
    setError('')
    setStatus('connecting')

    // sync params into URL for easy sharing
    const params = new URLSearchParams()
    if (ipAddress) params.set('ip', ipAddress)
    if (token) params.set('token', token)
    setSearchParams(params)

    if (!wsUrl) {
      setStatus('disconnected')
      setError('Missing ip or token')
      return
    }

    try {
      const ws = new WebSocket(wsUrl)
      websocketRef.current = ws
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => setStatus('connected')
      ws.onclose = () => setStatus('disconnected')
      ws.onerror = () => {
        setStatus('error')
        setError('WebSocket error')
      }
      ws.onmessage = (ev: MessageEvent) => {
        setLastMessageAt(Date.now())
        if (typeof ev.data === 'string') {
          try {
            const hdr = JSON.parse(ev.data) as DepthHeader
            setHeader(hdr)
            latestHeaderRef.current = hdr
            expectingBinaryRef.current = true
            updateFps(hdr.ts_ms)
          } catch (e) {
            // ignore malformed header
          }
        } else if (expectingBinaryRef.current) {
          latestBufferRef.current = ev.data as ArrayBuffer
          expectingBinaryRef.current = false
        }
      }
    } catch (e: any) {
      setStatus('error')
      setError(e?.message || 'Failed to connect')
    }
  }

  useEffect(() => {
    // start render loop
    rafRef.current = window.requestAnimationFrame(renderLoop)
    return () => {
      try { websocketRef.current?.close() } catch {}
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Pulse ring keyframes */}
      <style>{`
        @keyframes pulseRing {
          0% { transform: scale(0.6); opacity: 0.6; }
          50% { transform: scale(1.3); opacity: 0.2; }
          100% { transform: scale(0.6); opacity: 0.6; }
        }
      `}</style>
      <Card className="border">
        <CardHeader>
          <CardTitle>Depth Viewer</CardTitle>
          <CardDescription>
            Connect to a Valthera Camera depth stream via WebSocket
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <div>
              <label className="text-sm text-muted-foreground">Valthera Camera IP</label>
              <Input
                placeholder="192.168.0.237"
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Token</label>
              <Input
                placeholder="valthera-dev-password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={connect} className="w-full md:w-auto">Connect</Button>
              <div className="text-sm text-muted-foreground flex items-center">Status: {status}</div>
            </div>
          </div>

          {error && (
            <Alert className="border-destructive/50">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="relative inline-flex items-center">
                <span
                  className={`inline-block h-2.5 w-2.5 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-gray-400'}`}
                />
                {isOnline && (
                  <span
                    className="absolute inline-flex h-5 w-5 rounded-full opacity-70"
                    style={{
                      boxShadow: '0 0 0 0 rgba(16, 185, 129, 0.7)',
                      animation: 'pulseRing 2s ease-in-out infinite',
                    }}
                  />
                )}
              </span>
              {header ? (
                <span>Frame: {header.width}×{header.height} • fmt: {header.fmt} • scale: {header.depth_scale_m ?? 'n/a'}</span>
              ) : (
                <span>Waiting for header…</span>
              )}
            </div>
            <div className="text-sm">{fps ? `${fps.toFixed(1)} fps` : ''}</div>
          </div>

          <div ref={containerRef} className="w-full overflow-auto">
            <canvas
              ref={canvasRef}
              className="border rounded-md bg-black"
              style={{ display: 'block', imageRendering: 'pixelated' as any }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default DepthViewer


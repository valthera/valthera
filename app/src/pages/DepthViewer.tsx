import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert'

type StreamInfo = {
  width: number
  height: number
  format: string
}

type DepthHeader = {
  type: 'frame'
  timestamp: number
  depth: StreamInfo & { scale_m: number }
  left_rgb: StreamInfo
  right_rgb: StreamInfo
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

  // Separate refs for RGB and depth
  const rgbContainerRef = useRef<HTMLDivElement | null>(null)
  const depthContainerRef = useRef<HTMLDivElement | null>(null)
  const rgbCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const depthCanvasRef = useRef<HTMLCanvasElement | null>(null)
  
  const websocketRef = useRef<WebSocket | null>(null)
  const latestHeaderRef = useRef<DepthHeader | null>(null)
  const rgbBufferRef = useRef<ArrayBuffer | null>(null)
  const depthBufferRef = useRef<ArrayBuffer | null>(null)
  
  // Message counter for the 3-message sequence
  const messageCounterRef = useRef<number>(0)
  
  // Keep the working depth rendering structure
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

  const renderRgb = () => {
    const canvas = rgbCanvasRef.current
    const container = rgbContainerRef.current
    const hdr = latestHeaderRef.current
    const buf = rgbBufferRef.current
    
    if (!canvas || !container || !hdr || !buf) {
      console.log('renderRgb early return:', { hasCanvas: !!canvas, hasContainer: !!container, hasHeader: !!hdr, hasBuffer: !!buf })
      return
    }

    console.log('renderRgb called with buffer size:', buf.byteLength)
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { width, height } = hdr.left_rgb
    
    // Calculate display size
    const containerWidth = container.clientWidth
    const displayWidth = containerWidth
    const displayHeight = Math.round((height / width) * displayWidth)
    
    // Set canvas size
    canvas.width = displayWidth
    canvas.height = displayHeight
    canvas.style.width = `${displayWidth}px`
    canvas.style.height = `${displayHeight}px`

    // Convert BGR8 buffer to RGB ImageData
    const bgrData = new Uint8Array(buf)
    const imgData = ctx.createImageData(width, height)
    
    // BGR8 to RGB conversion
    for (let i = 0, j = 0; i < bgrData.length; i += 3, j += 4) {
      imgData.data[j] = bgrData[i + 2]     // R (from B)
      imgData.data[j + 1] = bgrData[i + 1] // G (from G) 
      imgData.data[j + 2] = bgrData[i]     // B (from R)
      imgData.data[j + 3] = 255            // Alpha
    }

    // Create temporary canvas for scaling
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = width
    tempCanvas.height = height
    const tempCtx = tempCanvas.getContext('2d')
    if (tempCtx) {
      tempCtx.putImageData(imgData, 0, 0)
      
      // Draw scaled to display canvas
      ctx.imageSmoothingEnabled = false
      ctx.drawImage(tempCanvas, 0, 0, displayWidth, displayHeight)
    }
    console.log('renderRgb completed')
  }

  const renderDepth = () => {
    const displayCanvas = depthCanvasRef.current
    const container = depthContainerRef.current
    const hdr = latestHeaderRef.current
    const buf = depthBufferRef.current
    
    if (!displayCanvas || !container || !hdr || !buf) {
      console.log('renderDepth early return:', { hasCanvas: !!displayCanvas, hasContainer: !!container, hasHeader: !!hdr, hasBuffer: !!buf })
      return
    }

    console.log('renderDepth called with buffer size:', buf.byteLength)
    // Use the proven working depth rendering logic
    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas')
    }
    const offscreen = offscreenCanvasRef.current
    if (!offscreenCtxRef.current) {
      offscreenCtxRef.current = offscreen.getContext('2d')
    }
    const offctx = offscreenCtxRef.current
    if (!offctx) return

    // Ensure offscreen matches frame dims
    if (!lastDrawnSizeRef.current || lastDrawnSizeRef.current.w !== hdr.depth.width || lastDrawnSizeRef.current.h !== hdr.depth.height) {
      offscreen.width = hdr.depth.width
      offscreen.height = hdr.depth.height
      lastDrawnSizeRef.current = { w: hdr.depth.width, h: hdr.depth.height }
      cachedImageDataRef.current = null
    }

    // Build or reuse ImageData and write grayscale
    let img = cachedImageDataRef.current
    if (!img) {
      img = new ImageData(hdr.depth.width, hdr.depth.height)
      cachedImageDataRef.current = img
    }
    
    const u16 = new Uint16Array(buf)
    const data = img.data
    
    // Dynamic depth range detection for better visualization
    const validDepths = u16.filter(d => d > 0)
    let minDepth = 0
    let maxDepth = 0
    
    if (validDepths.length > 0) {
      // Use loop-based approach to avoid stack overflow with large arrays
      minDepth = validDepths[0]
      maxDepth = validDepths[0]
      for (let i = 1; i < validDepths.length; i++) {
        const depth = validDepths[i]
        if (depth < minDepth) minDepth = depth
        if (depth > maxDepth) maxDepth = depth
      }
      
      // If range is too small, expand it for better contrast
      if (maxDepth - minDepth < 100) {
        const mid = (minDepth + maxDepth) / 2
        minDepth = Math.max(0, mid - 500)
        maxDepth = mid + 500
      }
    } else {
      // Fallback values if no valid depth data
      minDepth = 0
      maxDepth = 5000
    }
    
    // Ensure we have a valid range
    if (maxDepth <= minDepth) {
      maxDepth = minDepth + 1000
    }
    
    const depthRange = maxDepth - minDepth
    
    console.log('Depth range:', { minDepth, maxDepth, depthRange, validCount: validDepths.length })
    
    let j = 0
    for (let i = 0; i < u16.length; i++) {
      const v16 = u16[i]
      let gray = 0
      
      if (v16 > 0 && depthRange > 0) {
        // Map depth to grayscale: closer = brighter, farther = darker
        // Invert so closer objects are brighter (more intuitive)
        gray = Math.floor(255 * (1 - (v16 - minDepth) / depthRange))
        gray = Math.max(0, Math.min(255, gray))
      }
      
      data[j++] = gray     // R
      data[j++] = gray     // G  
      data[j++] = gray     // B
      data[j++] = 255      // Alpha
    }
    
    offctx.putImageData(img, 0, 0)

    // Compute display size to fully fit width without cropping
    const dpr = window.devicePixelRatio || 1
    const containerWidth = container.clientWidth || hdr.depth.width
    const displayWidthCss = containerWidth
    const displayHeightCss = Math.round((hdr.depth.height / hdr.depth.width) * displayWidthCss)
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
      ctx.imageSmoothingEnabled = false
      ctx.clearRect(0, 0, displayCanvas.width, displayCanvas.height)
      ctx.drawImage(offscreen, 0, 0, displayCanvas.width, displayCanvas.height)
    }
    console.log('renderDepth completed')
  }

  const renderLoop = () => {
    // Render both views if we have data
    if (latestHeaderRef.current) {
      console.log('Render loop - rendering both views, header:', latestHeaderRef.current)
      renderRgb()
      renderDepth()
    } else {
      console.log('Render loop - no header yet')
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
            console.log('Received header:', hdr)
            setHeader(hdr)
            latestHeaderRef.current = hdr
            updateFps(hdr.timestamp)
            
            // Reset buffers for new frame
            rgbBufferRef.current = null
            depthBufferRef.current = null
            messageCounterRef.current = 0 // Reset message counter
            console.log('Reset buffers and message counter for new frame')
          } catch (e) {
            console.error('Failed to parse header:', e)
          }
        } else if (ev.data instanceof ArrayBuffer) {
          console.log('Received binary data:', ev.data.byteLength, 'bytes')
          
          // Handle the 3-message sequence: left RGB, right RGB, depth
          messageCounterRef.current++
          if (messageCounterRef.current === 1) {
            // First binary message = Left RGB
            console.log('Storing first message as RGB data')
            rgbBufferRef.current = ev.data
          } else if (messageCounterRef.current === 2) {
            // Second message = Right RGB (skip it)
            console.log('Skipping second message (right RGB)')
            // Don't store it, just mark that we've seen it
          } else if (messageCounterRef.current === 3) {
            // Third message = Depth data
            console.log('Storing third message as depth data')
            depthBufferRef.current = ev.data
          } else {
            console.log('Unexpected message sequence, resetting')
            // Reset for next frame
            rgbBufferRef.current = null
            depthBufferRef.current = null
            messageCounterRef.current = 0
          }
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
            Connect to a Valthera Camera RGB + depth stream via WebSocket
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
                <span>
                  RGB: {header.left_rgb.width}×{header.left_rgb.height} • 
                  Depth: {header.depth.width}×{header.depth.height} • 
                  Scale: {header.depth.scale_m}m
                </span>
              ) : (
                <span>Waiting for header…</span>
              )}
            </div>
            <div className="text-sm">{fps ? `${fps.toFixed(1)} fps` : ''}</div>
          </div>

          {/* Camera Views - Side by Side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* RGB View */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm">RGB Camera</CardTitle>
              </CardHeader>
              <CardContent>
                <div ref={rgbContainerRef} className="w-full overflow-auto">
                  <canvas
                    ref={rgbCanvasRef}
                    className="border rounded-md bg-black w-full"
                    style={{ display: 'block', imageRendering: 'pixelated' as any }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Depth View */}
            <Card className="border">
              <CardHeader>
                <CardTitle className="text-sm">Depth Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div ref={depthContainerRef} className="w-full overflow-auto">
                  <canvas
                    ref={depthCanvasRef}
                    className="border rounded-md bg-black w-full"
                    style={{ display: 'block', imageRendering: 'pixelated' as any }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default DepthViewer


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
  const [currentView, setCurrentView] = useState<'color' | 'depth'>('color')

  // Single refs for the current view (since we only show one at a time)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  
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
    const canvas = canvasRef.current
    const container = containerRef.current
    const hdr = latestHeaderRef.current
    const buf = rgbBufferRef.current
    
    if (!canvas || !container || !hdr || !buf) {
      console.log('renderRgb early return:', { hasCanvas: !!canvas, hasContainer: !!container, hasHeader: !!hdr, hasBuffer: !!buf, currentView })
      return
    }
    
    console.log('renderRgb: Using RGB buffer, size:', buf.byteLength)

    console.log('renderRgb called with buffer size:', buf.byteLength)
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      console.error('Failed to get 2D context for RGB canvas')
      return
    }

    const { width, height, format } = hdr.left_rgb
    console.log('RGB dimensions:', width, 'x', height, 'format:', format)
    
    // Calculate display size - ensure container has width
    const containerWidth = container.clientWidth || 400 // fallback width
    const displayWidth = Math.max(containerWidth, 200) // minimum width
    const displayHeight = Math.round((height / width) * displayWidth)
    
    // Set canvas size
    canvas.width = displayWidth
    canvas.height = displayHeight
    canvas.style.width = `${displayWidth}px`
    canvas.style.height = `${displayHeight}px`

    // Check if RGB data is compressed (JPEG format)
    if (format === 'jpeg' || hdr.compressed) {
      console.log('Rendering compressed RGB data as JPEG')
      // Use ImageBitmap for compressed RGB data (like the server viewer)
      const blob = new Blob([buf], { type: 'image/jpeg' })
      createImageBitmap(blob).then(bitmap => {
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.imageSmoothingEnabled = false
          ctx.clearRect(0, 0, displayWidth, displayHeight)
          ctx.drawImage(bitmap, 0, 0, displayWidth, displayHeight)
          bitmap.close()
        }
        console.log('renderRgb completed (compressed) - canvas size:', displayWidth, 'x', displayHeight)
      }).catch(err => {
        console.error('JPEG RGB rendering failed:', err)
        // Fallback to raw data processing
        renderRgbRaw(buf, width, height, displayWidth, displayHeight)
      })
      return
    }

    // Handle raw RGB data
    console.log('Rendering raw RGB data')
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
      ctx.clearRect(0, 0, displayWidth, displayHeight)
      ctx.drawImage(tempCanvas, 0, 0, displayWidth, displayHeight)
    }
    console.log('renderRgb completed - canvas size:', displayWidth, 'x', displayHeight)
  }

  const renderRgbRaw = (buf: ArrayBuffer, width: number, height: number, displayWidth: number, displayHeight: number) => {
    console.log('Rendering raw RGB data as fallback')
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

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
      ctx.clearRect(0, 0, displayWidth, displayHeight)
      ctx.drawImage(tempCanvas, 0, 0, displayWidth, displayHeight)
    }
    console.log('renderRgbRaw completed - canvas size:', displayWidth, 'x', displayHeight)
  }

  const renderDepth = () => {
    const displayCanvas = canvasRef.current
    const container = containerRef.current
    const hdr = latestHeaderRef.current
    const buf = depthBufferRef.current
    
    if (!displayCanvas || !container || !hdr || !buf) {
      console.log('renderDepth early return:', { hasCanvas: !!displayCanvas, hasContainer: !!container, hasHeader: !!hdr, hasBuffer: !!buf, currentView })
      return
    }
    
    console.log('renderDepth: Using depth buffer, size:', buf.byteLength)

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
    if (!offctx) {
      console.error('Failed to get 2D context for depth offscreen canvas')
      return
    }

    console.log('Depth dimensions:', hdr.depth.width, 'x', hdr.depth.height, 'format:', hdr.depth.format, 'compressed:', hdr.compressed)

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
    
    // Check if depth data is compressed (PNG format) - but now we send raw data
    if (hdr.depth.format === 'png' || hdr.compressed) {
      console.log('Rendering raw depth data (server now sends raw 16-bit data), buffer size:', buf.byteLength)
      // Server now sends raw 16-bit depth data instead of PNG
      // Process it as raw data for analysis
      renderDepthRaw(buf, hdr.depth.width, hdr.depth.height)
      return
    }

    // Handle raw depth data - match server exactly
    const depth = new Uint16Array(buf)
    const depthImg = ctx.createImageData(hdr.depth.width, hdr.depth.height)
    
    // Enhanced depth visualization for room-scale distances
    const maxDepth = 4000; // 4 meters in mm (covers 10ft+ room)
    const minDepth = 50;   // 5cm minimum depth (very close range)
    
    let minVal = 65535;
    let maxVal = 0;
    
    // Find actual min/max values for better contrast
    for (let i = 0; i < depth.length; i++) {
      if (depth[i] > 0 && depth[i] < 65535) {
        minVal = Math.min(minVal, depth[i]);
        maxVal = Math.max(maxVal, depth[i]);
      }
    }
    
    // Use actual range with aggressive contrast enhancement
    let actualMin = Math.max(minDepth, minVal);
    let actualMax = Math.min(maxDepth, maxVal);
    
    // Force a reasonable range for better contrast
    let range = actualMax - actualMin;
    if (range < 2000) {
      // If range is too small, force a wider range for better visibility
      const mid = (actualMin + actualMax) / 2;
      actualMin = Math.max(50, mid - 1500);
      actualMax = Math.min(4000, mid + 1500);
      range = actualMax - actualMin;
      console.log(`Forced depth range for better contrast: ${actualMin}mm - ${actualMax}mm`);
    }
    
    // Additional contrast boost - use only the middle 80% of the range for better visibility
    const contrastBoost = 0.2; // Use 20% padding on each end
    const adjustedMin = actualMin + (range * contrastBoost);
    const adjustedMax = actualMax - (range * contrastBoost);
    const adjustedRange = adjustedMax - adjustedMin;
    
    console.log(`🔄 Final depth range: ${adjustedMin}mm - ${adjustedMax}mm (${Math.round(adjustedMin/10)}cm - ${Math.round(adjustedMax/10)}cm)`);
    
    for (let i = 0, j = 0; i < depth.length; i++, j += 4) {
      const v16 = depth[i];
      
      if (v16 === 0 || v16 >= 65535) {
        // Invalid depth - show as black
        depthImg.data[j] = 0;
        depthImg.data[j+1] = 0;
        depthImg.data[j+2] = 0;
        depthImg.data[j+3] = 255;
      } else {
        // Map depth to grayscale: closer = white, farther = black
        // Closer objects have smaller depth values, farther objects have larger depth values
        const normalized = Math.max(0, Math.min(1, (v16 - adjustedMin) / adjustedRange));
        
        // Apply strong contrast curve for better visibility
        const gamma = 0.4; // Lower gamma = much brighter mid-tones
        const contrastNormalized = Math.pow(normalized, gamma);
        
        // INVERT: closer objects (small depth values) should be white (high grayscale)
        // farther objects (large depth values) should be black (low grayscale)
        const grayscale = Math.floor((1 - contrastNormalized) * 255);
        
        // Apply additional contrast boost
        const boostedGrayscale = Math.min(255, Math.max(0, grayscale * 1.5));
        
        // Set all RGB channels to the same grayscale value
        depthImg.data[j] = boostedGrayscale;     // R
        depthImg.data[j+1] = boostedGrayscale;   // G
        depthImg.data[j+2] = boostedGrayscale;   // B
        depthImg.data[j+3] = 255;                // A
      }
    }
    
    // Calculate average depth in center square and highlight it
    const centerX = Math.floor(hdr.depth.width / 2)
    const centerY = Math.floor(hdr.depth.height / 2)
    const squareSize = 40 // 40x40 pixel square in center
    const halfSquare = Math.floor(squareSize / 2)
    
    let centerDepthSum = 0
    let centerDepthCount = 0
    const centerDepths = []
    
    // Calculate average depth in center square
    for (let y = centerY - halfSquare; y < centerY + halfSquare; y++) {
      for (let x = centerX - halfSquare; x < centerX + halfSquare; x++) {
        if (x >= 0 && x < hdr.depth.width && y >= 0 && y < hdr.depth.height) {
          const idx = y * hdr.depth.width + x
          const depthValue = depth[idx]
          if (depthValue > 0 && depthValue < 65535) {
            centerDepths.push(depthValue)
            centerDepthSum += depthValue
            centerDepthCount++
          }
        }
      }
    }
    
    const averageDepth = centerDepthCount > 0 ? centerDepthSum / centerDepthCount : 0
    const averageDepthCm = Math.round(averageDepth * hdr.depth.scale_m * 100) // Convert to cm
    console.log(`🎯 Center square (${squareSize}x${squareSize}) average depth: ${averageDepth}mm (${averageDepthCm}cm)`)
    console.log(`📊 Center depth range: ${Math.min(...centerDepths)}mm - ${Math.max(...centerDepths)}mm`)
    
    // Highlight center square in red
    for (let y = centerY - halfSquare; y < centerY + halfSquare; y++) {
      for (let x = centerX - halfSquare; x < centerX + halfSquare; x++) {
        if (x >= 0 && x < hdr.depth.width && y >= 0 && y < hdr.depth.height) {
          const idx = (y * hdr.depth.width + x) * 4
          // Set red border (keep some original depth info)
          depthImg.data[idx] = 255     // R = red
          depthImg.data[idx + 1] = 0   // G = 0
          depthImg.data[idx + 2] = 0   // B = 0
          depthImg.data[idx + 3] = 255 // A = opaque
        }
      }
    }

    // Put image data directly to display canvas (exactly like server)
    const ctx = displayCanvas.getContext('2d')
    if (ctx) {
      // Set canvas size to match image dimensions (exactly like server)
      displayCanvas.width = hdr.depth.width
      displayCanvas.height = hdr.depth.height
      displayCanvas.style.width = `${hdr.depth.width}px`
      displayCanvas.style.height = `${hdr.depth.height}px`

      // Put image data directly (exactly like server)
      ctx.putImageData(depthImg, 0, 0)
    }
    console.log('renderDepth completed - canvas size:', hdr.depth.width, 'x', hdr.depth.height)
  }

  const renderDepthRaw = (buf: ArrayBuffer, width: number, height: number) => {
    console.log('Rendering raw depth data as fallback')
    const displayCanvas = canvasRef.current
    const container = containerRef.current
    
    if (!displayCanvas || !container) return

    const u16 = new Uint16Array(buf)
    const img = new ImageData(width, height)
    const data = img.data
    
    // Dynamic depth range detection for better visualization
    const validDepths = u16.filter(d => d > 0 && d < 65535)
    let minDepth = 0
    let maxDepth = 0
    
    console.log('Raw depth data - valid pixels:', validDepths.length, 'out of', u16.length)
    
    if (validDepths.length > 0) {
      minDepth = validDepths[0]
      maxDepth = validDepths[0]
      for (let i = 1; i < validDepths.length; i++) {
        const depth = validDepths[i]
        if (depth < minDepth) minDepth = depth
        if (depth > maxDepth) maxDepth = depth
      }
      
      // Ensure we have a reasonable range
      if (maxDepth - minDepth < 100) {
        const mid = (minDepth + maxDepth) / 2
        minDepth = Math.max(0, mid - 1000)
        maxDepth = mid + 1000
      }
    } else {
      // Fallback values if no valid depth data
      minDepth = 0
      maxDepth = 5000
    }
    
    if (maxDepth <= minDepth) {
      maxDepth = minDepth + 2000
    }
    
    const depthRange = maxDepth - minDepth
    console.log('Depth range for visualization:', minDepth, 'to', maxDepth, 'range:', depthRange)
    
    let j = 0
    for (let i = 0; i < u16.length; i++) {
      const v16 = u16[i]
      
      if (v16 === 0 || v16 >= 65535) {
        // Invalid depth - show as black
        data[j++] = 0
        data[j++] = 0
        data[j++] = 0
        data[j++] = 255
      } else if (depthRange > 0) {
        // Map depth to color with better contrast
        const normalized = Math.max(0, Math.min(1, (v16 - minDepth) / depthRange))
        const intensity = Math.floor(normalized * 255)
        
        // Use a color map: blue (close) -> green -> yellow -> red (far)
        if (normalized < 0.25) {
          // Blue to cyan
          data[j++] = 0
          data[j++] = intensity
          data[j++] = 255
        } else if (normalized < 0.5) {
          // Cyan to green
          data[j++] = 0
          data[j++] = 255
          data[j++] = 255 - intensity
        } else if (normalized < 0.75) {
          // Green to yellow
          data[j++] = intensity
          data[j++] = 255
          data[j++] = 0
        } else {
          // Yellow to red
          data[j++] = 255
          data[j++] = 255 - intensity
          data[j++] = 0
        }
        data[j++] = 255
      } else {
        // No valid range - show as gray
        data[j++] = 128
        data[j++] = 128
        data[j++] = 128
        data[j++] = 255
      }
    }
    
    // Calculate display size
    const containerWidth = container.clientWidth || 400
    const displayWidthCss = Math.max(containerWidth, 200)
    const displayHeightCss = Math.round((height / width) * displayWidthCss)

    const ctx = displayCanvas.getContext('2d')
    if (ctx) {
      // Set canvas size
      displayCanvas.width = displayWidthCss
      displayCanvas.height = displayHeightCss
      displayCanvas.style.width = `${displayWidthCss}px`
      displayCanvas.style.height = `${displayHeightCss}px`

      // Create temporary canvas for scaling
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = width
      tempCanvas.height = height
      const tempCtx = tempCanvas.getContext('2d')
      if (tempCtx) {
        tempCtx.putImageData(img, 0, 0)
        
        // Draw scaled to display canvas
        ctx.imageSmoothingEnabled = false
        ctx.clearRect(0, 0, displayWidthCss, displayHeightCss)
        ctx.drawImage(tempCanvas, 0, 0, displayWidthCss, displayHeightCss)
      }
    }
    console.log('renderDepthRaw completed - canvas size:', displayWidthCss, 'x', displayHeightCss)
  }

  const renderLoop = () => {
    // The render loop is now mainly for cleanup and monitoring
    // Actual rendering happens immediately when data arrives
    if (latestHeaderRef.current && rgbBufferRef.current && depthBufferRef.current) {
      console.log('Render loop - data available, but rendering happens on data arrival')
    } else {
      console.log('Render loop - waiting for data:', { 
        hasHeader: !!latestHeaderRef.current, 
        hasRgb: !!rgbBufferRef.current, 
        hasDepth: !!depthBufferRef.current 
      })
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
            
            // Reset message counter for new frame
            messageCounterRef.current = 0
            console.log('New frame header received, reset message counter')
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
            console.log('Complete frame received - RGB and depth data ready')
            console.log('Buffer states:', {
              rgb: !!rgbBufferRef.current,
              depth: !!depthBufferRef.current,
              rgbSize: rgbBufferRef.current?.byteLength,
              depthSize: depthBufferRef.current?.byteLength
            })
            
            // Render based on current view (like the server viewer)
            console.log('Rendering complete frame immediately, current view:', currentView)
            if (currentView === 'color') {
              renderRgb()
            } else {
              renderDepth()
            }
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
    // start render loop after a short delay to ensure containers are mounted
    const startRenderLoop = () => {
      rafRef.current = window.requestAnimationFrame(renderLoop)
    }
    
    // Start immediately and also after a short delay to ensure DOM is ready
    startRenderLoop()
    const timeoutId = setTimeout(startRenderLoop, 100)
    
    return () => {
      try { websocketRef.current?.close() } catch {}
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current)
      clearTimeout(timeoutId)
    }
  }, [])

  // Re-render when view changes
  useEffect(() => {
    if (latestHeaderRef.current && rgbBufferRef.current && depthBufferRef.current) {
      console.log('View changed to:', currentView, '- re-rendering')
      if (currentView === 'color') {
        renderRgb()
      } else {
        renderDepth()
      }
    }
  }, [currentView])

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

          <div className="flex gap-2 items-center">
            <label className="text-sm text-muted-foreground">View:</label>
            <Button 
              onClick={() => setCurrentView('color')}
              variant={currentView === 'color' ? 'default' : 'outline'}
              size="sm"
            >
              Color
            </Button>
            <Button 
              onClick={() => setCurrentView('depth')}
              variant={currentView === 'depth' ? 'default' : 'outline'}
              size="sm"
            >
              Depth
            </Button>
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
                  {rgbBufferRef.current && depthBufferRef.current && (
                    <span className="text-green-500 ml-2">• Data Ready</span>
                  )}
                </span>
              ) : (
                <span>Waiting for header…</span>
              )}
            </div>
            <div className="text-sm">{fps ? `${fps.toFixed(1)} fps` : ''}</div>
          </div>

          {/* Camera View - Single Canvas like server viewer */}
          <Card className="border">
            <CardHeader>
              <CardTitle className="text-sm">
                {currentView === 'color' ? 'RGB Camera' : 'Depth Data'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div ref={containerRef} className="w-full overflow-auto">
                <canvas
                  ref={canvasRef}
                  className="border rounded-md bg-black w-full"
                  style={{ display: 'block', imageRendering: 'pixelated' as any, minHeight: '300px' }}
                />
              </div>
              {currentView === 'depth' && (
                <div className="mt-2 text-xs text-muted-foreground">
                  Depth Legend: <span className="text-white font-bold">White</span> (close) → <span className="text-gray-400">Gray</span> → <span className="text-gray-600">Dark Gray</span> → <span className="text-black font-bold">Black</span> (far)
                </div>
              )}
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}

export default DepthViewer


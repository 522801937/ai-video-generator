import { useEffect, useRef } from 'react'
import { fadeIn, slideIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function ImageScene({ slide, width = 1920, height = 1080 }: Props) {
  const imgRef = useRef<HTMLDivElement>(null)
  const captionRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()
    if (imgRef.current) tl.add('img', () => fadeIn(imgRef.current!, 1000), 0)
    if (captionRef.current && slide.text) {
      tl.add('caption', () => slideIn(captionRef.current!, 'bottom', 600), 1.0)
    }
    tl.play()
    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(180deg, #0d1117 0%, #010409 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      position: 'relative',
    }}>
      <div ref={imgRef} style={{
        width: '80%', height: '60%',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        opacity: 0,
      }}>
        <span style={{ color: '#8b949e', fontSize: 24 }}>
          🖼️ {slide.keywords?.[0] || '图片区域'}
        </span>
      </div>
      {slide.text && (
        <p ref={captionRef} style={{
          fontSize: 28, color: 'rgba(255,255,255,0.7)',
          marginTop: 32, textAlign: 'center', maxWidth: '70%',
          opacity: 0,
        }}>
          {slide.text}
        </p>
      )}
    </div>
  )
}

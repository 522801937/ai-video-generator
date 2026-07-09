import { useEffect, useRef } from 'react'
import { fadeIn, scaleIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function OutroScene({ slide, width = 1920, height = 1080 }: Props) {
  const textRef = useRef<HTMLHeadingElement>(null)
  const lineRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()
    if (lineRef.current) tl.add('line', () => fadeIn(lineRef.current!, 600), 0)
    if (textRef.current) tl.add('text', () => scaleIn(textRef.current!, 1000), 0.5)
    tl.play()
    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(135deg, #0a0a2e 0%, #0d1b2a 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    }}>
      <div ref={lineRef} style={{
        width: 120, height: 3,
        background: 'linear-gradient(90deg, transparent, #00c8ff, transparent)',
        marginBottom: 32, opacity: 0,
      }} />
      <h1 ref={textRef} style={{
        fontSize: 56, fontWeight: 700, color: '#ffffff',
        textAlign: 'center', opacity: 0,
      }}>
        {slide.title || slide.text || '感谢观看'}
      </h1>
    </div>
  )
}

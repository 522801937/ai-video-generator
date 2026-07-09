import { useEffect, useRef } from 'react'
import { fadeIn, scaleIn, slideIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function TitleScene({ slide, width = 1920, height = 1080 }: Props) {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const subtitleRef = useRef<HTMLParagraphElement>(null)
  const decorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()

    // 0.0s: 装饰线淡入
    if (decorRef.current) {
      tl.add('decor', () => fadeIn(decorRef.current!, 600), 0)
    }

    // 0.3s: 标题弹性放大
    if (titleRef.current) {
      tl.add('title', () => scaleIn(titleRef.current!, 800), 0.3)
    }

    // 1.2s: 副标题滑入
    if (subtitleRef.current && slide.text) {
      tl.add('subtitle', () => slideIn(subtitleRef.current!, 'bottom', 600), 1.2)
    }

    tl.play()

    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b2a 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* 背景浮动装饰圆 */}
      <div style={{
        position: 'absolute', top: '15%', right: '10%',
        width: 300, height: 300, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0,200,255,0.08), transparent)',
      }} />
      <div style={{
        position: 'absolute', bottom: '20%', left: '8%',
        width: 200, height: 200, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(120,80,255,0.06), transparent)',
      }} />

      {/* 装饰线 */}
      <div ref={decorRef} style={{
        width: 160, height: 3,
        background: 'linear-gradient(90deg, transparent, #00c8ff, transparent)',
        marginBottom: 40, opacity: 0,
      }} />

      {/* 标题 */}
      <h1 ref={titleRef} style={{
        fontSize: 72, fontWeight: 700, color: '#ffffff',
        textAlign: 'center', maxWidth: '80%',
        textShadow: '0 2px 20px rgba(0,200,255,0.3)',
        opacity: 0,
      }}>
        {slide.title || slide.text}
      </h1>

      {/* 副标题 */}
      {slide.text && slide.title && (
        <p ref={subtitleRef} style={{
          fontSize: 28, color: 'rgba(255,255,255,0.7)',
          marginTop: 24, textAlign: 'center', maxWidth: '60%',
          opacity: 0,
        }}>
          {slide.text}
        </p>
      )}
    </div>
  )
}

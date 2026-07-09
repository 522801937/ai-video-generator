import { useEffect, useRef } from 'react'
import { slideIn, staggerList } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function BulletsScene({ slide, width = 1920, height = 1080 }: Props) {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const itemsRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()

    if (titleRef.current && slide.title) {
      tl.add('title', () => slideIn(titleRef.current!, 'left', 600), 0)
    }

    if (itemsRef.current) {
      const items = itemsRef.current.querySelectorAll('li')
      tl.add('items', () => staggerList(items, 500, 250), 0.5)
    }

    tl.play()
    return () => tl.stop()
  }, [slide])

  // Split text by newlines or semicolons into list items
  const items = slide.text
    .split(/[\n；;]/)
    .map(s => s.trim())
    .filter(Boolean)

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(160deg, #0d1117 0%, #161b22 100%)',
      display: 'flex', flexDirection: 'column', justifyContent: 'center',
      padding: '100px 140px',
    }}>
      {slide.title && (
        <h2 ref={titleRef} style={{
          fontSize: 48, fontWeight: 700, color: '#00c8ff',
          marginBottom: 40, opacity: 0,
        }}>
          {slide.title}
        </h2>
      )}
      <ul ref={itemsRef} style={{ listStyle: 'none', padding: 0 }}>
        {items.map((item, i) => (
          <li key={i} style={{
            fontSize: 32, color: '#e6edf3', marginBottom: 20,
            paddingLeft: 40, position: 'relative', opacity: 0,
          }}>
            <span style={{
              position: 'absolute', left: 0, color: '#00c8ff',
              fontSize: 24, top: 4,
            }}>
              ●
            </span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

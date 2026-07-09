import TitleScene from '../scenes/TitleScene'
import BulletsScene from '../scenes/BulletsScene'
import ImageScene from '../scenes/ImageScene'
import OutroScene from '../scenes/OutroScene'
import type { SlideItem } from '../types'

interface Props {
  slides: SlideItem[]
  title: string
  currentSlide: number
}

export default function PreviewPanel({ slides, title, currentSlide }: Props) {
  if (slides.length === 0) {
    return (
      <div style={{ textAlign: 'center', color: '#8b949e' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🎬</div>
        <p>在左侧输入文案并点击"解析"</p>
        <p>即可在此预览视频动画效果</p>
      </div>
    )
  }

  const slide = slides[currentSlide]
  if (!slide) return null

  // 预览缩放: 1920x1080 → 容器内自适应
  const scale = 0.45

  const sceneComponent = (() => {
    switch (slide.type) {
      case 'title': return <TitleScene slide={slide} />
      case 'bullets': return <BulletsScene slide={slide} />
      case 'image': return <ImageScene slide={slide} />
      case 'outro': return <OutroScene slide={slide} />
      default: return <div style={{ color: '#8b949e' }}>未知场景类型: {slide.type}</div>
    }
  })()

  return (
    <div style={{
      transform: `scale(${scale})`,
      transformOrigin: 'center center',
      borderRadius: 8,
      overflow: 'hidden',
      boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
    }}>
      {sceneComponent}
    </div>
  )
}

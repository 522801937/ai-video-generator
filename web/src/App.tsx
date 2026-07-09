import { useState } from 'react'
import type { SlideItem } from './types'
import Editor from './components/Editor'
import PreviewPanel from './components/PreviewPanel'
import ExportPanel from './components/ExportPanel'
import './styles/global.css'

export default function App() {
  const [slides, setSlides] = useState<SlideItem[]>([])
  const [title, setTitle] = useState('')
  const [currentSlide, setCurrentSlide] = useState(0)

  const handleSlidesChange = (newSlides: SlideItem[], newTitle: string) => {
    setSlides(newSlides)
    setTitle(newTitle)
    setCurrentSlide(0)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎬 AI 科普视频生成器</h1>
      </header>
      <main className="app-main">
        <div className="panel panel-left">
          <Editor
            onSlidesChange={handleSlidesChange}
            onSlideSelect={setCurrentSlide}
            currentSlide={currentSlide}
          />
        </div>
        <div className="panel panel-center">
          <PreviewPanel slides={slides} title={title} currentSlide={currentSlide} />
        </div>
        <div className="panel panel-right">
          <ExportPanel slides={slides} title={title} />
        </div>
      </main>
    </div>
  )
}

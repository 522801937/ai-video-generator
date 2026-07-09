export interface SlideItem {
  type: 'title' | 'bullets' | 'image' | 'outro' | 'concept' | 'compare' | 'flow' | 'chart' | 'quote' | 'timeline'
  text: string
  title: string
  keywords: string[]
  config: Record<string, any>
}

export interface RenderStatus {
  task_id: string
  status: 'queued' | 'generating_audio' | 'rendering_frames' | 'compositing' | 'done' | 'error'
  progress: number
  output_path?: string
  error?: string
}

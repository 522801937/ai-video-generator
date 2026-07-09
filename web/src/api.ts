import type { SlideItem, RenderStatus } from './types'

const BASE = '/api'

export async function healthCheck(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`)
    return r.ok
  } catch {
    return false
  }
}

export async function parseScript(content: string, title: string): Promise<{ title: string; slides: SlideItem[] }> {
  const r = await fetch(`${BASE}/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, title }),
  })
  if (!r.ok) throw new Error(`Parse failed: ${r.statusText}`)
  return r.json()
}

export async function startRender(
  slides: SlideItem[],
  title: string,
  voice: string = 'xiaoxiao',
  options?: { subtitles?: boolean; voiceover?: boolean; bgTheme?: string }
): Promise<{ task_id: string; status: string }> {
  const r = await fetch(`${BASE}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slides, title, voice, ...options }),
  })
  if (!r.ok) throw new Error(`Render failed: ${r.statusText}`)
  return r.json()
}

export async function getRenderStatus(taskId: string): Promise<RenderStatus> {
  const r = await fetch(`${BASE}/render/${taskId}/status`)
  if (!r.ok) throw new Error(`Status check failed: ${r.statusText}`)
  return r.json()
}

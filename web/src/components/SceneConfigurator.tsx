import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem | null
  onChange: (updated: SlideItem) => void
}

const SCENE_LABELS: Record<string, string> = {
  title: '📌 标题页',
  bullets: '📝 要点列举',
  image: '🖼️ 图片展示',
  outro: '👋 片尾',
}

export default function SceneConfigurator({ slide, onChange }: Props) {
  if (!slide) {
    return <div style={{ color: '#8b949e' }}>选择一个场景来编辑参数</div>
  }

  const sceneTypes = ['title', 'bullets', 'image', 'outro']

  return (
    <div className="scene-config">
      <h4>⚙️ 场景配置</h4>
      <div className="field">
        <label>场景类型</label>
        <select
          value={slide.type}
          onChange={e => onChange({ ...slide, type: e.target.value as any })}
          className="select"
        >
          {sceneTypes.map(t => (
            <option key={t} value={t}>{SCENE_LABELS[t] || t}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>文本内容</label>
        <textarea
          value={slide.text}
          onChange={e => onChange({ ...slide, text: e.target.value })}
          rows={4}
          className="textarea"
        />
      </div>
    </div>
  )
}

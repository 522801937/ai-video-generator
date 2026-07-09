interface Props {
  onSlideSelect: (index: number) => void
  currentSlide: number
}

export default function Timeline({ onSlideSelect, currentSlide }: Props) {
  return (
    <div className="timeline" style={{ marginTop: 16 }}>
      <h4>📋 场景列表</h4>
      <p style={{ color: '#8b949e', fontSize: 12, marginTop: 4 }}>
        选择场景查看预览，拖拽排序 (即将支持)
      </p>
    </div>
  )
}

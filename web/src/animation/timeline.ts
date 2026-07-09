/**
 * 场景时间线引擎 — 管理一个场景内多个动画的编排
 */
import anime, { AnimeInstance } from 'animejs'

export interface AnimationStep {
  name: string
  fn: () => AnimeInstance
  at: number  // 开始时间(秒)
}

export class SceneTimeline {
  private steps: AnimationStep[] = []
  private instances: AnimeInstance[] = []

  add(name: string, fn: () => AnimeInstance, at: number) {
    this.steps.push({ name, fn, at })
    return this
  }

  play(onComplete?: () => void) {
    this.stop()
    this.instances = []

    const maxEnd = this.steps.reduce((max, step) => {
      const inst = step.fn()
      this.instances.push(inst)
      const end = step.at * 1000 + (inst.duration || 0) + (inst.delay || 0)
      return Math.max(max, end)
    }, 0)

    if (onComplete) {
      setTimeout(onComplete, maxEnd)
    }
    return this
  }

  stop() {
    this.instances.forEach(inst => {
      try { inst.pause() } catch {}
    })
    this.instances = []
  }

  get totalDuration(): number {
    return this.steps.reduce((max, step) => {
      return Math.max(max, step.at + 1.5)  // 保守估计每个动画约1.5秒
    }, 0)
  }
}

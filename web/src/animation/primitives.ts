/**
 * 动画原语 — 基于 anime.js 封装的常用动画效果
 * 所有函数操作 DOM 元素，返回 anime.js 实例
 */
import anime from 'animejs'

export type AnimationTarget = string | HTMLElement | NodeList

export function fadeIn(target: AnimationTarget, duration: number = 800, delay: number = 0) {
  return anime({ targets: target, opacity: [0, 1], duration, delay, easing: 'easeOutCubic' })
}

export function fadeOut(target: AnimationTarget, duration: number = 600, delay: number = 0) {
  return anime({ targets: target, opacity: [1, 0], duration, delay, easing: 'easeInCubic' })
}

export function slideIn(target: AnimationTarget, from: 'left' | 'right' | 'bottom' = 'bottom', duration: number = 700, delay: number = 0) {
  const translateMap = { left: [-60, 0], right: [60, 0], bottom: [40, 0] }
  const [fromVal, toVal] = translateMap[from]
  return anime({
    targets: target,
    translateY: from === 'bottom' ? [fromVal, toVal] : undefined,
    translateX: from !== 'bottom' ? [fromVal, toVal] : undefined,
    opacity: [0, 1],
    duration,
    delay,
    easing: 'easeOutCubic',
  })
}

export function scaleIn(target: AnimationTarget, duration: number = 800, delay: number = 0) {
  return anime({
    targets: target,
    scale: [0.3, 1],
    opacity: [0, 1],
    duration,
    delay,
    easing: 'easeOutElastic(1, .6)',
  })
}

export function typewriter(target: HTMLElement, text: string, duration: number = 2000, delay: number = 0) {
  const chars = text.length
  let i = 0
  target.textContent = ''
  return anime({
    targets: { count: 0 },
    count: [0, chars],
    duration,
    delay,
    easing: 'linear',
    update() {
      const current = Math.floor((this as any).animations[0].currentValue)
      while (i < current) { target.textContent += text[i]; i++ }
    },
  })
}

export function staggerList(targets: AnimationTarget, duration: number = 500, staggerDelay: number = 200, delay: number = 0) {
  return anime({
    targets: targets as any,
    translateY: [30, 0],
    opacity: [0, 1],
    duration,
    delay: anime.stagger(staggerDelay, { start: delay }),
    easing: 'easeOutCubic',
  })
}

export function counterUp(target: HTMLElement, from: number, to: number, duration: number = 1500, delay: number = 0) {
  return anime({
    targets: { val: from },
    val: [from, to],
    duration,
    delay,
    easing: 'easeOutCubic',
    round: 1,
    update() {
      target.textContent = String(Math.round((this as any).animations[0].currentValue))
    },
  })
}

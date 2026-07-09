declare module 'animejs' {
  interface AnimeParams {
    targets?: any
    opacity?: number | number[]
    translateX?: number | number[]
    translateY?: number | number[]
    scale?: number | number[]
    duration?: number
    delay?: number | ((el: any, i: number, total: number) => number)
    easing?: string
    round?: number | boolean
    update?: (anim?: any) => void
    complete?: (anim?: any) => void
    begin?: (anim?: any) => void
    loop?: boolean | number
    direction?: 'normal' | 'reverse' | 'alternate'
    endDelay?: number
    [key: string]: any
  }

  interface AnimeInstance {
    duration: number
    delay: number
    paused: boolean
    finished: Promise<void>
    play(): void
    pause(): void
    restart(): void
    reverse(): void
    seek(time: number): void
    finished: Promise<void>
  }

  interface AnimeStatic {
    (params: AnimeParams): AnimeInstance
    stagger(val: number | number[], options?: any): (el: any, i: number, total: number) => number
    random(min: number, max: number): number
    timeline(params?: any): any
  }

  export { AnimeInstance, AnimeParams }
  const anime: AnimeStatic
  export default anime
}

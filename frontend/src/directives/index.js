import { canHover, gsap, prefersReducedMotion, ScrollTrigger } from '@/composables/motion'

/**
 * v-reveal[:variant]="delayMs" — fades/slides the element in the first
 * time it enters the viewport. Variants: up (default), left, right, zoom,
 * clip. Styles live in styles/base.css ([data-reveal]).
 */
let revealObserver = null
function getRevealObserver() {
  if (!revealObserver) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed')
            revealObserver.unobserve(entry.target)
          }
        }
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.12 },
    )
  }
  return revealObserver
}

const reveal = {
  mounted(el, binding) {
    el.dataset.reveal = binding.arg || 'up'
    if (binding.value) el.style.setProperty('--reveal-delay', `${binding.value}ms`)
    if (prefersReducedMotion()) {
      el.classList.add('is-revealed')
      return
    }
    getRevealObserver().observe(el)
  },
  unmounted(el) {
    revealObserver?.unobserve(el)
  },
}

/** v-parallax="0.2" — moves the element against the scroll by `speed`. */
const parallax = {
  mounted(el, binding) {
    if (prefersReducedMotion()) return
    const speed = Number(binding.value ?? 0.2)
    el._parallax = gsap.fromTo(
      el,
      { yPercent: -speed * 50 },
      {
        yPercent: speed * 50,
        ease: 'none',
        scrollTrigger: { trigger: el.parentElement || el, start: 'top bottom', end: 'bottom top', scrub: true },
      },
    )
  },
  unmounted(el) {
    el._parallax?.scrollTrigger?.kill()
    el._parallax?.kill()
  },
}

/** v-magnetic — the element leans towards the pointer while hovered. */
const magnetic = {
  mounted(el, binding) {
    if (!canHover() || prefersReducedMotion()) return
    const strength = Number(binding.value ?? 0.3)
    const move = (e) => {
      const r = el.getBoundingClientRect()
      gsap.to(el, {
        x: (e.clientX - r.left - r.width / 2) * strength,
        y: (e.clientY - r.top - r.height / 2) * strength,
        duration: 0.4,
        ease: 'power3.out',
      })
    }
    const leave = () => gsap.to(el, { x: 0, y: 0, duration: 0.7, ease: 'elastic.out(1, 0.4)' })
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', leave)
    el._magnetic = { move, leave }
  },
  unmounted(el) {
    if (!el._magnetic) return
    el.removeEventListener('pointermove', el._magnetic.move)
    el.removeEventListener('pointerleave', el._magnetic.leave)
  },
}

/** v-tilt — 3D tilt + a light spot following the pointer (--mx/--my). */
const tilt = {
  mounted(el, binding) {
    if (!canHover() || prefersReducedMotion()) return
    const max = Number(binding.value ?? 8)
    const move = (e) => {
      const r = el.getBoundingClientRect()
      const px = (e.clientX - r.left) / r.width
      const py = (e.clientY - r.top) / r.height
      el.style.setProperty('--mx', `${px * 100}%`)
      el.style.setProperty('--my', `${py * 100}%`)
      gsap.to(el, {
        rotateY: (px - 0.5) * max,
        rotateX: (0.5 - py) * max,
        transformPerspective: 900,
        duration: 0.5,
        ease: 'power2.out',
      })
    }
    const leave = () => gsap.to(el, { rotateX: 0, rotateY: 0, duration: 0.8, ease: 'power3.out' })
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', leave)
    el._tilt = { move, leave }
  },
  unmounted(el) {
    if (!el._tilt) return
    el.removeEventListener('pointermove', el._tilt.move)
    el.removeEventListener('pointerleave', el._tilt.leave)
  },
}

/** v-count-up — animates the element's number from 0 when it scrolls into view. */
const countUp = {
  mounted(el, binding) {
    const target = Number(binding.value) || 0
    if (prefersReducedMotion()) {
      el.textContent = target
      return
    }
    const counter = { n: 0 }
    el.textContent = '0'
    el._count = gsap.to(counter, {
      n: target,
      duration: 1.8,
      ease: 'power3.out',
      onUpdate: () => (el.textContent = Math.round(counter.n)),
      scrollTrigger: { trigger: el, start: 'top 90%', once: true },
    })
  },
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      el._count?.scrollTrigger?.kill()
      el._count?.kill()
      countUp.mounted(el, binding)
    }
  },
  unmounted(el) {
    el._count?.scrollTrigger?.kill()
    el._count?.kill()
  },
}

export default {
  install(app) {
    app.directive('reveal', reveal)
    app.directive('parallax', parallax)
    app.directive('magnetic', magnetic)
    app.directive('tilt', tilt)
    app.directive('count-up', countUp)
    // Images loading late change the page height — keep triggers accurate.
    window.addEventListener('load', () => ScrollTrigger.refresh())
  },
}

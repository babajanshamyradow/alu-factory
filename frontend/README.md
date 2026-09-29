# Alu Factory — public website

Vue 3 + Vite site for visitors: home (slider, banners), catalog, product page, contact form, about us.
UI languages: every `SystemLang` value — `src/i18n/locales/{en,ru,tr,de}.json` (add new strings to all four).

## Run

```bash
# 1. Public API (backend/src/sip, SIP_PORT = 9999 in backend/config.ini)
backend/venv/bin/sip

# 2. Site (Node 22, see .nvmrc) — http://localhost:5175
cd frontend && nvm use && npm install && npm run dev
```

The dev server proxies `/api/*` and `/media/*` to `http://localhost:9999`.
In production serve `dist/` and route those two prefixes to the sip app.

## API (all anonymous)

| Method | Path | |
|---|---|---|
| GET | `/api/company` | company info, logo, cover, active gallery |
| GET | `/api/slider` | active slides inside their show window |
| GET | `/api/banners` | active banners (+ linked product slug) |
| GET | `/api/categories` | active categories with product counts |
| GET | `/api/products?search=&category=<slug>&featured=1&page=&per-page=` | catalog page |
| GET | `/api/products/<slug>` | product with images and related products |
| POST | `/api/contact-messages` | contact form (lands in the console's Contact list) |

Animations: GSAP + ScrollTrigger, Lenis smooth scroll, Swiper; all respect `prefers-reduced-motion`.

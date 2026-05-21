#!/usr/bin/env node
// Stage backend/static/changelog.json into frontend/.changelog-fixture.json
// before `next build`. Required so the SSG fallback in
// app/(marketing)/changelog/page.tsx can read the source-of-truth
// changelog when the API isn't reachable at build time.
//
// Three execution contexts:
//   1. Local dev (`npm run build` from a checkout): `../backend/static/
//      changelog.json` is reachable; copy it.
//   2. CI build (.github/workflows/{staging,production}.yml): a pre-step
//      copies the fixture into `frontend/.changelog-fixture.json` BEFORE
//      `docker build`, so by the time the Docker builder runs this script
//      via npm's prebuild hook, the destination already exists and the
//      source is unreachable (../backend/ is outside the build context).
//      We detect that and no-op.
//   3. PR CI (frontend-pr.yml): no fixture staged (parity build only,
//      doesn't push). The fallback gracefully returns [] in that case.
//
// Previously lived as this same script under the Vite build; deleted in
// commit a4b3998 on the (incorrect) assumption ISR-fetch made it
// unnecessary. PR #350 review caught the gap.

import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FRONTEND_ROOT = join(__dirname, '..')
const SRC = join(FRONTEND_ROOT, '..', 'backend', 'static', 'changelog.json')
const DST = join(FRONTEND_ROOT, '.changelog-fixture.json')

if (existsSync(DST) && !existsSync(SRC)) {
  // Context 2: CI pre-staged the fixture; source isn't reachable from here.
  console.log(`  [sync-changelog-fixture] ${DST} already present (CI staged); skipping copy.`)
  process.exit(0)
}

if (!existsSync(SRC)) {
  // Context 3: no source, no pre-staged destination — page.tsx fallback
  // returns []. Warn so a misconfigured CI surface shows up clearly.
  console.warn(`  [sync-changelog-fixture] ${SRC} missing; build-time JSON-LD fallback will be empty.`)
  process.exit(0)
}

mkdirSync(dirname(DST), { recursive: true })
copyFileSync(SRC, DST)
console.log(`  [sync-changelog-fixture] ${SRC} -> ${DST}`)

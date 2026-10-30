// Walks the whole film without capturing a picture and lists where a visible arm passes what a human arm can do.
//   node tools/arm_audit.mjs [fromStorySeconds] [toStorySeconds] [framesPerSecond]      (needs the dev server on 5441)
// Same measure as the render's arm limit check in tools/film.mjs, but it finds every fault instead of stopping at the first.
import { chromium } from 'playwright'


const STORY_MINUS_OUTPUT = 5
const fromStory = Number(process.argv[2] ?? 18)
const toStory = Number(process.argv[3] ?? 269.2)
const framesPerSecond = Number(process.argv[4] ?? 6)

function virtualClock() {
  let now = 0
  window.filmMode = true
  let nextId = 1
  const callbacks = new Map()
  window.requestAnimationFrame = (callback) => {
    const id = nextId++
    callbacks.set(id, callback)
    return id
  }
  window.cancelAnimationFrame = (id) => callbacks.delete(id)
  performance.now = () => now
  window.advanceVirtualFrame = (milliseconds) => {
    now += milliseconds
    const due = [...callbacks.values()]
    callbacks.clear()
    due.forEach((callback) => callback(now))
  }
}

const browser = await chromium.launch({ headless: true, args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] })
const page = await browser.newPage({ viewport: { width: 320, height: 180 } })
await page.addInitScript(virtualClock)
await page.goto('http://localhost:5441/film.html', { timeout: 120000 })
await page.waitForSelector('canvas')
const advance = (milliseconds) => page.evaluate((amount) => window.advanceVirtualFrame(amount), milliseconds)
for (let attempt = 0; attempt < 600 && !(await page.evaluate(() => window.film?.ready)); attempt++) {
  await advance(33)
  await page.waitForTimeout(40)
}

const runs = []
const worst = new Map()
const openRuns = new Map()
const seen = new Set()
await page.evaluate((at) => window.film.start(at), fromStory - STORY_MINUS_OUTPUT - 1 / framesPerSecond)
for (let frame = 0; frame < (toStory - fromStory) * framesPerSecond; frame++) {
  await advance(1000 / framesPerSecond)
  const story = fromStory + frame / framesPerSecond
  const arms = await page.evaluate(() => window.measureArms())
  Object.keys(arms.largest).forEach((key) => seen.add(key.split(' ')[0]))
  const now = new Set(arms.faults.map((fault) => fault.key))
  for (const fault of arms.faults) {
    if (!openRuns.has(fault.key)) openRuns.set(fault.key, { key: fault.key, from: story, over: 0 })
    const run = openRuns.get(fault.key)
    run.to = story
    run.over = Math.max(run.over, fault.over)
    worst.set(fault.key, Math.max(worst.get(fault.key) ?? 0, fault.over))
  }
  for (const [key, run] of openRuns) {
    if (!now.has(key)) {
      runs.push(run)
      openRuns.delete(key)
    }
  }
}
runs.push(...openRuns.values())
await browser.close()
console.log('mannequins seen:', [...seen].join(', '))
const clock = (story) => {
  const output = Math.max(0, story - STORY_MINUS_OUTPUT)
  return Math.floor(output / 60) + ':' + (output % 60).toFixed(1).padStart(4, '0')
}
runs.sort((first, second) => first.from - second.from)
for (const run of runs) console.log(clock(run.from) + '-' + clock(run.to), run.key.padEnd(26), '+' + run.over.toFixed(0) + ' deg')
console.log(runs.length === 0 ? 'no arm past its limit' : runs.length + ' runs past a limit')

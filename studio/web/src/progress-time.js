// Pure timing rules for the progress screen, kept free of the DOM so node can test them.

// The server may report the approval moment as an ISO string or as epoch seconds.
export function toMs (value) {
  if (value === undefined || value === null || value === '') return 0
  if (typeof value === 'number') return Number.isFinite(value) && value > 0 ? (value < 1e11 ? value * 1000 : value) : 0
  const parsed = Date.parse(value)
  if (Number.isFinite(parsed)) return parsed
  const numeric = Number(value)
  return Number.isFinite(numeric) ? toMs(numeric) : 0
}

// When the publication was approved, or 0 when this browser cannot know it. The counter never
// starts from the first check or from page load: those are later than the real start.
export function approvedAtMs (publication, localStamp) {
  return toMs(publication && (publication.approved_at || publication.created)) || toMs(localStamp)
}

// Index of the stage that is working now. Approval is already behind us once a publication exists.
export function currentStage (state, seen, stageCount) {
  return state === 'published' ? stageCount - 1 : Math.max(1, seen)
}

// Seconds-counter text: empty while the start is unknown, so the screen stays honest.
export function elapsedMs (startMs, now) {
  return startMs > 0 ? Math.max(0, now - startMs) : -1
}

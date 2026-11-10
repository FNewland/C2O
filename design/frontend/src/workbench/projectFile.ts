/**
 * Project file Save / Load — the one implementation used by every Save and Load button
 * (workbench context bar, Home "Load from File", Export drawer).
 *
 * Save downloads the server's complete project document (GET /api/studies/{id}/export:
 * every table of the study, files on disk, the person's logbook entries) and adds the
 * breadcrumb. Load posts the file to POST /api/studies/import, which creates a NEW study
 * with fresh ids in one transaction (no link proposals, no duplicates), then opens it and
 * restores the breadcrumb with the ids the server returns. Old browser-built save files
 * (format 1) are converted by the server. Format: services/project_file.py.
 */
import i18n from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { showAlert } from '../components/ui/Dialog'

const API = '/api'

type Crumb = { id: string; name: string; type?: string | null }

interface ImportResult {
  id: string
  name: string
  counts: Record<string, number>
  warnings: string[]
  converted_from?: number | null
  ui?: { breadcrumb?: Crumb[] } | null
}

async function errorText(res: Response): Promise<string> {
  try {
    const body = await res.json()
    const d = body?.detail
    if (typeof d === 'string') return d
    if (d && typeof d.message === 'string') return d.message
  } catch { /* not JSON */ }
  return `HTTP ${res.status}`
}

function fileNameFrom(disposition: string | null): string | null {
  const m = disposition?.match(/filename="?([^";]+)"?/)
  return m ? m[1] : null
}

/** Download the complete project file of a study. Throws on failure. */
export async function saveProjectFile(studyId: string): Promise<void> {
  const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/export`)
  if (!res.ok) throw new Error(await errorText(res))
  const doc = await res.json()
  const { breadcrumb, currentLevel, focusElementId } = useUIStore.getState()
  doc.ui = { breadcrumb, currentLevel, focusElementId }
  const name = fileNameFrom(res.headers.get('content-disposition'))
    ?? `spacecdf_${new Date().toISOString().slice(0, 10)}.spacecdf.json`
  const blob = new Blob([JSON.stringify(doc)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

/** Import a project file's text as a new study and open it. Returns the new study id. */
export async function importProjectText(text: string): Promise<string | null> {
  try { JSON.parse(text) } catch {
    void showAlert(i18n.t('This file is not a SpaceCDF project file.'))
    return null
  }
  const res = await fetch(`${API}/studies/import`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: text,
  })
  if (!res.ok) {
    void showAlert(i18n.t('Load failed: {{message}}', { message: await errorText(res) }))
    return null
  }
  const result = (await res.json()) as ImportResult
  const ui = useUIStore.getState()
  ui.setStudyId(result.id)
  ui.drillUp(-1)
  for (const crumb of result.ui?.breadcrumb ?? []) {
    if (crumb?.id) useUIStore.getState().drillInto(crumb.id, crumb.name, crumb.type)
  }
  if (result.converted_from === 1) {
    void showAlert(i18n.t('This file was saved by an older version of SpaceCDF. It was opened with what it holds: elements, interfaces, requirements, allocations, risks and the Pugh matrix.'))
  } else if (result.warnings?.length) {
    void showAlert(i18n.t('The study was loaded with warnings: {{warnings}}', { warnings: result.warnings.join('; ') }))
  }
  return result.id
}

/** Ask for a project file (.json), import it as a new study and open it. */
export function loadProjectFile(onLoaded?: (studyId: string) => void): void {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,application/json'
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return
    try {
      const id = await importProjectText(await file.text())
      if (id && onLoaded) onLoaded(id)
    } catch (err) {
      void showAlert(i18n.t('Load failed: {{message}}', { message: (err as Error).message }))
    }
  }
  input.click()
}

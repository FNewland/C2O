import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'  // initialise i18next before the first render
import './theme/useTheme'  // sets <html data-theme> (light by default)
import App from './App'
import { installSeatFetch } from './seats/api'
import './index.css'
import './components/ui/primitives.css'  // after index.css: variants override the base
import './styles/shell.css'
import './logbook/logbook.css'
import './where/where.css'
import './seats/seats.css'
import './styles/utilities.css'          // last: utilities win over component defaults

// Seats (WP9): identity + active-seat headers on every /api request, and the
// "owned by another seat — send for review" flow (REDESIGN_DECISIONS.md ruling 5).
installSeatFetch()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

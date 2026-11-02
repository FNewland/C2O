import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'  // initialise i18next before the first render
import './theme/useTheme'  // sets <html data-theme> (light by default)
import App from './App'
import './index.css'
import './components/ui/primitives.css'  // after index.css: variants override the base
import './styles/shell.css'
import './styles/utilities.css'          // last: utilities win over component defaults

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'  // initialise i18next before the first render
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

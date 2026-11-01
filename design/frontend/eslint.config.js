import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
  // C2O design system guard rails (docs/ui/C2O_UI_BRIEF.md §3, R3 §5.1.6):
  // font sizes come from the type scale in src/theme/tokens.ts, never literals.
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: ['src/theme/**'],
    rules: {
      'no-restricted-syntax': ['error',
        {
          selector: "Property[key.name='fontSize'] Literal[value!='inherit']",
          message: 'Use a type-scale token (fs.label | fs.body | fs.value | fs.title from src/theme/tokens) instead of a fontSize literal.',
        },
        {
          selector: "Property[key.name='fontSize'] TemplateLiteral",
          message: 'Use a type-scale token (fs.*) instead of a computed fontSize.',
        },
        {
          selector: "JSXAttribute[name.name='fontSize'] Literal",
          message: 'Use a type-scale token (fs.*) instead of a fontSize literal.',
        },
      ],
    },
  },
])

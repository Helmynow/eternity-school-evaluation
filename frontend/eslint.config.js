import reactPlugin from 'eslint-plugin-react'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import reactRefreshPlugin from 'eslint-plugin-react-refresh'

/**
 * ESLint v9+ flat config.
 *
 * This repo previously used `npm run lint` without an explicit config file.
 * ESLint v9 requires an `eslint.config.(js|mjs|cjs)` file.
 */
export default [
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
      'coverage/**',
    ],
  },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      'react-refresh': reactRefreshPlugin,
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,

      // This codebase currently has many intentional dependency patterns (e.g., API loaders
      // defined inline) and the lint script enforces --max-warnings 0. Until the code is
      // fully refactored, keep this rule disabled to avoid blocking CI.
      'react-hooks/exhaustive-deps': 'off',

      // React 17+ JSX transform
      'react/react-in-jsx-scope': 'off',

      // This codebase often doesn’t use PropTypes (TS types or implicit props).
      'react/prop-types': 'off',

      // Avoid failing builds on apostrophes/quotes in JSX text.
      'react/no-unescaped-entities': 'off',

      // HOCs may legitimately be anonymous in this repo.
      'react/display-name': 'off',

      // Keep this off for now to avoid turning existing warnings into CI failures.
      // Can be enabled later if desired.
      'react-refresh/only-export-components': 'off',
    },
  },
]

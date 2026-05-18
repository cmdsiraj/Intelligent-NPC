/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface:  '#111111',
        card:     '#1a1a1a',
        border:   '#2a2a2a',
        muted:    '#666666',
        positive: '#22c55e',
        negative: '#ef4444',
        accent:   '#6366f1',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

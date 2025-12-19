/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                'bg-app': 'var(--bg-app)',
                'bg-sidebar': 'var(--bg-sidebar)',
                'bg-surface': 'var(--bg-surface)',
                'border-color': 'var(--border-color)',
                'text-primary': 'var(--text-primary)',
                'text-secondary': 'var(--text-secondary)',
                'accent-blue': '#3b82f6',
                'accent-violet': '#8b5cf6',
            }
        },
    },
    plugins: [],
}

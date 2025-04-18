/**
 * Theme management for dark/light mode
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    
    // Check for saved theme preference or use the system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply initial theme
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        showActiveThemeIcon('dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        showActiveThemeIcon('light');
    }
    
    // Toggle theme when button is clicked
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            // Save the preference
            localStorage.setItem('theme', newTheme);
            
            // Apply the theme
            document.documentElement.setAttribute('data-theme', newTheme);
            
            // Update the visible icon
            showActiveThemeIcon(newTheme);
        });
    }
    
    // Function to show the correct icon
    function showActiveThemeIcon(theme) {
        if (!sunIcon || !moonIcon) return;
        
        if (theme === 'dark') {
            moonIcon.classList.add('hidden');
            sunIcon.classList.remove('hidden');
        } else {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
    }
}); 
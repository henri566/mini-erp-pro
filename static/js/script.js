document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    // Récupérer le thème enregistré ou utiliser 'dark' par défaut
    const savedTheme = localStorage.getItem('theme') || 'dark';
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeUI(savedTheme);

    // Écouter le clic sur le bouton de basculement
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeUI(newTheme);
    });

    function updateThemeUI(theme) {
        if (theme === 'light') {
            themeToggleBtn.innerHTML = '☀️ <span id="theme-text">Clair</span>';
        } else {
            themeToggleBtn.innerHTML = '🌙 <span id="theme-text">Sombre</span>';
        }
    }
});
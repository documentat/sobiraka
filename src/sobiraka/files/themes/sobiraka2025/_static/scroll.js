document.addEventListener('DOMContentLoaded', () => {

    // Set the smooth scroll behavior only after the page is loaded.
    // Otherwise, an animation would happen on every page refresh, which is ugly.
    setTimeout(() => {
        document.documentElement.style.scrollBehavior = 'smooth';
    }, 0);
});
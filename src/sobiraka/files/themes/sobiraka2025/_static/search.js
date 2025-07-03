document.addEventListener('DOMContentLoaded', () => {

    const search = document.querySelector('search');
    new PagefindUI({
        element: 'search',
        pageSize: 10,
        showImages: false,
        translations: JSON.parse(search.dataset['translations'] || 'null'),
    });

    const searchInput = document.querySelector('.pagefind-ui__search-input');
    const clearSearch = document.querySelector('.pagefind-ui__search-clear');
    const closeSearch = document.querySelector('.close-search');

    // Focus the search field on Ctrl+K
    document.addEventListener('keydown', event => {
        if (event.ctrlKey && event.code === 'KeyK') {
            event.preventDefault();
            searchInput.focus();
        }
    });

    // Clear and close the search interface when clicked on the outside ares
    closeSearch.addEventListener('click', () => clearSearch.click());
});
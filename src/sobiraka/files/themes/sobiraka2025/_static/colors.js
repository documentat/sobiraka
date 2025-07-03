document.addEventListener('DOMContentLoaded', () => {

    const highlightStyleHrefs = {
        'light': document.querySelector('link[data-theme="light"]').href,
        'dark': document.querySelector('link[data-theme="dark"]').href,
    };

    if (localStorage['colors'] !== undefined) {
        document.body.dataset['colors'] = localStorage['colors'];
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.dataset['colors'] = 'dark'
    } else {
        document.body.dataset['colors'] = 'light';
    }

    const highlightStyleLink = document.head.appendChild(document.createElement('link'));
    highlightStyleLink.rel = 'stylesheet';
    highlightStyleLink.href = highlightStyleHrefs[document.body.dataset['colors']];

    document.querySelector('.btn-colors').addEventListener('click', () => {
        const currentColors = document.body.dataset['colors'] || 'light';
        document.body.dataset['colors'] = (currentColors === 'dark') ? 'light' : 'dark';
        localStorage['colors'] = document.body.dataset['colors'];
        highlightStyleLink.href = highlightStyleHrefs[document.body.dataset['colors']];
    });
});
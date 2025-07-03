document.addEventListener('DOMContentLoaded', (event) => {

    const fullscreen = document.querySelector('.fullscreen');

    document.querySelectorAll('.big-image > a, figure > a').forEach(imgLink => {
        imgLink.addEventListener('click', event => {
            const img = imgLink.children[0];


            const fullscreenImg = fullscreen.appendChild(new Image(img.width, img.height));
            fullscreenImg.src = img.src;
            fullscreen.replaceChildren(fullscreenImg);

            fullscreen.classList.add('active');
            fullscreen.focus();
            event.preventDefault();
        });
    });

    fullscreen.addEventListener('keydown', event => {
        console.log(event);
        if (event.code === 'Escape') {
            fullscreen.classList.remove('active');
        }
    });

    fullscreen.addEventListener('click', event => {
        if (event.target === fullscreen) {
            fullscreen.classList.remove('active');
        }
    });

    fullscreen.addEventListener('wheel', event => event.preventDefault());
    fullscreen.addEventListener('touchmove', event => event.preventDefault());
});
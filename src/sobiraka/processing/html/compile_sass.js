const fs = require('node:fs');
const path = require('node:path');
const util = require('node:util');

const {compile, sassTrue, sassFalse} = require('sass');


const args = util.parseArgs({
    options: {
        source: {type: 'string'},
        flavor: {type: 'string'},
        customization: {type: 'string'},
        pdf: {type: 'boolean'},
    },
}).values;

const source = args.source;
const flavor = args.flavor;
const customization = args.customization;

const {css} = compile(source, {
    style: 'compressed',
    functions: {
        'is-browser()': () => args.pdf ? sassFalse : sassTrue,
        'is-pdf()': () => args.pdf ? sassTrue : sassFalse,
    },
    importers: [{
        canonicalize(url) {
            switch (url) {

                case 'flavor':
                    return new URL('sobiraka:flavor');

                case 'customization':
                    return new URL('sobiraka:customization');

                default:
                    return null;
            }
        },

        load(canonicalUrl) {
            switch (canonicalUrl.toString()) {

                case 'sobiraka:flavor':
                    return {
                        syntax: flavor ? path.extname(flavor).substring(1) : 'scss',
                        contents: flavor ? fs.readFileSync(flavor, 'utf8') : ''
                    };

                case 'sobiraka:customization':
                    return {
                        syntax: customization ? path.extname(customization).substring(1) : 'scss',
                        contents: customization ? fs.readFileSync(customization, 'utf8') : ''
                    };

                default:
                    return null;
            }
        },
    }],
});

console.log(css);
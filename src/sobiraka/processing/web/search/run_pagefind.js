const fs = require('node:fs');
const path = require('node:path');
const readline = require("node:readline");
const util = require('node:util');

const args = util.parseArgs({
    options: {
        'indexPath': {type: 'string'},
    },
}).values;

(async function () {
    let pagefind;
    try {
        pagefind = await import('pagefind');
    } catch (err) {
        pagefind = await import(`${process.env.NODE_PATH}/pagefind/lib/index.js`);
    }

    const {index} = await pagefind.createIndex();

    const rl = readline.createInterface({input: process.stdin});
    for await (const line of rl) {
        const record = JSON.parse(line);
        await index.addCustomRecord(record);
    }

    await index.writeFiles({outputPath: args.indexPath});
})();
import {createRequire} from 'node:module';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(resolve(process.argv[2]||root,'package.json'));
const {build}=require('esbuild');
const work=resolve(process.argv[3]||resolve(root,'.local'));
await build({entryPoints:[resolve(work,'pages-src/worker.mjs')],outfile:resolve(work,'pages-dist/_worker.js'),bundle:true,format:'esm',platform:'browser',target:'es2022',external:['cloudflare:sockets'],legalComments:'none'});
console.log('Cloudflare Pages Worker bundled.');

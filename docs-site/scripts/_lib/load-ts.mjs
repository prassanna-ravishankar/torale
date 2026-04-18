import { build } from 'esbuild';

/**
 * Bundle a .ts entry point with esbuild and dynamic-import it. Returns the
 * module's exports. Used by build scripts to load typed data files without a
 * runtime TS loader.
 */
export async function loadTsModule(entryPath) {
  const bundle = await build({
    entryPoints: [entryPath],
    bundle: true,
    format: 'esm',
    platform: 'node',
    target: 'node20',
    write: false,
  });
  const code = bundle.outputFiles[0].text;
  const dataUrl = `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
  return import(dataUrl);
}

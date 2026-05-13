import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import sitemap from '@astrojs/sitemap';
import polyglot from 'starlight-polyglot';

export default defineConfig({
  site: 'https://edithatogo.github.io/lifecourse',
  base: '/lifecourse',
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'lifecourse Documentation',
      plugins: [
        polyglot({ python: { entryPoints: ['src/lifecourse'], output: 'api/python' } }),
      ],
      sidebar: [
        { label: 'Home', link: '/' },
        { label: 'Getting Started', link: '/getting-started/' },
        { label: 'Design', link: '/design/' },
        { label: 'Requirements', link: '/requirements/' },
        { label: 'Architecture', link: '/architecture/' },
        { label: 'Simulation Engine', link: '/simulation-engine/' },
        { label: 'API Reference', autogenerate: { directory: 'api' } },
      ],
    }),
    sitemap(),
  ],
});

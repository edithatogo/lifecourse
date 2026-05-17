import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import sitemap from '@astrojs/sitemap';
import starlightLinksValidator from 'starlight-links-validator';
import starlightVersions from 'starlight-versions';
import starlightLlmsTxt from 'starlight-llms-txt';

export default defineConfig({
  site: 'https://edithatogo.github.io/lifecourse',
  base: '/lifecourse',
  trailingSlash: 'always',
  integrations: [
    starlight({
      title: 'lifecourse Documentation',
      description: 'Health-economic microsimulation for genomic testing policy analysis',
      logo: {
        src: './src/assets/logo.svg',
        alt: 'lifecourse logo',
      },
      social: {
        github: 'https://github.com/edithatogo/lifecourse',
      },
      editLink: {
        baseUrl: 'https://github.com/edithatogo/lifecourse/edit/main/docs/astro-site/',
      },
      lastUpdated: true,
      plugins: [
        starlightLinksValidator(),
        starlightVersions({
          versions: [
            { slug: 'latest', label: 'latest' },
          ],
          defaultVersion: 'latest',
        }),
        starlightLlmsTxt({
          full: true,
        }),
      ],
      sidebar: [
        {
          label: 'Start Here',
          items: [
            { label: 'Home', link: '/' },
            { label: 'Getting Started', link: '/getting-started/' },
            { label: 'Usage Guide', link: '/usage/' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { label: 'API Reference', link: '/api-reference/' },
          ],
        },
        {
          label: 'Community',
          items: [
            { label: 'Contributing', link: '/contributing/' },
          ],
        },
      ],
    }),
    sitemap(),
  ],
});

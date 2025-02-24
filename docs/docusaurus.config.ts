import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Valthera Docs',
  tagline: 'Securing the Future',
  favicon: 'img/valthera-logo-light.png',

  // Set the production url of your site here
  url: 'https://valthera.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub Pages deployment, it is often '/<projectName>/'
  baseUrl: '',

  // GitHub pages deployment config.
  organizationName: 'valthera', // Your GitHub org/user name.
  projectName: 'valthera', // Your repository name.
  deploymentBranch: 'gh-pages',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {    
        docs: {
          routeBasePath: '/', // This makes `/docs` accessible directly from `/`
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/valthera/valthera/tree/main/docs/',
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl:
            'https://github.com/valthera/valthera/tree/main/docs/',
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'Valthera Docs',
      logo: {
        alt: 'Valthera Logo',
        src: 'img/valthera-logo-light.png',
      },
      items: [        
        {
          href: 'https://github.com/valthera/valthera',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [             
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Valthera, Inc.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;

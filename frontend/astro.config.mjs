import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
  output: 'static',
  site: 'https://shop.xspi.pro',
  trailingSlash: 'always',
  build: { format: 'directory' },
  integrations: [react()],
});

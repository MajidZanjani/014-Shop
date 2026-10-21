import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const probes = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/probes' }),
  schema: z.object({
    id: z.literal('skeleton'),
    title: z.string().min(1).max(120),
    evidence_class: z.literal('local-synthetic'),
  }).strict(),
});

export const collections = { probes };

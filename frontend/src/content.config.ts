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

const products = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/products' }),
  schema: z.object({
    schema_version: z.literal(1), product_id: z.literal('sll-xspi-mc'), support_product_id: z.literal('sll-xspi-mc-support-10h'), profile_id: z.literal('sll-xspi-mc-v1'),
    title: z.string().min(1).max(120), site: z.literal('https://shop.xspi.pro'), source_sha256: z.string().regex(/^[a-f0-9]{64}$/),
    vendors: z.array(z.object({id:z.string(),label:z.string(),families:z.array(z.object({id:z.string(),label:z.string()}).strict())}).strict()).length(3),
    terms: z.array(z.object({id:z.string(),label:z.string(),vendors:z.array(z.string()),description:z.string()}).strict()).length(3),
    production_bands: z.array(z.object({id:z.string(),label:z.string(),minimum:z.number().int().positive(),maximum:z.number().int().positive().nullable()}).strict()).length(4),
    approvals: z.object({prices:z.null(),rights:z.null(),access:z.null(),coverage:z.null(),terms:z.null(),recurrence:z.null(),production_accounting:z.null()}).strict(),
    money: z.object({currency:z.literal('EUR'),currency_status:z.literal('draft'),base_minor:z.null(),additional_family_minor:z.null(),production_minor:z.null(),mode_minor:z.null(),node_minor:z.null(),support_minor:z.null(),tax_minor:z.null(),total_minor:z.null()}).strict(),
    support_seconds_per_package:z.literal(36000),
  }).strict(),
});
export const collections = { probes, products };

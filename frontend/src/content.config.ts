import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const probes = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/probes' }),
  schema: z.object({ id:z.literal('skeleton'), title:z.string().min(1).max(120), evidence_class:z.literal('local-synthetic') }).strict(),
});
const products = defineCollection({
  loader: glob({ pattern: 'supporting-hours-bundle.md', base: './src/content/products' }),
  schema: z.object({
    schema_version:z.literal(1),product_id:z.literal('supporting-hours-bundle'),title:z.literal('Supporting Hours Bundle'),
    site:z.literal('https://shop.xspi.pro'),visibility:z.literal('invitation-only'),
    source_sha256:z.literal('ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e'),manual_time_tracking:z.literal(true),
    variants:z.tuple([
      z.object({id:z.literal('shb-fpga-10h'),label:z.literal('FPGA Supporting Hours Bundle'),hours_per_bundle:z.literal(10),workflow:z.literal('checkout'),hours_expire:z.literal(false)}).strict(),
      z.object({id:z.literal('shb-asic-25h'),label:z.literal('ASIC Supporting Hours Bundle'),hours_per_bundle:z.literal(25),workflow:z.literal('request'),hours_expire:z.null()}).strict(),
    ]),
    commercial:z.object({currency:z.null(),fpga_hourly_minor:z.null(),asic_hourly_minor:z.null(),approved_offer_revision:z.null(),tax_policy_revision:z.null(),terms_revision:z.null(),privacy_revision:z.null(),refund_revision:z.null(),asic_supplement_revision:z.null(),manual_charging_policy_revision:z.null()}).strict(),
  }).strict(),
});
export const collections = { probes, products };

#!/usr/bin/env python3
"""One-time, explicit 30 October scope amendment; never replay over later work."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / '.planning'
ARCHIVE = ROOT / 'docs/archive/2026-10-30-before-shb'
SOURCE = '014-Shop-SHB-Proposal-Revision-2026-10-30.md'
DIGEST = 'ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e'
QUICK = 'quick/261030-dsk-apply-shb-revision-1-1-rewrite-all-activ/261030-dsk'
PHASES = {
 1: ('Source authority and SHB scope reconciliation', 'Retain immutable sources; apply SHB revision 1.1, document deferrals and reconcile every planning file.', 'Source hash, archive readback, planning inventory and all thirty acceptance mappings.', []),
 2: ('Reproducible application and isolated deployment foundation', 'Reuse exact pinned Astro/Django/PostgreSQL/worker stack; retain database destination, all-write/attestation, native/licence/SBOM, immutable-image, CI and independent runtime gates.', 'Original BUILD-01–08 criteria, actual PostgreSQL, full OCI/CI and authorized independent lifecycle/resource/storage observations. No full acceptance is claimed.', [1]),
 3: ('Supporting Hours Bundle catalog and approved pricing', 'One Supporting Hours Bundle product; FPGA Supporting Hours Bundle/10 hours and ASIC Supporting Hours Bundle/25 hours. Strict positive quantity and authoritative integer money; approved ASIC base hourly rate exceeds FPGA. Per-order purchased hours only.', 'SHB-01/03/04/05/29; null live rates/terms fail closed, explicit synthetic fixtures pass. Markdown is the reviewed catalog source.', [1]),
 4: ('Shared SHB form, invitations and private storefront', 'Minimal common billing/contact form, same-phone helper and conditional tax; ASIC short assistance/context. Six calendar months in Asia/Tbilisi, UTC expiry, digest-only reusable invitations, current-state session checks and private static delivery.', 'SHB-02/06/10/11/12/13/14/27. Deny base/deep/static/origin/alternate-host bypass and new IP purchases; GET has no purchase/request/coupon/mail effects.', [3]),
 5: ('SHB durable records, archives and outbox', 'Reuse immutable order/acceptance/payment and archived evidence/outbox primitives. Add invitation/request/offer/coupon records with explicit customer scope. Preserve old data and ledger without connecting SHB.', 'Transactions/uniqueness/retry identity, archive-before-effects, bounded leased worker and failure recovery; no manual-time record import or cumulative balances.', [3]),
 6: ('Invitation scope, verified resources and staff MFA', 'Invitation authorizes current offers/new purchases only; no customer history or prefilled private data. Retain verified-contact access for old private resources and MFA/recent verification/resource permissions for every staff route.', 'SHB-11/13/14/22. Forwardable bearer is not named identity; contact edits never replace the authorized company support contact.', [4,5]),
 7: ('FPGA checkout, ASIC reviewed offers and scoped discounts', 'Automatic eligible FPGA checkout; ASIC request/clarify/decline/withdraw/approve/dated offer/acceptance. One scoped percentage code; PostgreSQL reservations survive ASIC review beyond claim expiry. Immutable accepted price/scope revisions.', 'SHB-05/07/08/09/15/16/17/18. Concurrent one-use arbitration, price-change reacceptance, one active offer/reservation; no routine engineer approval for eligible FPGA.', [3,4,5,6]),
 8: ('Payment lifecycle and fault-injectable synthetic bank', 'Reuse one archived attempt claim and lookup-only uncertainty; authenticate/correlate merchant/order/amount/currency and preserve duplicate money events without duplicate purchase. Couple coupon consumption/finalization/outbox durably.', 'SHB-19/20/21/22/23. Real PostgreSQL races/process interruption, forged return/callback denial, safe cancellation/expiry and no blind retry.', [7]),
 9: ('Selected-bank sandbox and complete reconciliation', 'Implement only actual selected-bank documented hosted payment/callback/status/refund capabilities and transaction bounds. Keep unknown provider behavior disabled.', 'Authenticated sandbox positive/negative evidence and complete financial windows under separately supplied merchant/provider authority.', [8]),
 10: ('Paid SHB orders, transaction notices and manual handoff', 'Finalize accepted verified paid orders once with variant, quantity, per-order hours, scope and reference; staff order view plus retryable transaction/request notifications. Financial refunds link the original order; staff consult/inform manual support records.', 'SHB-07/20/23/24/25/26. No new IP licence/package/reference-design obligation, time credit/debit, usage calculation, time-entry screen, task-email automation or customer bundle panel.', [7,8]),
 11: ('Private release delivery and protected-host qualification', 'Private Object Storage releases; manifest-approved Astro snapshot behind Django authorization in isolated shop runtime. Retain unchanged shared ingress/TLS, full inventory/allowlist/activation-impact review, separate DB and aggregate CPU/memory/storage controls.', 'SHB-10/30. No publicly readable protected copy/JSON/assets/sourcemap/preview bypass; exact scoped host/service/action authority before mutations, no A/AAAA before traffic path proof.', [2,4,6]),
 12: ('Independent backup, restore and SHB reopening', 'Independent sbg backups, complete-pool-loss off-host rehearsal and custody. Block effects before exposure; invalidate restored sessions/MFA; reconcile original invitation expiry/revocations, customer scope, financial/order/acceptance/coupon/offer/document events.', 'SHB-28. Preserve original order references and prevent staff counting replay as a new sale. Five-minute WAL timeout, 35-day DB window, 15-minute RPO and four-hour operator-start restore are proposed targets; measure safe reopening separately.', [5,8,10,11]),
 13: ('Thirty SHB acceptance cases and release verification', 'Exercise both variant paths, JS/no-JS keyboard/mobile, invite/static/customer isolation, PostgreSQL coupon/payment concurrency, transaction-mail failure and restore/replay. Trace each SHB-01–30 result to exact artifacts.', 'No skipped mandatory shared security/payment/recovery check; distinguish local/synthetic, selected-bank, actual OVH, production and attributable human evidence. Dedicated deferred IP/time-ledger tests are not SHB launch gates.', [3,4,6,7,8,10]),
 14: ('SHB handover and separately authorized activation', 'Version release/config/catalog/policy identities, actual support-offer approvals, operating owners, private release/rollback/custody and concrete pending external actions. Supply usable local demonstration and full commands.', 'SHB-29/30; required image/runtime/legal/CI/independent/recovery/host/mail/bank evidence and exact external action authority. No activation from proposal or generic deployment approval.', [9,11,12,13]),
}
PRIMARY = {1:3,2:4,3:3,4:3,5:3,6:4,7:10,8:7,9:7,10:4,11:6,12:4,13:6,14:6,15:7,16:7,17:7,18:7,19:8,20:8,21:8,22:8,23:10,24:10,25:10,26:10,27:4,28:12,29:14,30:11}
SCENARIOS = {}
for line in (ROOT / SOURCE).read_text().splitlines():
    match = re.match(r'\| SHB-(\d+) \| (.*?) \| (.*?) \|', line)
    if match:
        SCENARIOS[int(match[1])] = (match[2], match[3])

PROTECTION = '''Existing October21 protection/security/financial/recovery requirements remain binding where relevant. Preserve Stalwart, WebAdminProxy, Plesk/WordPress, existing PostgreSQL, Prometheus, Grafana/Grafana-TLS, Blackbox, Alertmanager, MicroVMs, NetBird, Matrix and every pre-existing/uncertain resource in every state. No blanket NixOS activation, protected reload/restart/edit/prune/GC/upgrade/reboot, firewall/DNS/TLS change, real bank/mail action or paid fallback. Inventory all owners/resources read-only, maintain docs/host-protection-inventory.md and docs/shop-resource-allowlist.md, separate database identity and complete activation-impact review before any authorized shop write. Rootless shopsvc directly on mx1, outside claude-dev; one leased worker, independent PostgreSQL, internal Caddy. Proposed host-controlled aggregate 200% CPU, 6G high/8G max, bounded tasks; preserve cpusets/parents/guests. Proposed 80 GiB aggregate ZFS including snapshots/descendants, 50 GiB DB including WAL; account GraphRoot/images/volumes/temp/logs/certificates/spool/backups. Private gra release storage and independent sbg recovery custody; no new production compute/block/IP rental. No host process/control/management mounts in apps. Independent runtime/fault/exhaustion/complete-loss drills require an assigned authorized off-host runner; none is assigned. Production/bank-sandbox database connection gate stays closed until actual identity/all-write/transport/migration/runtime qualification. Prepared evidence is not completion; archive recoverable accepted/order/payment/document effects before use; uncertain bank dispatch cannot authorize a blind retry.'''
MANUAL = 'SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n')


def jwrite(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False))


def link(path, target):
    import os
    return Path(os.path.relpath(target, path.parent)).as_posix()


def header(path, title):
    return f'# {title}\n\nCurrent authority: [SHB revision 1.1]({link(path, ROOT / SOURCE)}), SHA256 `{DIGEST}`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md]({link(path, P / "STATE.md")}) / [ROADMAP.md]({link(path, P / "ROADMAP.md")}).\n\n'


def historical(path, raw, role='historical-evidence'):
    old = ARCHIVE / path.relative_to(ROOT)
    title = next(iter(re.findall(r'^#+ (.+)', raw, re.M)), path.stem)
    phase = next((int(x[:2]) for x in path.parts if re.match(r'^\d{2}-', x)), None)
    body = header(path, title + ' — retained historical record')
    body += f'Disposition: **{role}**. [Exact original bytes and dated evidence]({link(path, old)}); original SHA256 `{hashlib.sha256(raw.encode()).hexdigest()}`. This pointer does not change any evidence or contract and does not award SHB acceptance. Historical next actions are superseded.\n\n'
    if phase in PHASES:
        body += f'Current Phase {phase}: **{PHASES[phase][0]}**. {PHASES[phase][1]}\n\n'
    return body + MANUAL + '\n\nShared payment/security/recovery/host gates remain in REQUIREMENTS.md and the applicable current phase plans.\n'


def plan(path, phase, number, action=None, deferred=False):
    title, scope, verify, deps = PHASES[phase]
    requirements = [f'SHB-{i:02d}' for i,p in PRIMARY.items() if p == phase]
    if phase == 13: requirements = [f'SHB-{i:02d}' for i in range(1,31)]
    text = f'---\nphase: {path.parent.name}\nplan: "{number:02d}"\ntype: execute\nwave: {max(1,phase-1)}\ndepends_on: {json.dumps([f"{d:02d}-01" for d in deps])}\nautonomous: true\nstatus: {"superseded" if deferred else "ready"}\nrelease: shb-1.1\nrequirements: {json.dumps(requirements)}\nfiles_modified: []\nmust_haves:\n  truths:\n    - {json.dumps(scope)}\n  artifacts: []\n---\n\n'
    text += header(path, f'{phase:02d}-{number:02d}: {title}')
    if deferred:
        return text + 'This historical task ID is **deferred from SHB launch**, not completed. Preserve its implementation, data, contracts and recorded evidence. No execution or dedicated qualification for this IP/time-accounting task is needed for new SHB purchases.\n\n' + MANUAL + '\n'
    text += f'<objective>{scope}</objective>\n\n<tasks>\n<task type="auto" tdd="true" id="{phase:02d}-{number:02d}-01">\n<name>{title}</name>\n<files>{action[0] if action else "Existing phase-owned modules; concrete code paths must be inspected before edits."}</files>\n<action>{action[1] if action else scope} {MANUAL}</action>\n<verify>{action[2] if action else verify}</verify>\n<done>{verify}</done>\n</task>\n</tasks>\n\n'
    text += '<verification>Use real PostgreSQL for concurrency; reject missing/skipped evidence. Local/synthetic results never establish actual provider/host/legal/independent approval. Retain exact failed controls and archive-before-effects. No runtime activation in this plan without separate actual authority.</verification>\n\n' + PROTECTION + '\n'
    return text


def main():
    assert hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest() == DIGEST
    assert len(SCENARIOS) == 30
    assert not ARCHIVE.exists(), 'One-time migration already ran; refuse to overwrite later work'
    before = {f: f.read_bytes() for f in P.rglob('*') if f.is_file() and f.name != 'milestone.lock' and QUICK not in f.as_posix()}
    external = [ROOT / x for x in ('AGENTS.md','README.md','docs/decisions.md','docs/purchase-flow.md')]
    for f in external:
        if f.exists(): before[f] = f.read_bytes()
    for path, raw in before.items():
        dest = ARCHIVE / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        assert hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(raw).digest()
    jwrite(ARCHIVE / 'manifest.json', {'schema':1, 'source':SOURCE, 'revision':'1.1', 'files':[
        {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)} for p,raw in sorted(before.items())]})
    write(ARCHIVE / 'ARCHIVE-INDEX.md', '# Before SHB revision 1.1\n\nExact original planning/instruction bytes. Historical evidence only; current routing is in ../../../.planning/STATE.md. manifest.json binds each original path, SHA256 and length. These files are not current work instructions; their historical links retain their original text.\n')
    dirs = {int(f.name[:2]):f for f in (P / 'phases').iterdir() if f.is_dir()}
    for phase in PHASES:
        if phase not in dirs:
            slug = {5:'durable-records-and-outbox',6:'invitation-scope-and-staff-mfa',9:'selected-bank-reconciliation',11:'private-delivery-and-protected-host',12:'independent-recovery',14:'shb-release-handover'}[phase]
            dirs[phase] = P / 'phases' / f'{phase:02d}-{slug}'
    for path,rawbytes in before.items():
        if P not in path.parents: continue
        raw = rawbytes.decode()
        if path.name == 'config.json':
            value=json.loads(raw); value['release']='shb-1.1'; value['source_revision_sha256']=DIGEST
            jwrite(path,value)
        elif path.name.startswith('.continue-here') or path.name=='HANDOFF.json':
            path.unlink()  # consumed pause routing, exact original retained above
        elif path.suffix=='.json':
            jwrite(path,{'schema':1,'release':'shb-1.1','disposition':'historical-evidence','original':str((ARCHIVE/path.relative_to(ROOT)).relative_to(ROOT)), 'source_sha256':DIGEST})
        elif path.name.endswith('-PLAN.md') and 'quick' not in path.parts:
            match=re.match(r'(\d+)-(\d+)-PLAN.md',path.name);phase,number=map(int,match.groups())
            if phase==2 and not path.with_name(path.name.replace('PLAN','SUMMARY')).exists():
                # Keep the exact detailed foundation tasks, acceptance and threat controls.
                # Remove only prior running-log appendices and obsolete routing prose.
                body=raw[raw.index('---\n'):]
                body=body.split('\n## Current image qualification implementation')[0]
                body=body.replace('Current authority is the complete October 21 proposal/handoff, .planning/PROJECT.md and docs/decisions.md.', 'SHB revision 1.1 controls product scope; the complete October21 protection/foundation contract remains binding.')
                write(path,header(path,f'{phase:02d}-{number:02d}: retained shared foundation') + 'Release dependency retained; local SHB product implementation proceeds first. Old IP-only/time-ledger launch requirements are deferred. Complete original task actions, verification and threats below still apply to shared foundation qualification.\n\n'+body)
            elif phase in (1,2) or (phase==7 and number==1):
                write(path,historical(path,raw,'completed-prior-slice'))
            else:
                action=None
                if phase==3:
                    action=('frontend/src/content/products/supporting-hours-bundle.md, scripts/compile_shb_catalog.py, backend/shop/shb/catalog.py, backend/shop/shb/forms.py', 'Compile one closed Markdown/YAML catalog with exact labels and 10/25-hour variants, null live rate/currency/policy approval values and explicit private synthetic fixture. Validate positive integer quantities, exact bounded money, higher ASIC base rate, per-order hours and shared minimal common/ASIC form rules. No new dependency pins.', 'python3 scripts/check_shb.py; python3 scripts/check_purchase_plan.py; focused compiler/form tests and real-PostgreSQL SHB tests.')
                if phase==4:
                    action=('backend/shop/shb, backend/shop/urls.py, backend/shop/core/middleware.py, frontend/src/pages, scripts/demo_shb.py, ops/caddy', 'Implement shared no-JavaScript form and selected React island; one private SHB snapshot. Digest-only 32-byte reusable invitations expire six calendar months from creation in Asia/Tbilisi with month-end clamp. Retain shorter existing 30-minute sessions capped by invite expiry, check current revocation/expiry every protected request and rotate session on entry. No PII prefill/history. Gate HTML/catalog/prices/assets and deny old IP sale paths/backend submissions. Keep unknown rate/terms disabled; no effect on invite GET. Prove server, alternate-path and origin denial before any publication.', 'python3 scripts/check_shb.py; backend invitation/form/route tests, private static manifest checks, then exact frontend build/check and keyboard/mobile browser coverage.')
                if phase==7:
                    detail={2:'Reserve/consume scoped percentage discounts with approved policy and atomic PostgreSQL customer/variant/use constraints; preserve ASIC reservation beyond coupon claim deadline and never release an uncertain payment claim.',3:'Reuse immutable FPGA order/acceptance/payment interfaces; eligible FPGA is automatic. ASIC submit is unpaid; assigned recent-MFA reviewer clarifies/declines/approves and issues matching immutable dated offer with explicit acceptance. Preserve company/contact separation.',4:'Implement assigned ASIC review/offer revision and explicit withdraw/expiry/reissue actions. One active reservation/payable offer, no customer/quantity/scope substitution. Default 14-day offers and 30-day coupon claims remain proposed pending commercial adoption.'}.get(number,PHASES[7][1])
                    action=('backend/shop/shb, existing catalog/quotation/payment/access/worker services',detail,PHASES[7][2])
                if phase==10:
                    detail={1:'Record one accepted/verified paid SHB order, its bundle quantity/hours and reference, without invoking legacy fulfilment/support-grant services.',4:'Archive invoice/receipt evidence and queue ordinary purchase/request/offer notifications in the existing durable worker; same order reference on retries. Staff order view exposes purchase facts, no handoff-ack gate.',5:'Keep financial refunds/chargebacks/corrections linked to original order and immutable money history; consult manual support records when unused hours matter and record staff communication to support. Never infer unused hours or reverse a time ledger.'}.get(number,PHASES[10][1])
                    action=('backend/shop/shb, existing payments/worker/staff order and document interfaces',detail,PHASES[10][2])
                write(path,plan(path,phase,number,action,deferred=phase==10 and number in (2,3,6)))
        else:
            role='deferred-IP-or-time-accounting-evidence' if any(x in path.name for x in ('SUPPORT-LEDGER','STATEMENT-MAIL','LICENCE-CHANGES','PRIVATE-PACKAGES','SUPPORT-RECOVERY','DELIVERY-HOLDS')) else 'historical-evidence'
            write(path,historical(path,raw,role))
    for phase in (5,6,9,11,12,14):
        path=dirs[phase]/f'{phase:02d}-01-PLAN.md';write(path,plan(path,phase,1))
    now=datetime.now(timezone.utc).isoformat();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status='in progress — SHB revision 1.1 replanned; implementing the single-product catalog and minimum forms; no live acceptance.'
    current='03-01 — Supporting Hours Bundle catalog, 10/25-hour variants and common/ASIC form rules.'
    next_action='Implement and verify SHB catalog/forms, then invitation-gated private storefront and old-IP route denial; continue FPGA/ASIC/coupon/payment integration under the revised plans.'
    status_block=f'**Current development focus:** 3 — Supporting Hours Bundle catalog and approved pricing.\n\n**Last fully completed phase:** 1 — documentary authority/reconciliation only; historical implementation evidence is not SHB acceptance.\n\n**Current plan:** {current}\n\n**Execution status:** {status}\n\n**Next implementation task:** {next_action}\n'
    state=f'''---
gsd_state_version: "1.0"
release: shb-1.1
current_phase: 3
current_phase_name: Supporting Hours Bundle catalog and approved pricing
current_plan: 1
current_task: 1
status: in_progress
last_updated: "{now}"
last_activity: 2026-10-30
state_head: {head}
progress:
  total_phases: 14
  completed_phases: 1
  total_plans: {len(list((P/'phases').glob('*/*-PLAN.md')))}
  completed_plans: {len(list((P/'phases').glob('*/*-SUMMARY.md')))}
  percent: 7
---

'''+header(P/'STATE.md','Project state — Supporting Hours Bundle revision 1.1')+status_block+'\n'+MANUAL+'\n\nHistorical completed-plan counts describe retained records, not SHB acceptance or engineering effort. Earlier Phase2 policy-issuance continuation is retained as a release prerequisite and is not the next product task.\n\n## Evidence and constraints\n\nPrevious synthetic backend/payment, archived transaction, staff MFA/recovery, exact source/image/SBOM/lock evidence remains attributable at docs/archive/2026-10-30-before-shb and docs/build. No old test result verifies the revised SHB product. SHB tests are pending until executed.\n\n## External inputs\n\nOne support-offer record and exact operation boundaries are in docs/decisions.md. No commercial rate/legal/tax/ASIC adoption, bank/mail/provider, independent runner, host or public activation approval is invented. User will provide company inputs later; continue independent local work without repeated requests.\n\n## Session Continuity\n\nLast session: '+now+'\nStopped at: active SHB replan complete; proceeding with 03-01. Old pause artifacts archived/consumed.\nResume file: HANDOFF.md\n\nSandbox startup fails on this workspace; narrowly scoped escalated local commands are the recorded workaround. Use existing owned .scratch/auth-unicode-tmp and .scratch/phase2-repro-nix-cache per command. Do not read/delete/stage unrelated http_cache.sqlite. No .env or real credentials are needed. Exact context percentage is unavailable; honor the user checkpoint rule without claiming automatic threshold monitoring.\n'
    write(P/'STATE.md',state)
    project=header(P/'PROJECT.md','SLL Supporting Hours Bundle Shop')+status_block+'''\n## What this is

Invitation-only B2B shop at https://shop.xspi.pro with one visible Supporting Hours Bundle product and exactly FPGA Supporting Hours Bundle (10 hours) / ASIC Supporting Hours Bundle (25 hours). Automatic eligible FPGA purchases and technically reviewed ASIC requests/offers share minimal company/billing/contact fields, quantity, optional scoped percentage code and versioned terms. No new IP sales.

**Core value:** Turn an invited eligible support purchase or approved ASIC offer into attributable acceptance, verified payment, one recoverable paid order and reliable support-team purchase information, without duplicate money/coupon/notification effects.

## Active scope

Retain Astro Content Collections + selected React islands, Django LTS/Gunicorn, PostgreSQL and one leased outbox worker. No request-time Node/adapter, mandatory Redis/Celery/CMS/IdP or replacement commerce platform. Markdown/YAML compiles reviewed versioned catalog and policies; staff cannot invent competing live prices. Private Astro release delivery must enforce server authorization for every protected static/API route. Invitations are reusable digest-only bearer access, six calendar months in Asia/Tbilisi, current-state expiry/revocation; they do not authorize history/private files or establish personal identity.

Commercial recommendations (30-day coupon claims, 14-day offers, ASIC no-expiry, manual time-charging convention) require real adoption before affected live operations. Existing shorter 30-minute session limit is retained and capped by invitation expiry. Approved rates/currency/taxes/legal/policies remain null until evidenced; synthetic fixtures must be visibly classified and never approved live.

## Deferred from this release

'''+MANUAL+'\n\nIP configurator/licence/host/production-band sales and new package/key/reference-design delivery are deferred. No per-sale FPGA technical approval, technical dossier, uploads, general consultancy, PCB design/layout, third-party IP support or paid time-management platform. Historical contracts/entitlements/financial records and obligations remain immutable.\n\n## Binding protection and durability\n\n'+PROTECTION+'\n\n## Workflow\n\nCurrent plan is the existing ROADMAP.md/STATE.md and per-phase plans; no replacement master plan. Continue substantive authorized local work across commits; ordinary non-force origin/main push after each project commit is already authorized. Do not stop after planning or each commit. Pause only for explicit user request, actual missing authority/prerequisite or real context pressure under the recorded context rule.\n'
    write(P/'PROJECT.md',project)
    roadmap=header(P/'ROADMAP.md','Roadmap — Supporting Hours Bundle')+status_block+'\nStable T01–T14/folder IDs preserve history. Titles and active task scopes now follow SHB 1.1. Completed summary counts below are historical records, not engineering effort or new commercial acceptance.\n\n## Phases\n\n'
    for phase,(title,scope,verify,deps) in PHASES.items():
        focus=' — CURRENT DEVELOPMENT FOCUS; '+status if phase==3 else ''
        roadmap+=f'- [{"x" if phase==1 else " "}] **Phase {phase}: {title}**{focus}\n'
    roadmap+='\n## Phase details\n\n'
    for phase,(title,scope,verify,deps) in PHASES.items():
        ids=[f'SHB-{i:02d}' for i,p in PRIMARY.items() if p==phase]
        if phase==13:ids=[f'SHB-{i:02d}' for i in range(1,31)]
        focus=' — CURRENT DEVELOPMENT FOCUS; '+status if phase==3 else ''
        roadmap+=f'### Phase {phase}: {title}{focus}\n\nGoal: {scope}\n\nDepends on: {", ".join(map(str,deps)) or "source authority"}. Local unaffected slices proceed while actual external gates remain pending.\n\nAcceptance: {verify}\n\nRequirements: {", ".join(ids) or "retained shared controls in REQUIREMENTS.md"}.\n\nPlans: '+', '.join(f'[{x.stem}]({x.relative_to(P).as_posix()})' for x in sorted(dirs[phase].glob('*-PLAN.md')))+'\n\n'
    roadmap+='## Progress\n\n| Phase | Retained plan summaries | Status | SHB qualification |\n|---|---|---|---|\n'
    for phase,(title,*_) in PHASES.items():
        count=len(list(dirs[phase].glob('*-SUMMARY.md')));total=len(list(dirs[phase].glob('*-PLAN.md')))
        rowstatus='Complete (documentary scope)' if phase==1 else 'In Progress' if phase in (2,3,5,6,7,8,10,12,13) else 'Pending'
        focus='; CURRENT DEVELOPMENT FOCUS; '+status if phase==3 else ''
        roadmap+=f'| {phase}. {title} | {count}/{total} | {rowstatus}{focus} | {"Source reconciliation only" if phase==1 else "Pending actual revised evidence"} |\n'
    write(P/'ROADMAP.md',roadmap)
    machine={'contract':'1.0.0','flavor':'core','milestone':'shb-1.1','source_revision_sha256':DIGEST,'phases':[{'number':str(n),'name':v[0],'status':'complete' if n==1 else 'in_progress' if n in (2,3,5,6,7,8,10,12,13) else 'pending'} for n,v in PHASES.items()], 'next':{'command':'$gsd-execute-phase 3','label':'Implement SHB catalog and forms','reason':'30 October user-authorized SHB revision 1.1'},'updated_at':now}
    jwrite(P/'state.json',machine)
    write(P/'HANDOFF.md',header(P/'HANDOFF.md','Active SHB continuation')+status_block+f'\n**Recorded implementation:** {head}\n\nReplan is not product completion. Continue 03-01 immediately; then 04-01 access/private delivery and 07/08/10 workflows. No old Phase2 pause or historic time-ledger task routes execution.\n\n'+MANUAL+'\n\nExternal dependencies and actual operation scope: docs/decisions.md. No independent runner or new external authority. Full commands/results will be recorded only after execution. Original snapshot and inventory: docs/archive/2026-10-30-before-shb/manifest.json.\n')
    requirements=header(P/'REQUIREMENTS.md','SHB release requirements')+'STATE.md and ROADMAP.md own current status. No SHB criterion is complete merely because earlier code/tests exist.\n\n'
    for ident,(scenario,result) in SCENARIOS.items():
        requirements+=f'- [ ] **SHB-{ident:02d}**: {scenario} — {result}\n'
    requirements+='\n## Retained shared controls\n\n'+PROTECTION+'\n\nRetain input validation, resource/contact authorization, recent staff MFA, CSRF/origin/host checks, privacy/log redaction, immutable approved money/terms/acceptance, positive database identity/all-write/migration guards, durable outbox/leases, archive-before-effects, exact provider correlation, uncertainty/reconciliation and financial refund history. AUTH-01 deliberate single-use mailbox verification remains for retained private resources; invitations are separately reusable bearer access.\n\n## Previous requirement disposition\n\n| ID | SHB disposition |\n|---|---|\n'
    original_req=before[P/'REQUIREMENTS.md'].decode()
    for ident in re.findall(r'^- \[[x ]\] \*\*([A-Z]+-\d+)\*\*:',original_req,re.M):
        deferred=(ident.startswith('FLOW-') and ident!='FLOW-08') or ident in ('SRC-02','AUTH-04','AUTH-05','COM-01','COM-02','FUL-01','FUL-03','FUL-04','FUL-05','FUL-06','OPS-04','SHOP-02')
        requirements+=f'| {ident} | {"Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate" if deferred else "Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred"} |\n'
    requirements+='\n'+MANUAL+'\n\n## Traceability\n\n| Requirement | Primary phase | Status |\n|---|---|---|\n'
    for ident,phase in PRIMARY.items():requirements+=f'| SHB-{ident:02d} | Phase {phase} | Pending revised evidence |\n'
    write(P/'REQUIREMENTS.md',requirements)
    sources=header(P/'SOURCES.md','Source authority and preserved identities')+f'Primary operative source: `{SOURCE}`, revision 1.1, SHA256 `{DIGEST}`, 82,668 bytes / 1,017 lines, read completely including Appendix A. Direct user instruction controls future scope; no unresolved scope conflict remains.\n\nSource precedence: 30 October direct instructions → SHB 1.1 operative sections → Appendix A FPGA draft terms → consistent earlier security/financial/recovery/host requirements. Appendix A old title/cart/price placeholders and automatic-ledger interpretations cannot override operative manual tracking. Historical October21/26 inputs and evidence hashes remain immutable.\n\nUse PROJECT.md, REQUIREMENTS.md, ROADMAP.md and STATE.md together. Archive manifest binds every prior planning/instruction file; PURCHASE-FLOW-RECONCILIATION.json classifies every current file. Source revisions supply requirements, never commercial/provider/host approval.\n'
    write(P/'SOURCES.md',sources)
    matrix=header(P/'SOURCE-MATRIX.md','SHB source-to-requirement map')+'| Criterion | Source section(s) | Primary phase | Evidence |\n|---|---|---|---|\n'
    sectionmap={1:'2–3',2:'1.3,7,12',3:'2,4',4:'2,5',5:'2,3,8',6:'3',7:'4,9',8:'5.3',9:'5',10:'6–7',11:'6',12:'6.2',13:'6.3',14:'6.3–6.5',15:'8',16:'8.2',17:'8.3',18:'8.2–8.3',19:'9.1',20:'9',21:'9.1',22:'5.3,6.5',23:'9.1–9.2',24:'1.2,9.3',25:'9.4',26:'6.5,9.3',27:'3,12–13',28:'13,14.2',29:'14.1',30:'14.2'}
    for ident in SCENARIOS:matrix+=f'| SHB-{ident:02d} | {sectionmap[ident]} / §13 | {PRIMARY[ident]} | Pending revised execution; prior evidence retained with exact scope |\n'
    write(P/'SOURCE-MATRIX.md',matrix)
    write(P/'PURCHASE-FLOW-AMENDMENT.md',header(P/'PURCHASE-FLOW-AMENDMENT.md','Current purchase flow — SHB revision 1.1')+'This existing entry point now routes to the 30 October SHB revision. Previous final26October platform/IP/staged-delivery purchase requirements are superseded for future SHB sales; their original bytes are archived. One SHB product, two variants, invitations/private static delivery, scoped discounts, automatic eligible FPGA and reviewed ASIC offers.\n\n'+MANUAL+'\n\nUse REQUIREMENTS.md and ROADMAP.md for all thirty cases. Rate/currency/tax/legal/ASIC-policy/provider approvals stay pending in the single support-offer record, docs/decisions.md. Shared protection/durability remains binding.\n')
    write(P/'EXECUTION-AMENDMENT-2026-10-22.md',header(P/'EXECUTION-AMENDMENT-2026-10-22.md','Execution policy — consolidated for SHB 1.1')+'Authorized local repository implementation and ordinary isolated tests continue. Proceed with revised 03/04 then 07/08/10; shared foundation/independent release gates remain but do not block unaffected product work. Do not continue the former Phase2 expansion as the immediate task.\n\nContinue substantive work across commits/syncs; ordinary non-force git push origin main after each project commit is authorized and repeatedly reaffirmed. No deployment/provider authority follows from push authorization. Update PROJECT/ROADMAP/STATE/HANDOFF together before every implementation/status commit, regenerate state.json/inventory and run scripts/check_planning.py and scripts/check_purchase_plan.py. Counts are retained records, never engineering-effort percentages.\n\nThe user will supply commercial inputs later; continue unaffected local work without repeating the request. Explicit synthetic fixtures never become live approval. Reuse completed tests/evidence without repeating unchanged expensive qualification; no expanding optional rehearsals.\n\nWhen supplied context usage exceeds 90%, run gsd-pause-work at a safe checkpoint, save exact next work/evidence/blockers without secrets and tell the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for resume. No exact percentage is available in this session; do not invent one or claim monitoring. Preserve a proactive handoff only when real context pressure is apparent or user requests pause.\n\n'+PROTECTION+'\n')
    for phase,directory in dirs.items():
        path=directory/f'{phase:02d}-CONTEXT.md'
        write(path,header(path,PHASES[phase][0]+' — current context')+PHASES[phase][1]+'\n\n<decisions>\nSHB 1.1 is the current product scope. Retain this phase/folder/task identity for history.\n'+MANUAL+'\n'+PROTECTION+'\n</decisions>\n\nAcceptance: '+PHASES[phase][2]+'\n')
    for name,text in {'ARCHITECTURE.md':'Static Astro generates a private release snapshot; Django authorizes storefront and APIs, isolated gateway serves manifest-approved files only. React enhances the same form/backend. PostgreSQL and one leased worker retain durable commerce; invitations, ASIC offers and coupons reuse established access/order/quote/payment primitives. No request-time Node and no public static-origin bypass.', 'STACK.md':'Retain exact pinned Astro/React/Node build graph, Python/Django LTS/Gunicorn/Psycopg, PostgreSQL, NixOS/rootless Podman/Quadlet and internal Caddy. No new platform/dependency pin. Current package/native/licence/OCI/CI and independent runtime qualification remains incomplete for its exact scope.', 'FEATURES.md':PHASES[3][1]+' '+PHASES[4][1]+' '+PHASES[7][1]+' '+PHASES[10][1], 'PITFALLS.md':'Protect static origins as well as API routes. Reusable invitation GET is not a purchase or mailbox identity. Six calendar months is not 180 days. Form email does not replace company authority. Reserve coupons once on PostgreSQL; keep ASIC claim through delayed review. Reconcile uncertain money before releasing claims. No online time ledger or usage-email release dependencies.', 'SUMMARY.md':'Proceed with product/forms → invitation/private delivery → FPGA/ASIC/coupon/order/payment/transaction notices → revised focused verification and separately qualified activation. Reuse existing components and preserve old evidence; no second master plan.'}.items():
        path=P/'research'/name;write(path,header(path,'SHB '+name.removesuffix('.md').lower())+text+'\n\n'+MANUAL+'\n')
    ui=dirs[7]/'07-UI-SPEC.md'
    write(ui,header(ui,'SHB interface contract')+'Preserve the existing green/cream shared shop style, clear labels, keyboard focus, accessible errors and narrow-screen reflow. One product heading and exact two variant labels. Quantity default1; positive whole bundles; current-order hours only. Common fields: company name, billing address/country, company phone, contact full name/phone/email; Same as company phone. Conditional tax, separate purchase-term acceptance/privacy acknowledgement, optional coupon Apply/Remove. ASIC help description required, known IP/project reused; optional stage/process/tools/timing with unknown/no-deadline allowed. FPGA Checkout; ASIC Submit Request then accepted approved offer Checkout. Show approved rate/subtotal/discount/tax/final total or honest unavailable/estimate text. No balance/history/bundle panel, uploads, licence/board/host/volume questionnaire or IP teaser. Private Astro/React enhancement and Django no-JS use one backend.\n')
    tracker=dirs[2]/'02-COMPLETION-TRACKER.md'
    write(tracker,header(tracker,'Shared foundation/release requirements retained')+'Phase2 retains eight historical local summaries out of eighteen physical plan records. No FULL_PASS/INVENTORY_PASS or parent SUMMARY. Previous current step policy issuance/isolated transport/all-write/migration/bootstrap/replica remains unfinished and gates production/bank-sandbox DB use; SHB catalog/forms proceed independently.\n\n'+PROTECTION+'\n\nBUILD-01–08 remain fully applicable: exact reproducibility/locks; actual artifact/transitive/native/source/helper/backup licences/SBOM and attributable review; isolated synthetic contracts; immutable rootless lifecycle; positive database identity/all-write; aggregate resource and storage/snapshot accounting; full activation-impact review. Original detailed task/criteria bytes are retained in each unfinished 02-PLAN and docs/archive. Native57/53/168/SBOM, four OCI/NAR, SQL236/source7/5/deployment16/31 evidence retains its dated local scope; do not repeat unchanged builds or infer independent approval.\n\nDedicated IP/time-ledger tests are outside SHB launch; shared transaction/security/worker/financial/recovery tests remain.\n')
    write(dirs[13]/'13-QUALIFICATION-REGISTER.md',header(dirs[13]/'13-QUALIFICATION-REGISTER.md','SHB qualification register')+'Use all SHB-01–30 in REQUIREMENTS.md; current revised product evidence is pending. Required local lanes: catalog/forms, invitation/private routes, minimum no-JS/React UI, assigned recent-MFA ASIC review, PostgreSQL coupons/orders/payment races, outbox transaction mail and restore/replay. Full release additionally retains exact shared BUILD/host/independent/runtime/recovery/legal/CI and human gates. Legacy IP/licence/package/time-ledger/task-usage-email cases are historical/deferred, not launch blockers.\n\nOne concise external-input register: docs/decisions.md. No new rehearsal feature or repeated unchanged audit merely to add coverage.\n')
    write(P/'ACTIVITY-LOG.md',header(P/'ACTIVITY-LOG.md','Implementation activity — SHB revision 1.1')+'Current STATE.md / ROADMAP.md govern routing. On 2026-10-30 the user explicitly stopped previous-proposal work and adopted the complete SHB 1.1 revision. Exact prior activity and all other planning originals are preserved in docs/archive/2026-10-30-before-shb/manifest.json. Replan registered; product execution and tests follow. No new local/product/live acceptance result is claimed here.\n')
    write(P/'REPLAN-VERIFICATION.md',header(P/'REPLAN-VERIFICATION.md','SHB replan verification')+'The complete source was read, fingerprinted and applied by explicit user instruction. All prior planning artifacts are archived with SHA256/length readback; every current artifact has a release/disposition. Stable phases/tasks retained; dedicated IP/time-ledger work deferred; thirty SHB acceptance cases mapped; shared external/recovery/financial/host controls preserved. Run scripts/check_purchase_plan.py and scripts/check_planning.py before recording verification results. This document alone is not a passing test result.\n')
    # Rewrite the active external instruction entry points as part of the same amendment.
    write(ROOT/'AGENTS.md','''# AGENTS.md — SLL Supporting Hours Bundle Shop

Current user-authorized product plan: [SHB revision 1.1](014-Shop-SHB-Proposal-Revision-2026-10-30.md), read fully including Appendix A. It supersedes conflicting earlier storefront/IP/time-ledger requirements. Existing .planning/PROJECT.md, REQUIREMENTS.md, ROADMAP.md and STATE.md are the operative plan; stable old phase/folder IDs are retained for history. Historical originals are in docs/archive/2026-10-30-before-shb; their next actions are not active instructions.

## Product

Invitation-only shop at https://shop.xspi.pro. One visible product **Supporting Hours Bundle**; exactly **FPGA Supporting Hours Bundle** (10 hours, automatic eligible Checkout) and **ASIC Supporting Hours Bundle** (25 hours, Submit Request then reviewed matching offer/acceptance/payment). Positive whole-bundle quantity, authoritative price/hours, minimum company/billing/contact form and optional scoped percentage code. New IP sales/routes are disabled; preserve prior code/history/accepted obligations. No new licence/board/host/production questionnaire or technical uploads.

'''+MANUAL+'''

## Architecture, privacy and money

Retain static Astro Content Collections + selected React islands; Django LTS/Gunicorn, PostgreSQL and one leased durable worker. No request-time Astro/Node, mandatory Redis/Celery/CMS/IdP or replacement platform. Markdown/YAML approved versioned catalog; unknown live price/currency/tax/terms/policy remains null and disables only the affected live action. One versioned support-offer approval record in docs/decisions.md; no invented adoption, approver, compatibility, legal/provider guarantee or automatic paid fallback.

Six-calendar-month invitations in Asia/Tbilisi (month-end clamp; UTC instant; now < expiry), 32 random-byte digest-only reusable bearers, no commercial effects from GET. Retain shorter 30-minute sessions capped by invitation and current-state expiry/revocation checks. No raw bearer in logs/referrers/normal DB records/bank URLs/browser persistence. Invitations authorize new offers/purchases only; no private history/prefill or proof of named identity. Preserve verified resource access and staff MFA/recent verification on every privileged route. Form-entered contact never becomes company authorization.

Protect static HTML/catalog/prices/assets behind server access control; private release storage with manifest-approved service delivery. No public bucket/alternate hostname/old route/preview/source-map bypass. No-store protected responses, host-only secure HTTP-only cookies and CSRF/origin controls. Authenticated bank reconciliation continues after invite expiry; preserve accepted prices/offer/order identity and archive-before-effects. Uncertain operations never authorize a blind retry. No synthetic record becomes real money/approval.

## Infrastructure and release gates

'''+PROTECTION+'''

## GSD workflow and continuation

Before file edits start through gsd-fast (trivial), gsd-quick (ad hoc), gsd-debug or gsd-execute-phase (planned), unless the user explicitly bypasses. Keep PROJECT/STATE/ROADMAP/HANDOFF and state.json synchronized before implementation/status commits; refresh planning inventory and run scripts/check_planning.py and scripts/check_purchase_plan.py. Completion counts are records, not engineering effort. User authorizes continued local implementation and ordinary isolated tests; deployment and every external operation retain scoped gates.

Continue across commits/syncs without stopping after each small task; ordinary non-force push to origin/main after each project commit is already authorized. Company inputs will arrive later; do not repeatedly request them. Continue unaffected local work with explicit synthetic fixtures. No new subagent request exists; execute inline.

When context usage supplied by the session exceeds90%, run gsd-pause-work at a safe checkpoint, saving exact completed/remaining tasks, evidence, blockers and next action without secrets. Tell the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for resumed/cleared session. If no exact percentage is supplied, do not invent one or claim automatic monitoring; save proactively only when actual context pressure is apparent and state the limitation. The user's standing conditional pause authorization remains.

Credentials: consult only needed authorized entries in .env without printing/copying secrets; no automatic .env loading. Missing needed entries may be added empty with purpose and the user asked to fill them in the file, never chat. Credentials do not grant resource/action authority. Current local work needs no real credentials. Leave unrelated http_cache.sqlite untouched.
''')
    write(ROOT/'README.md','# SLL Supporting Hours Bundle Shop\n\nCurrent plan: [30 October SHB revision1.1]('+SOURCE+') and [.planning/ROADMAP.md](.planning/ROADMAP.md); current implementation and pending gates: [.planning/STATE.md](.planning/STATE.md). One invitation-only product, 10-hour FPGA Checkout and 25-hour ASIC request/review/offer. Support usage and task emails are manual outside the shop; orders retain hours purchased only. New IP sales are deferred.\n\nHistorical sources/evidence and old contracts remain preserved. Rates, policies, selected bank/mail and actual protected-host/independent qualification remain pending; synthetic local work is not live approval. Local SHB commands/results will be maintained in [docs/purchase-flow.md](docs/purchase-flow.md).\n')
    decisions='# SHB support-offer and external-operation decision record\n\nRevision1.1 replaces future IP-sale/time-ledger requirements. This is the one consolidated support-offer record; no actual commercial values/approver/date/evidence have been supplied. Preserve original P-01–P-12 decision history at docs/archive/2026-10-30-before-shb/docs/decisions.md. IP-only rights/host/production/package decisions are deferred and do not block support-alone implementation.\n\n| Applicable existing reference | Pending input | Affected live action |\n|---|---|---|\n| P-02/P-05 | FPGA/ASIC hourly rates (ASIC higher), currency, approved discount policy/defaults, real approver/date/scope/evidence | Payable offer, real discount issue/payment for affected variant |\n| P-05/P-08 | Final SHB/refund/privacy/ASIC supplement, ASIC no-expiry adoption, separate manual FPGA/ASIC scope, ordinary manual time-charging unit/minimum/rounding | Relevant live intake/offer/sale; unusual tool/multi-engineer charges unavailable absent agreement |\n| P-08 | Seller/invoice identity, tax/territory/compliance/acceptance rules | Affected actual transaction |\n| P-01/P-12 | Customer/SLL-IP eligibility, authorized contacts and assigned technical reviewers | Automatic FPGA invitation or ASIC offer approval |\n| P-07 | Selected-bank documented capabilities/merchant/currency/min/max/deadlines and scoped sandbox/production authority | Actual bank integration/charge/refund |\n| P-09/P-10/P-11/P-12 | Qualified private release/backup custody, existing mail route, independent runner, host inventory/allowlist/impact and complete unchanged ingress/cert lifecycle | Actual recovery/deployment/mail/public activation with separate exact resource/action authority |\n\nThe 30-day new coupon claim window and14-day ASIC offer validity are proposed defaults, not commercial approval; each issued policy/offer records its actual adopted deadline. Existing30-minute browser session maximum is retained, capped by invitation expiry. ASIC initial feasibility is proposed uncharged pre-sales administration; no paid investigation without agreement. No recommendation becomes an actual fact or guarantee. FPGA no-expiry comes from Appendix A; invitation expiry does not cancel purchases.\n\nUnusual work charges depend on agreement before that work, not an extra shop workflow. Manual support tasks/balances/emails are the support team responsibility, not release software gates. Local catalog/forms/invitation/coupon/payment implementation continues with explicit synthetic configuration. User will supply company inputs later; do not repeat requests.\n\n'+PROTECTION+'\n'
    write(ROOT/'docs/decisions.md',decisions)
    write(ROOT/'docs/purchase-flow.md','# Supporting Hours Bundle — current local implementation\n\nCurrent authority: [SHB revision1.1](../'+SOURCE+'). Active plan and exact current position: [STATE](../.planning/STATE.md) / [ROADMAP](../.planning/ROADMAP.md). Previous IP/staged-delivery/time-ledger demonstration instructions are historical at docs/archive/2026-10-30-before-shb/docs/purchase-flow.md.\n\nImplement the one-product/two-variant batch and record executed commands/results here. Local SHB demo is not yet implemented or verified. Do not use previous IP purchase rehearsals as SHB acceptance. Live commercial/provider/deployment inputs remain pending in decisions.md.\n')
    print(f'SHB_REPLAN_WRITTEN archived_files={len(before)} source_sha256={DIGEST}; verification pending')


if __name__=='__main__':
    import sys
    if sys.argv[1:]!=['--apply']:
        raise SystemExit('One-time scope amendment only: replan_shb.py --apply')
    main()

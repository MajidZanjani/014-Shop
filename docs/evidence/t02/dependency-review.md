# T02 direct-artifact review — awaiting human response

Candidate-set SHA-256: `136610b07612762d390b3b3c234ff1ef3f6dc6b0e44a69a2abc646d9106b51bd`

No downloaded code was executed or installed. No candidate is tested compatible. SUS is a research heuristic, not compromise evidence.
Full licence texts and hook commands are in the JSON. Hash consistency is not signer verification.

| Package | Version | Research heuristic | SHA-256 | Upstream / release / artifact | Hooks / licences |
|---|---|---|---|---|---|
| astro | 7.4.1 | SUS: too-new | `56d48cb846424b9de7880bb035218d42f83f25326f0592169204a5e412084b47` | [upstream](https://github.com/withastro/astro) / [release/security](https://docs.astro.build/en/guides/upgrade-to/v7/) / [artifact](https://registry.npmjs.org/astro/-/astro-7.4.1.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| @astrojs/react | 7.1.0 | SUS: too-new | `f53762632de00083da52938f1103e07cd912f6e0bf8c778b38cdf91d701dd944` | [upstream](https://github.com/withastro/astro) / [release/security](https://docs.astro.build/en/guides/integrations-guide/react/) / [artifact](https://registry.npmjs.org/@astrojs/react/-/react-7.1.0.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| react | 19.3.1 | SUS: too-new | `56936913918dcf1f7a6fe58784e79df54b18200a88655ce809cf5e9c4ef871aa` | [upstream](https://github.com/react/react) / [release/security](https://react.dev/versions) / [artifact](https://registry.npmjs.org/react/-/react-19.3.1.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| react-dom | 19.3.1 | SUS: too-new | `8b49975821eec6311e00d2b3f4b8337923253c876517388a33f9839c61ab262e` | [upstream](https://github.com/react/react) / [release/security](https://react.dev/versions) / [artifact](https://registry.npmjs.org/react-dom/-/react-dom-19.3.1.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| @astrojs/check | 0.9.11 | SUS: too-new | `75ef65165434deb4e2825541a19861b552741506ef4678c8956af8faabfde513` | [upstream](https://github.com/withastro/astro) / [release/security](https://docs.astro.build/en/reference/cli-reference/) / [artifact](https://registry.npmjs.org/@astrojs/check/-/check-0.9.11.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| typescript | 6.0.3 | OK; latest 7 excluded by checker peer | `33cd0ee1beaa8c9e9d15a9da836c62ddea4c34a42d7c2d349dbc80d94165d22a` | [upstream](https://github.com/microsoft/TypeScript) / [release/security](https://www.typescriptlang.org/download/) / [artifact](https://registry.npmjs.org/typescript/-/typescript-6.0.3.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| @types/react | 19.3.0 | OK | `ffa77ffdbdc82e5f67a0fd74d750990375a7dfd8685ec7f10a27c0db128f7766` | [upstream](https://github.com/DefinitelyTyped/DefinitelyTyped) / [release/security](https://github.com/DefinitelyTyped/DefinitelyTyped) / [artifact](https://registry.npmjs.org/@types/react/-/react-19.3.0.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| @types/react-dom | 19.3.0 | OK | `0782e1cd4af4a6a030843235a48e55dc690c36f9428b0b672dc53350806dcf21` | [upstream](https://github.com/DefinitelyTyped/DefinitelyTyped) / [release/security](https://github.com/DefinitelyTyped/DefinitelyTyped) / [artifact](https://registry.npmjs.org/@types/react-dom/-/react-dom-19.3.0.tgz) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| npm | 11.19.1 | Bootstrap: bundled Node installer version | `9f58bff01604cb1b14008fef14dceb14d836a49225e45c6c2e37de3be3e707f0` | [upstream](https://github.com/npm/cli) / [release/security](https://github.com/npm/cli/releases/tag/v11.19.1) / [artifact](https://registry.npmjs.org/npm/-/npm-11.19.1.tgz) | lifecycle: prepack; build files: 1; licence texts: 148 |
| Django | 5.2.18 | SUS: too-new, unknown-downloads | `92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c` | [upstream](https://github.com/django/django) / [release/security](https://docs.djangoproject.com/en/5.2/releases/5.2.18/) / [artifact](https://files.pythonhosted.org/packages/d6/01/6568ec52b26548ca1b83d33249f7274db3bf74698f42c0da42ec9db1a24a/django-5.2.18-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 10 |
| gunicorn | 26.2.0 | SUS: unknown-downloads | `bd249d0b3f7972f7432f0a6b6ff3b3ee2d129f70cd1ff6c09a9dd9e29a2b88e3` | [upstream](https://github.com/benoitc/gunicorn) / [release/security](https://gunicorn.org/news/) / [artifact](https://files.pythonhosted.org/packages/fe/85/7522a52e5e2f42faf1a129113ab63e548c42e103e9af395b7bfe65e403e2/gunicorn-26.2.0-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| psycopg | 3.3.6 | SUS: unknown-downloads | `a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631` | [upstream](https://github.com/psycopg/psycopg) / [release/security](https://www.psycopg.org/psycopg3/docs/news.html) / [artifact](https://files.pythonhosted.org/packages/4e/de/748bd7609c71cae5d737f0ba9192f19329f70180ecda8fff3cac02c5abe3/psycopg-3.3.6-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| pip | 26.2.1 | Bootstrap: no pip execution | `71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e` | [upstream](https://github.com/pypa/pip) / [release/security](https://pip.pypa.io/en/stable/news/) / [artifact](https://files.pythonhosted.org/packages/f3/6e/1736e5b4ae2b778ef2f81c47d797de9f891d4d8acb047a24ca37a60294dd/pip-26.2.1-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 41 |
| pip-tools | 7.6.2 | SUS: too-new, unknown-downloads, no-repository (heuristic missed lowercase metadata) | `f37eb4b736859c2c30230e50977312c61918b7ef931071ff7811fd067715c25f` | [upstream](https://github.com/jazzband/pip-tools) / [release/security](https://github.com/jazzband/pip-tools/releases) / [artifact](https://files.pythonhosted.org/packages/4b/68/f3bd09c53ed3159bb1349e1d5859ad1ea7755b8e4cd50174290e9e8cbb47/pip_tools-7.6.2-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| jsonschema | 4.26.0 | SUS: unknown-downloads | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` | [upstream](https://github.com/python-jsonschema/jsonschema) / [release/security](https://github.com/python-jsonschema/jsonschema/blob/main/CHANGELOG.rst) / [artifact](https://files.pythonhosted.org/packages/69/90/f63fb5873511e014207a475e2bb4e8b2e570d655b00ac19a9a0ca0a385ee/jsonschema-4.26.0-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 1 |
| cyclonedx-bom | 7.5.0 | SUS: too-new, unknown-downloads | `a3020e225107214a66cb9c79ae83e3a71640a06d4ff3a0e2f9cb0d238f7061fd` | [upstream](https://github.com/CycloneDX/cyclonedx-python) / [release/security](https://github.com/CycloneDX/cyclonedx-python/releases) / [artifact](https://files.pythonhosted.org/packages/39/f6/4da2674038e1558b93872dc6a3d10172be60db05c5ca9a5e5de73b3edd7e/cyclonedx_bom-7.5.0-py3-none-any.whl) | lifecycle: none in direct manifest; build files: 0; licence texts: 3 |
| node | 24.22.0 | Native runtime source; build qualification pending | `41f97cff2c666f1f8293dc5f85c65e8dd605c16b43fd9febd49ede32ee1e0329` | [upstream](https://github.com/nodejs/node) / [release/security](https://nodejs.org/en/blog/release/v24.22.0) / [artifact](https://nodejs.org/dist/v24.22.0/node-v24.22.0.tar.xz) | lifecycle: none in direct manifest; build files: 18; licence texts: 233 |
| python | 3.13.16 | Native runtime source; build qualification pending | `f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d` | [upstream](https://github.com/python/cpython) / [release/security](https://www.python.org/downloads/release/python-31316/) / [artifact](https://www.python.org/ftp/python/3.13.16/Python-3.13.16.tar.xz) | lifecycle: none in direct manifest; build files: 13; licence texts: 6 |
| postgresql | 18.6 | Native runtime source; build qualification pending | `555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f` | [upstream](https://github.com/postgres/postgres) / [release/security](https://www.postgresql.org/docs/current/release-18-6.html) / [artifact](https://ftp.postgresql.org/pub/source/v18.6/postgresql-18.6.tar.bz2) | lifecycle: none in direct manifest; build files: 290; licence texts: 3 |
| libpq | 18.6 | Native runtime source; build qualification pending | `555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f` | [upstream](https://github.com/postgres/postgres) / [release/security](https://www.postgresql.org/docs/current/release-18-6.html) / [artifact](https://ftp.postgresql.org/pub/source/v18.6/postgresql-18.6.tar.bz2) | lifecycle: none in direct manifest; build files: 290; licence texts: 3 |

## Declared range observations

- astro: optional peer @astrojs/markdown-remark absent; transitive resolution pending
- astro: npm 11.19.1 satisfies declared >=9.6.5
- astro: node 24.22.0 satisfies declared >=22.22.0
- @astrojs/react: react 19.3.1 satisfies declared ^17.0.2 || ^18.0.0 || ^19.0.0
- @astrojs/react: react-dom 19.3.1 satisfies declared ^17.0.2 || ^18.0.0 || ^19.0.0
- @astrojs/react: @types/react 19.3.0 satisfies declared ^17.0.50 || ^18.0.21 || ^19.0.0
- @astrojs/react: @types/react-dom 19.3.0 satisfies declared ^17.0.17 || ^18.0.6 || ^19.0.0
- @astrojs/react: optional peer oxc-transform-react absent; transitive resolution pending
- @astrojs/react: node 24.22.0 satisfies declared >=22.22.0
- react: node 24.22.0 satisfies declared >=0.10.0
- react-dom: react 19.3.1 satisfies declared ^19.3.1
- @astrojs/check: typescript 6.0.3 satisfies declared ^5.0.0 || ^6.0.0
- typescript: node 24.22.0 satisfies declared >=14.17
- @types/react-dom: @types/react 19.3.0 satisfies declared ^19.3.0
- npm: node 24.22.0 satisfies declared ^20.17.0 || >=22.9.0
- Django: Python 3.13.16 satisfies declared >=3.10
- gunicorn: Python 3.13.16 satisfies declared >=3.10
- psycopg: Python 3.13.16 satisfies declared >=3.10
- pip: Python 3.13.16 satisfies declared >=3.10
- pip-tools: Python 3.13.16 satisfies declared >=3.9
- jsonschema: Python 3.13.16 satisfies declared >=3.10
- cyclonedx-bom: Python 3.13.16 satisfies declared <4,>=3.9

## Decisions and unresolved findings

- TypeScript 6.0.3 selected: checker 0.9.11 declares ^5.0.0 || ^6.0.0; latest 7.0.2 excluded.
- Node 24.22.0 bundles npm 11.19.1. Python 3.13.16, pip and pip-tools are explicit bootstrap candidates; no downloaded bootstrap executed.
- PostgreSQL/libpq share official 18.6 source bytes; Psycopg uses system libpq, no binary bundle.
- Signer authenticity, native closure, complete transitive hashes/hooks/licences/SBOM and runtime/build tests remain pending producing-plan obligations.
- Optional absent peers are reported; no peer conflicts suppressed. pnpm is not selected.
- Release/security links were fetched and hashed, not an assertion that all advisories are resolved. Legal assessment remains pending.

- astro: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- @astrojs/react: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- react: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- react-dom: REGISTRY/ARCHIVE SCRIPT DISCREPANCY: compare registry_scripts with hooks.archive_scripts; unresolved human review finding; Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- @astrojs/check: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- typescript: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- @types/react: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- @types/react-dom: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- npm: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- Django: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim; Release assessment: Official 5.2.18 notes describe language-cache and header-parser denial-of-service fixes, spatial-byte request forgery mitigation and editable-primary-key formset privilege fixes. Later application regression tests remain required.
- gunicorn: Not installed, built or tested compatible; inspect hooks before use; Registry Python >=3.10 vs docs Python 3.12+; selected 3.13 meets both; runtime tests pending; Release/security page captured by hash; no vulnerability-free or legal approval claim
- psycopg: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- pip: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- pip-tools: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- jsonschema: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- cyclonedx-bom: Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim
- node: Source artifact; native build/closure identity remains producing-plan work; Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim; Release assessment: Official release dated 2026-10-14 labels 24.22.0 Krypton LTS; release includes crypto API and runtime fixes. Index lists bundled npm 11.19.1. This is release provenance, not a security clearance.
- python: Source artifact; native build/closure identity remains producing-plan work; Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim; Release assessment: Official 3.13.16 release page publishes SHA-256 f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d for selected XZ source; downloaded bytes match. Signatures not verified.
- postgresql: Source artifact; native build/closure identity remains producing-plan work; Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim; Release assessment: Official 18.6 notes say 18.5 was never released and identify output-plugin restriction and pgcrypto cipher-failure fixes. Existing databases may require configuration/data cleanup; none is operated here.
- libpq: Source artifact; native build/closure identity remains producing-plan work; Not installed, built or tested compatible; inspect hooks before use; Release/security page captured by hash; no vulnerability-free or legal approval claim; Release assessment: Same official PostgreSQL 18.6 source archive; installed libpq/OpenSSL build identity and client smoke tests remain pending.

## Human gate

Review this exact digest, JSON hook commands/licence texts and upstream release links. Supply attributable explicit approval of the digest or concrete changes. human_response remains null. No bank, cloud, commercial or operational approval is implied.

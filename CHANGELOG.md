# Changelog

## 1.0.0 (2026-08-03)


### 🚀 Features

* add opt-in integrations, PR docs previews, and docs linting ([30b1531](https://github.com/hasansezertasan/copier-pyproject/commit/30b1531a04cac69983c0b9eea400e43a032004ef))
* adopt ensure-dunder-all and cache settings/logger accessors ([#113](https://github.com/hasansezertasan/copier-pyproject/issues/113)) ([ba23412](https://github.com/hasansezertasan/copier-pyproject/commit/ba23412012937c0d0b6847277174aa3db7e912c8))
* **config:** Add configuration files for Docker, VSCode, and linting tools ([#6](https://github.com/hasansezertasan/copier-pyproject/issues/6)) ([2b9855d](https://github.com/hasansezertasan/copier-pyproject/commit/2b9855dda2e2e65bf2aa274743df7e9c32f7e5e5))
* **copier:** use copier ([#2](https://github.com/hasansezertasan/copier-pyproject/issues/2)) ([c8d87c3](https://github.com/hasansezertasan/copier-pyproject/commit/c8d87c39ddd664793f38bbdfee9601b91b0edfc1))
* enforce architecture contracts with import-linter ([#104](https://github.com/hasansezertasan/copier-pyproject/issues/104)) ([eff53e5](https://github.com/hasansezertasan/copier-pyproject/commit/eff53e591ffd5a7694fc800a08cce218ac8f7990))
* gate MegaLinter behind include_megalinter as a lean complement ([#99](https://github.com/hasansezertasan/copier-pyproject/issues/99)) ([720a77b](https://github.com/hasansezertasan/copier-pyproject/commit/720a77b24a619a4d107e557718326a031f9c4ae5))
* **gui-script:** Add GUI launcher and associated tests ([#7](https://github.com/hasansezertasan/copier-pyproject/issues/7)) ([73a9cfc](https://github.com/hasansezertasan/copier-pyproject/commit/73a9cfc97dd34527eca1d28d93b0baae670b7bde))
* **init:** initialize project ([5917233](https://github.com/hasansezertasan/copier-pyproject/commit/5917233dfb26b30920ce1cb235d2253518bc3f77))
* manage .gitignore with cobo (LF-sealed, drift-checked) ([#97](https://github.com/hasansezertasan/copier-pyproject/issues/97)) ([cbf0b35](https://github.com/hasansezertasan/copier-pyproject/commit/cbf0b3565a8cad39899fcf9eca13ef8480a48353))
* provision repository labels (incl. no-issue) via label sync ([#92](https://github.com/hasansezertasan/copier-pyproject/issues/92)) ([7819562](https://github.com/hasansezertasan/copier-pyproject/commit/7819562fb48266f783906aaa0de5739f5e854cae))
* replace stefanzweifel integration with MegaLinter CI layer ([#83](https://github.com/hasansezertasan/copier-pyproject/issues/83)) ([6e3bba3](https://github.com/hasansezertasan/copier-pyproject/commit/6e3bba31e8180a093a90c8cf565a0faa77b97b9e))
* template self-versioning and downstream copier update automation ([#110](https://github.com/hasansezertasan/copier-pyproject/issues/110)) ([3b9f548](https://github.com/hasansezertasan/copier-pyproject/commit/3b9f5483de4b47f94469dee0ef282f250788e829))
* **template:** add active security scanning workflow + release SBOM ([#60](https://github.com/hasansezertasan/copier-pyproject/issues/60)) ([085489c](https://github.com/hasansezertasan/copier-pyproject/commit/085489c9c2e0da572aeee2752ae769cc859510af))
* **template:** add community-health files and harden generated-project prek ([#54](https://github.com/hasansezertasan/copier-pyproject/issues/54)) ([4c5c0e9](https://github.com/hasansezertasan/copier-pyproject/commit/4c5c0e9bc4607998e9dcc020623a3f77b76ad63d))
* **template:** add editorconfig-checker and ghalint, harden CI workflows ([#62](https://github.com/hasansezertasan/copier-pyproject/issues/62)) ([c1c39b1](https://github.com/hasansezertasan/copier-pyproject/commit/c1c39b1d950fc0f3fb86ab45745d8f0db4514bce))
* **template:** add package_keywords prompt for custom PyPI keywords ([#36](https://github.com/hasansezertasan/copier-pyproject/issues/36)) ([75f39e5](https://github.com/hasansezertasan/copier-pyproject/commit/75f39e5e64b9568dbe45859dbdf7f3b0f0fe9dfa))
* **template:** add PR task-list completion check ([#32](https://github.com/hasansezertasan/copier-pyproject/issues/32)) ([0fdb7aa](https://github.com/hasansezertasan/copier-pyproject/commit/0fdb7aa556386c431fcc9746b1e8ec5eca19bb69))
* **template:** add real-broker worker integration tests ([#49](https://github.com/hasansezertasan/copier-pyproject/issues/49)) ([97f02e4](https://github.com/hasansezertasan/copier-pyproject/commit/97f02e492168834e74890d1d7be7e3193672f752))
* **template:** document remaining one-time setup, soften Codecov gate, fix freezer spec ([#53](https://github.com/hasansezertasan/copier-pyproject/issues/53)) ([5e7f288](https://github.com/hasansezertasan/copier-pyproject/commit/5e7f2885e2d609cb4bd564dded188d7b3afab842))
* **template:** enforce conventional branch names on pull requests ([#35](https://github.com/hasansezertasan/copier-pyproject/issues/35)) ([1024875](https://github.com/hasansezertasan/copier-pyproject/commit/1024875c20a170986b0760b47effd373dbdaa05f))
* **template:** enforce linked issues on pull requests ([#31](https://github.com/hasansezertasan/copier-pyproject/issues/31)) ([b86842c](https://github.com/hasansezertasan/copier-pyproject/commit/b86842c41921131e99c5c768d081d7a36600a7df))
* **template:** harden the optional Docker Hub publish channel ([#51](https://github.com/hasansezertasan/copier-pyproject/issues/51)) ([f48250e](https://github.com/hasansezertasan/copier-pyproject/commit/f48250ebe8b92c880964e892f7c2fb37471a12c4))
* **template:** replace MkDocs with Sphinx + Shibuya docs ([#42](https://github.com/hasansezertasan/copier-pyproject/issues/42)) ([20eac5b](https://github.com/hasansezertasan/copier-pyproject/commit/20eac5b7294867e62bf320fe4b8c87635c912281))
* **template:** restructure modules into subpackages and add deployment workflows ([#9](https://github.com/hasansezertasan/copier-pyproject/issues/9)) ([656f7d1](https://github.com/hasansezertasan/copier-pyproject/commit/656f7d1f69b0b0d6741e14b91623c635a85e1e16))
* **template:** split standalone-executable toggle into launcher/compiler/freezer ([#43](https://github.com/hasansezertasan/copier-pyproject/issues/43)) ([68e3381](https://github.com/hasansezertasan/copier-pyproject/commit/68e3381538fc1aea55975a4cf39aedb9cc78e57e))
* **template:** standardize metadata files and repo hygiene ([#27](https://github.com/hasansezertasan/copier-pyproject/issues/27)) ([158c6e2](https://github.com/hasansezertasan/copier-pyproject/commit/158c6e270bdbe203065afe5fa4e68cff9dabf69f))
* **tools:** Add configuration files for Codecov, Docker, EditorConfig, and GitHub workflows ([#5](https://github.com/hasansezertasan/copier-pyproject/issues/5)) ([6702ad0](https://github.com/hasansezertasan/copier-pyproject/commit/6702ad0cde765c0ed57ca474e123c7f5e95edaa3))


### 🐛 Bug Fixes

* **ci:** exclude generated CHANGELOG.md from markdown linting ([#90](https://github.com/hasansezertasan/copier-pyproject/issues/90)) ([e3afa95](https://github.com/hasansezertasan/copier-pyproject/commit/e3afa95fb0ea584f9fa86da3e8e4e4574a795bb7))
* **ci:** make tox cli smoke-test the posargs default ([#88](https://github.com/hasansezertasan/copier-pyproject/issues/88)) ([ec85981](https://github.com/hasansezertasan/copier-pyproject/commit/ec859810b52ba10c1b5ab2e3081527d34339d6ed))
* **copier:** escape broken template tags ([#3](https://github.com/hasansezertasan/copier-pyproject/issues/3)) ([9f6f672](https://github.com/hasansezertasan/copier-pyproject/commit/9f6f6723429bd90325e04793e1ca4d29f4cf8fe0))
* **cspell:** escape author-name tokens for YAML safety ([#103](https://github.com/hasansezertasan/copier-pyproject/issues/103)) ([082f641](https://github.com/hasansezertasan/copier-pyproject/commit/082f64164ee1469239fef56563ea6e77d29a9125))
* grant contents:read to the label-sync checkout ([#93](https://github.com/hasansezertasan/copier-pyproject/issues/93)) ([4f432f9](https://github.com/hasansezertasan/copier-pyproject/commit/4f432f947e51ec999f0fbef520fdc21125743aa4))
* green-on-generation for prek taplo formatting and cspell ([#91](https://github.com/hasansezertasan/copier-pyproject/issues/91)) ([bcea922](https://github.com/hasansezertasan/copier-pyproject/commit/bcea9229c809486cd70bee7f9ca48cec74369e5f))
* harden generated projects against CI failures and placeholder rot ([#84](https://github.com/hasansezertasan/copier-pyproject/issues/84)) ([f97c65e](https://github.com/hasansezertasan/copier-pyproject/commit/f97c65e2d541bd54c092da11bb31abe65981a8d1))
* **import:** update import path for the main application CLI ([e144c79](https://github.com/hasansezertasan/copier-pyproject/commit/e144c792026ca138de7afd18ce0dae29cd347cc7))
* **release:** baseline release-please manifest at 0.0.0 ([#86](https://github.com/hasansezertasan/copier-pyproject/issues/86)) ([c254dc8](https://github.com/hasansezertasan/copier-pyproject/commit/c254dc87776aed596e9c0d496e0259182fdf66ea))
* require github_repo_name to be a valid Python package name ([#106](https://github.com/hasansezertasan/copier-pyproject/issues/106)) ([fa854cb](https://github.com/hasansezertasan/copier-pyproject/commit/fa854cb6501dae53adbbda131121eb423fb2f21a))
* resolve lint failures in generated projects ([#101](https://github.com/hasansezertasan/copier-pyproject/issues/101)) ([8922e31](https://github.com/hasansezertasan/copier-pyproject/commit/8922e319280badc805ab28e9010ca8daa6e95d13))
* stop seeding CHANGELOG.md so adoption can't wipe history ([#87](https://github.com/hasansezertasan/copier-pyproject/issues/87)) ([030b1bf](https://github.com/hasansezertasan/copier-pyproject/commit/030b1bfae67cfe2465c1955c8403eea2747c79bf))
* **template:** harden generated devcontainer, tighten repo-name validator, fix docs drift ([#58](https://github.com/hasansezertasan/copier-pyproject/issues/58)) ([f263019](https://github.com/hasansezertasan/copier-pyproject/commit/f263019b3dd706abc7e6750adb42818f52c3d20d))
* **template:** repair broken components, harden workflows, and clean up lint ([#14](https://github.com/hasansezertasan/copier-pyproject/issues/14)) ([899532d](https://github.com/hasansezertasan/copier-pyproject/commit/899532d462114aa8196803bb87409103bd58fa73))
* **tests:** reorder import statement for consistency in test_main.py ([b7c99cd](https://github.com/hasansezertasan/copier-pyproject/commit/b7c99cdac8d381625fc992c76ff6b7a339b8d0b0))
* upload coverage tokenless on public repos ([69aa7f9](https://github.com/hasansezertasan/copier-pyproject/commit/69aa7f9abd0739c3ae32b19ee13e142a7c913177))
* use logger.exception in except handlers ([#114](https://github.com/hasansezertasan/copier-pyproject/issues/114)) ([3f37e71](https://github.com/hasansezertasan/copier-pyproject/commit/3f37e71b8f3c568c9f36064903eecc49bf00d91d))


### ♻️ Refactoring

* rename project from 'theproject' to 'projectname' and update related configurations ([247cd91](https://github.com/hasansezertasan/copier-pyproject/commit/247cd91d5c567d65dedb024fac5e4fb574c9cafc))
* **template:** five strict type checkers and bump style tooling ([#26](https://github.com/hasansezertasan/copier-pyproject/issues/26)) ([1900696](https://github.com/hasansezertasan/copier-pyproject/commit/19006960cca36514a71ee592178268520186ece7))
* **template:** fold build-wheels into cd workflow ([#22](https://github.com/hasansezertasan/copier-pyproject/issues/22)) ([2bab707](https://github.com/hasansezertasan/copier-pyproject/commit/2bab70755af318b9f8013eaafc2363aba365c4b5))
* **template:** overall improvements ([#8](https://github.com/hasansezertasan/copier-pyproject/issues/8)) ([61aedc8](https://github.com/hasansezertasan/copier-pyproject/commit/61aedc873bd255233e40268483d42f893f0000d3))
* **template:** standardize on release-please for release automation ([#23](https://github.com/hasansezertasan/copier-pyproject/issues/23)) ([db1f617](https://github.com/hasansezertasan/copier-pyproject/commit/db1f617c5572a941285a94c4e4ad53b732738442))
* use Renovate's copier manager for template updates ([#118](https://github.com/hasansezertasan/copier-pyproject/issues/118)) ([1eede79](https://github.com/hasansezertasan/copier-pyproject/commit/1eede79ad8db07c0847a2bf449b5ac0c49b7de3c))
* **web:** update project template and dependencies ([#4](https://github.com/hasansezertasan/copier-pyproject/issues/4)) ([777eee1](https://github.com/hasansezertasan/copier-pyproject/commit/777eee13f9f4b742024b8291b544b9d2cddec7f0))


### 📝 Documentation

* fix contradictions and misinformation across template docs ([#24](https://github.com/hasansezertasan/copier-pyproject/issues/24)) ([b53e4ec](https://github.com/hasansezertasan/copier-pyproject/commit/b53e4ecd5f374928b5d243d58ba4006982c584cf))
* **template:** add PyPI Map to README analysis section ([#64](https://github.com/hasansezertasan/copier-pyproject/issues/64)) ([d7538b9](https://github.com/hasansezertasan/copier-pyproject/commit/d7538b9a786db9cf200ad41e561eb047cf3c8072))


### 👷 CI

* adopt zizmor and harden GitHub Actions workflows ([#76](https://github.com/hasansezertasan/copier-pyproject/issues/76)) ([c4ee482](https://github.com/hasansezertasan/copier-pyproject/commit/c4ee4820fb3d3b53a21c205fde8e255f57444ce1))
* correct label-sync trigger comment and serialize runs ([#96](https://github.com/hasansezertasan/copier-pyproject/issues/96)) ([00ce24c](https://github.com/hasansezertasan/copier-pyproject/commit/00ce24c34aaa07633bf226116910e5b65291a5fc))
* key bot-PR gate on PR author and keep the check reporting ([#95](https://github.com/hasansezertasan/copier-pyproject/issues/95)) ([e5331e1](https://github.com/hasansezertasan/copier-pyproject/commit/e5331e14f7dc464ddd30ceab6dbc6d3083c95b2c))
* remove opencode workflow ([#55](https://github.com/hasansezertasan/copier-pyproject/issues/55)) ([88cafe9](https://github.com/hasansezertasan/copier-pyproject/commit/88cafe96cbe85ceb94a47dc97c32c46eb2618c89))
* skip linked-issue and task-list gates for bot PRs ([#94](https://github.com/hasansezertasan/copier-pyproject/issues/94)) ([1276a36](https://github.com/hasansezertasan/copier-pyproject/commit/1276a3602646e9d8105831993a4d2c714ba10d37))

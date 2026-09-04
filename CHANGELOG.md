# Changelog

## [1.3.0](https://github.com/hasansezertasan/copier-pyproject/compare/v1.2.1...v1.3.0) (2026-09-04)


### 🚀 Features

* add a detect-secrets pre-commit gate with a committed baseline ([#236](https://github.com/hasansezertasan/copier-pyproject/issues/236)) ([825f420](https://github.com/hasansezertasan/copier-pyproject/commit/825f420cf4fafcc4444f85b108db84a21b4389e8))
* add per-component, cost-aware CI ([#159](https://github.com/hasansezertasan/copier-pyproject/issues/159), [#160](https://github.com/hasansezertasan/copier-pyproject/issues/160)) ([#259](https://github.com/hasansezertasan/copier-pyproject/issues/259)) ([2cc6a96](https://github.com/hasansezertasan/copier-pyproject/commit/2cc6a96ad98fc9424c969ba4d5fe1db71bf1408c))
* auto-generate the CLI reference from the live Typer app (include_cli) ([#248](https://github.com/hasansezertasan/copier-pyproject/issues/248)) ([19b02f7](https://github.com/hasansezertasan/copier-pyproject/commit/19b02f755e423828bc367cefd87fdfd0718f6a24))
* auto-generate the configuration reference from the pydantic-settings model (include_pydantic_settings) ([#246](https://github.com/hasansezertasan/copier-pyproject/issues/246)) ([50d93b9](https://github.com/hasansezertasan/copier-pyproject/commit/50d93b9505837938c8e0b3ccc131e86a0a3f08b2))
* combine coverage across the CI matrix + optional tokenless HTML host (include_smokeshow) ([#256](https://github.com/hasansezertasan/copier-pyproject/issues/256)) ([46e2b96](https://github.com/hasansezertasan/copier-pyproject/commit/46e2b96ad902240c7fe60180c9f0dfc68a851edf))
* flag unused pytest fixtures with pytest-deadfixtures ([#234](https://github.com/hasansezertasan/copier-pyproject/issues/234)) ([2b25949](https://github.com/hasansezertasan/copier-pyproject/commit/2b259497dad5eb08ad5a4dc306a0549b58181c71))
* harden devcontainer backing services with no-new-privileges ([#228](https://github.com/hasansezertasan/copier-pyproject/issues/228)) ([3c79586](https://github.com/hasansezertasan/copier-pyproject/commit/3c7958630f43165940a2f245cb490e10f5c198ae))
* make the Sphinx docs subsystem optional (include_docs) ([#253](https://github.com/hasansezertasan/copier-pyproject/issues/253)) ([f054e03](https://github.com/hasansezertasan/copier-pyproject/commit/f054e03c6bfdfbdace10b4343ce00b86798bf69c))
* offer GitHub services: containers as a lighter worker-integration path ([#257](https://github.com/hasansezertasan/copier-pyproject/issues/257)) ([374e0cd](https://github.com/hasansezertasan/copier-pyproject/commit/374e0cdce8b52884e46326e842a9d2d5d9dede62))
* publish the web app's OpenAPI schema (include_web) ([#247](https://github.com/hasansezertasan/copier-pyproject/issues/247)) ([f1a9671](https://github.com/hasansezertasan/copier-pyproject/commit/f1a96718665492dc1940a1c6abda6dc6de9e5b33))
* publish the worker's AsyncAPI message-interface schema (include_worker) ([#243](https://github.com/hasansezertasan/copier-pyproject/issues/243)) ([3eaa627](https://github.com/hasansezertasan/copier-pyproject/commit/3eaa627f89bcbba41f75f0ce432ef0e4b5087ad5))
* reproducible docs builds via SOURCE_DATE_EPOCH ([#232](https://github.com/hasansezertasan/copier-pyproject/issues/232)) ([c393e4d](https://github.com/hasansezertasan/copier-pyproject/commit/c393e4d6588fda8f68296657cd1cb35033902d54))
* ship structured issue forms and a PR template ([#235](https://github.com/hasansezertasan/copier-pyproject/issues/235)) ([4fc53ca](https://github.com/hasansezertasan/copier-pyproject/commit/4fc53cae6d3404b21525c149afbd1a34e3c0293d))
* Sphinx build-warning allowlist gate for the docs ([#242](https://github.com/hasansezertasan/copier-pyproject/issues/242)) ([ab6a857](https://github.com/hasansezertasan/copier-pyproject/commit/ab6a8575d401f41fb35ab98a1bf50a2a1ff29fe7))
* treat documentation examples as real, tested code (include_docs) ([#261](https://github.com/hasansezertasan/copier-pyproject/issues/261)) ([ca4c84b](https://github.com/hasansezertasan/copier-pyproject/commit/ca4c84bd28a4d92c0a19e013e9d698dd08829a6d))
* versioned documentation + per-page "last updated" stamps ([#258](https://github.com/hasansezertasan/copier-pyproject/issues/258)) ([effbf80](https://github.com/hasansezertasan/copier-pyproject/commit/effbf80c0838af26cc2f45ed01a83a76ec3bb43f))
* worker probe dev helper + mise task (include_worker) ([#239](https://github.com/hasansezertasan/copier-pyproject/issues/239)) ([dc02db0](https://github.com/hasansezertasan/copier-pyproject/commit/dc02db0540cb232abff15063b82959f85de00eaf))


### 🐛 Bug Fixes

* re-indent pylint disable comment continuations for editorconfig-checker ([#238](https://github.com/hasansezertasan/copier-pyproject/issues/238)) ([b220fc5](https://github.com/hasansezertasan/copier-pyproject/commit/b220fc543c7ec8d4bcfc4bb7639adf6331b5a851))
* stop emitting a stray docs/.rst when include_worker is off ([#250](https://github.com/hasansezertasan/copier-pyproject/issues/250)) ([ff8a48d](https://github.com/hasansezertasan/copier-pyproject/commit/ff8a48d941348556fae20fd83e33b58397da6d83))


### ♻️ Refactoring

* define the worker_broker class/module mapping once via a computed var ([#240](https://github.com/hasansezertasan/copier-pyproject/issues/240)) ([5e4c58a](https://github.com/hasansezertasan/copier-pyproject/commit/5e4c58a7fadf0cfdcf726b10b333cb286f0f0ac7))
* drop the empty `all` extra from generated projects ([#263](https://github.com/hasansezertasan/copier-pyproject/issues/263)) ([95c27c1](https://github.com/hasansezertasan/copier-pyproject/commit/95c27c1ae606a01dcd8e2ac780182a6d71636c0b))
* extract worker destination names into shared constants ([#231](https://github.com/hasansezertasan/copier-pyproject/issues/231)) ([04edfea](https://github.com/hasansezertasan/copier-pyproject/commit/04edfead48d784e4e581c9af1048d9dc66677f3b))


### 📝 Documentation

* add a shared-terminology glossary to CLAUDE.md ([#254](https://github.com/hasansezertasan/copier-pyproject/issues/254)) ([e00c597](https://github.com/hasansezertasan/copier-pyproject/commit/e00c5975d8f2096b97f8d4d8223eada62985bc34))
* enforce Sphinx warnings-as-errors on the HTML build ([#229](https://github.com/hasansezertasan/copier-pyproject/issues/229)) ([ea3e2cf](https://github.com/hasansezertasan/copier-pyproject/commit/ea3e2cf1b943b558aa897eba9e004c662f31a53c))
* gate component-specific CONTRIBUTING.md prose behind include_* toggles ([#230](https://github.com/hasansezertasan/copier-pyproject/issues/230)) ([9eba782](https://github.com/hasansezertasan/copier-pyproject/commit/9eba782577faeeaa8a73d86dd9226e1dc1a6e156))


### 🧪 Tests

* regenerate golden pyproject snapshots to match main ([#249](https://github.com/hasansezertasan/copier-pyproject/issues/249)) ([24f5378](https://github.com/hasansezertasan/copier-pyproject/commit/24f53787b34b9a477bcba73a49d30c59e21cc5dd))
* render-and-inspect suite — YAML/TOML validity + golden files ([#244](https://github.com/hasansezertasan/copier-pyproject/issues/244)) ([121dfd1](https://github.com/hasansezertasan/copier-pyproject/commit/121dfd13a2a32c129fe24553f234c44077b62340))


### 👷 CI

* enforce full prek suite in template CI ([#266](https://github.com/hasansezertasan/copier-pyproject/issues/266)) ([24b796c](https://github.com/hasansezertasan/copier-pyproject/commit/24b796c5b7eca05531a407f1b35869ac82ef7c22))
* **labeler:** add `hotfix` prefix to the `bug` label rule ([#226](https://github.com/hasansezertasan/copier-pyproject/issues/226)) ([49d3cee](https://github.com/hasansezertasan/copier-pyproject/commit/49d3cee58f10e0f6942747b2d41ed294de3c110f))

## [1.2.1](https://github.com/hasansezertasan/copier-pyproject/compare/v1.2.0...v1.2.1) (2026-08-15)


### 🐛 Bug Fixes

* don't log a traceback for the expected missing-metadata CLI error ([#225](https://github.com/hasansezertasan/copier-pyproject/issues/225)) ([8422ef0](https://github.com/hasansezertasan/copier-pyproject/commit/8422ef0401db6d730f1ae6611ddd950c49f5b0c8))
* stop rendering Typer-only docs wiring and wording for argparse CLIs ([#222](https://github.com/hasansezertasan/copier-pyproject/issues/222)) ([45bbe21](https://github.com/hasansezertasan/copier-pyproject/commit/45bbe210750fdc7477275a6ad6f9b1afa3b1fd22))

## [1.2.0](https://github.com/hasansezertasan/copier-pyproject/compare/v1.1.0...v1.2.0) (2026-08-14)


### 🚀 Features

* add setup and update skills, package as copier-pyproject plugin ([#212](https://github.com/hasansezertasan/copier-pyproject/issues/212)) ([7819f01](https://github.com/hasansezertasan/copier-pyproject/commit/7819f01c738165a8ebd052b74a21a406e7f3ea05))
* expose secondary components as CLI subcommands, not separate console scripts ([#206](https://github.com/hasansezertasan/copier-pyproject/issues/206)) ([f59084c](https://github.com/hasansezertasan/copier-pyproject/commit/f59084c9bb9bdeb9a0fb0da00b4c81225692f26d))
* make the CLI framework a choice (cli_framework) ([#207](https://github.com/hasansezertasan/copier-pyproject/issues/207)) ([d1d1952](https://github.com/hasansezertasan/copier-pyproject/commit/d1d195282b1b593463f956c30379e5038c8f4347))
* opt-in repository ruleset as code (include_repo_ruleset) ([#211](https://github.com/hasansezertasan/copier-pyproject/issues/211)) ([a3953c1](https://github.com/hasansezertasan/copier-pyproject/commit/a3953c16135b34bc2eb6eab35edc3819b8c02c0a))
* ship a resume-driven repo-setup skill single-sourced from the setup doc ([#218](https://github.com/hasansezertasan/copier-pyproject/issues/218)) ([d51afff](https://github.com/hasansezertasan/copier-pyproject/commit/d51affff148805f38863cb09aac3bbc21714a1c0))


### 🐛 Bug Fixes

* all-contributors generate rewrites the README badge to a #contributors- anchor the MD051 gate rejects ([#210](https://github.com/hasansezertasan/copier-pyproject/issues/210)) ([521d1c4](https://github.com/hasansezertasan/copier-pyproject/commit/521d1c40b5ef05142d66206ec47f0ca023a8c4ed))
* freeze shipped template pins from Renovate to prevent copier-update conflicts ([#209](https://github.com/hasansezertasan/copier-pyproject/issues/209)) ([55f7acc](https://github.com/hasansezertasan/copier-pyproject/commit/55f7acc5a1e46fb6089083ea8f4ac887503693b5))


### 📝 Documentation

* consolidate maintainer repository setup into one actor-tagged docs home ([#217](https://github.com/hasansezertasan/copier-pyproject/issues/217)) ([920dbbc](https://github.com/hasansezertasan/copier-pyproject/commit/920dbbca2e4ca7c6b30663ff81111bbeaa2dede1))
* de-bloat CLAUDE.md into a lean router over copier.yml help + ADRs ([#219](https://github.com/hasansezertasan/copier-pyproject/issues/219)) ([81147cb](https://github.com/hasansezertasan/copier-pyproject/commit/81147cb653c9e5d5a4c49fcde91695c8f73f56c3))

## [1.1.0](https://github.com/hasansezertasan/copier-pyproject/compare/v1.0.0...v1.1.0) (2026-08-07)


### 🚀 Features

* add always-on pylint quality gate ([#132](https://github.com/hasansezertasan/copier-pyproject/issues/132)) ([e4e0bcb](https://github.com/hasansezertasan/copier-pyproject/commit/e4e0bcb8ad93754cd4209ab13bdddf0916a0a735))
* add copier-pyproject Claude Code plugin with adopt-copier-pyproject skill ([#140](https://github.com/hasansezertasan/copier-pyproject/issues/140)) ([ebf8f89](https://github.com/hasansezertasan/copier-pyproject/commit/ebf8f895f2595d250ce01de8a5f3b319f2250394))
* add include_repo_settings toggle and expand label set ([#154](https://github.com/hasansezertasan/copier-pyproject/issues/154)) ([638e774](https://github.com/hasansezertasan/copier-pyproject/commit/638e7743a74b37d4d661b3ffc3454c8e14af0999))
* add preset question and grouped ordering to copier scaffolding ([#141](https://github.com/hasansezertasan/copier-pyproject/issues/141)) ([f19b8e2](https://github.com/hasansezertasan/copier-pyproject/commit/f19b8e230d156a61d6f79c7282c7546bfeff744a))
* make the examples/ folder optional via include_examples ([#139](https://github.com/hasansezertasan/copier-pyproject/issues/139)) ([846e09c](https://github.com/hasansezertasan/copier-pyproject/commit/846e09c0b6837b4cbb38cdae62e7f402abdb66cd))
* opt-in Homebrew tap and Scoop bucket distribution ([#153](https://github.com/hasansezertasan/copier-pyproject/issues/153)) ([f330859](https://github.com/hasansezertasan/copier-pyproject/commit/f330859680495419dc0a254331362d5fabf5fd99))
* replace preset ladder with library/tool/web archetypes ([#148](https://github.com/hasansezertasan/copier-pyproject/issues/148)) ([7c0987b](https://github.com/hasansezertasan/copier-pyproject/commit/7c0987bf994773f0f86887d737278ab48a084237))
* run import-linter and slotscheck as prek hooks ([#138](https://github.com/hasansezertasan/copier-pyproject/issues/138)) ([7d3219c](https://github.com/hasansezertasan/copier-pyproject/commit/7d3219cf26b031b41b902c8226531e44ae226299))


### 🐛 Bug Fixes

* degrade to console-only logging when log dir is unavailable ([#126](https://github.com/hasansezertasan/copier-pyproject/issues/126)) ([f47e6fc](https://github.com/hasansezertasan/copier-pyproject/commit/f47e6fc4aa885851b671eb33772b472abcb24f26))
* harden Homebrew/Scoop reference bundle and correct distribution tests ([#155](https://github.com/hasansezertasan/copier-pyproject/issues/155)) ([638b658](https://github.com/hasansezertasan/copier-pyproject/commit/638b658e4d047f4ef7abaf7b2d93d124755746d1))
* recover tag-derived version for source-archive installs ([#125](https://github.com/hasansezertasan/copier-pyproject/issues/125)) ([5073e1c](https://github.com/hasansezertasan/copier-pyproject/commit/5073e1c4c67b189440dbd45ef4d0f1700331b7ae))
* require enabled-component deps and harden logging at import ([#119](https://github.com/hasansezertasan/copier-pyproject/issues/119)) ([5906ff2](https://github.com/hasansezertasan/copier-pyproject/commit/5906ff28e5cf8a0f65bf70974017c962ceb6325a))
* restore lost [#148](https://github.com/hasansezertasan/copier-pyproject/issues/148) review fixes and correct root CLAUDE.md ADR links ([#150](https://github.com/hasansezertasan/copier-pyproject/issues/150)) ([6d98efd](https://github.com/hasansezertasan/copier-pyproject/commit/6d98efdc691a613baf6874902623bf49ebb6f721))
* wire the bare command to the primary component entrypoint ([#147](https://github.com/hasansezertasan/copier-pyproject/issues/147)) ([038ce0e](https://github.com/hasansezertasan/copier-pyproject/commit/038ce0ef5c335776f90a44ebd954dc67dc157f9b))


### 📝 Documentation

* document branch and PR naming conventions for agents ([#120](https://github.com/hasansezertasan/copier-pyproject/issues/120)) ([4e99232](https://github.com/hasansezertasan/copier-pyproject/commit/4e99232a67c8e43c65a306eaaaa68b401e41152e))
* document macOS Icon char-class LF tradeoff ([#111](https://github.com/hasansezertasan/copier-pyproject/issues/111)) ([#129](https://github.com/hasansezertasan/copier-pyproject/issues/129)) ([c58b01e](https://github.com/hasansezertasan/copier-pyproject/commit/c58b01e36b0d2facc6220c6a050dbdac725ded53))
* document stale untagged release-comment link as accepted limitation ([#152](https://github.com/hasansezertasan/copier-pyproject/issues/152)) ([c6a4558](https://github.com/hasansezertasan/copier-pyproject/commit/c6a455893d68c22c42b47aa60c8f62eb7e6b05d7))
* document standalone-application install path ([#145](https://github.com/hasansezertasan/copier-pyproject/issues/145)) ([7fc30f0](https://github.com/hasansezertasan/copier-pyproject/commit/7fc30f0b2a846329c1dbed24cb6e2ac92c94ce35))
* move template features to root README and dev docs to CONTRIBUTING ([#136](https://github.com/hasansezertasan/copier-pyproject/issues/136)) ([2e0d835](https://github.com/hasansezertasan/copier-pyproject/commit/2e0d8354b8df18249baafb85480efc132f3ed8f1))
* recommend git URL over gh: shorthand for copier _src_path ([#151](https://github.com/hasansezertasan/copier-pyproject/issues/151)) ([9611c6d](https://github.com/hasansezertasan/copier-pyproject/commit/9611c6d0d1553db4cd98755a88dfaf63a5b260f6))
* replace Join The Project Team stub with real content ([#128](https://github.com/hasansezertasan/copier-pyproject/issues/128)) ([7a90d73](https://github.com/hasansezertasan/copier-pyproject/commit/7a90d73913951efbb5f36f89c3d42a134bdfef7d))

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

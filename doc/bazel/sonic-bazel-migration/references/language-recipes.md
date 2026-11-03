# Go, Rust, Python and prebuilt input routes

Read the [shared contract](common-contract.md), then applicable sections after Make analysis identifies languages/production. Follow inputs -> dependencies -> native targets -> installation -> acceptance. Mixed-language components also use [C/C++](native-cc.md)/[generation](code-generation.md). Dedicated topics continue to own locking/version/module policy.

## Go and CGo

Follow [Go](go.md): original evidence -> prerequisites -> MODULE/SDK -> native/ZIP locks -> Gazelle/native targets -> applicable branches -> installation/acceptance. It covers pure Go/CGo/tags/resources/vendor/workspaces/generation. [Locking](dependency-locking.md#go-modules) owns formats/updates.

## Rust

Follow [Rust](rust.md): analysis -> MODULE/SDK -> Cargo/shared graph -> native targets -> features/build.rs/proc-macros/native libraries -> installation/consumers.

## Python and wheels

Follow [Python](python.md): analysis -> interpreters/tools -> shared contents/metadata -> wheel/direct installation TAR -> cross-component runtime metadata -> assembly locks/consumers. Examples cover requires/extras/entries/resources/runtime_deps for two packages. Build dependencies, distribution requirements and final runtime versions remain distinct.

## Pinned prebuilt inputs

1. Establish original URL/version/architecture/checksum/license/contents/purpose. Modified/rebuilt inputs use source routes. Distinguish fixed distributions from current source components.
2. Declare downloads/extraction with repository/package rules. Target inputs use target architecture; exec tools use executor architecture. File existence does not prove ABI/loader/runtime compatibility.
3. Prefer producer/APT CcInfo. Other managed libraries may use cc_import where supported; components must not rewrap existing APT APIs. Data exports files/TAR; tools export executable/closure.
4. Verify identity/install contents/target ABI/real consumers. Reuse initial extraction rather than repack/unpack for images. Report as prebuilt input preparation, not source recompilation.

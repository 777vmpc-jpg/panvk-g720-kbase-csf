# Public PanVK/Faux123 source audit (2026-11-26)

## What is public

- Faux123's public PanVK device repositories publish the README, license and release packages. The RG556 repository README says the build container, the author's patch files, test harnesses and recreate guide are in a private companion repository. The public repository itself does not expose those patch files.
- Faux123's v1.1.9 release notes explicitly state that the package was built from Mesa `5a07217f`, the `zenithblue-oss/panvk-kbase-android` `v0.1.0-rc4` series (`5b87b74`), plus 192 Faux123 patches. The release package is a binary `.adpkg.zip`, not a source patch archive.
- Therefore the 192 Faux123-authored patches cannot be reconstructed faithfully from the public repo or release notes. This project must not label unrelated patches as those 192 patches.

## Public source retained in this repository

The complete public `zenithblue-oss/panvk-kbase-android` source repository is retained as a Git submodule at:

- Path: `vendor/panvk-kbase-android-public`
- Upstream: https://github.com/zenithblue-oss/panvk-kbase-android
- Pinned upstream commit: `cf70e02b918e1864cbcd746a7fefa57b96c673ce`
- Upstream `sources.lock` Mesa base: `5a07217f034b3e50d8c7c7794f97a2df1742613b`

This public repository contains patch families for Android, common code, CSF v11, JM v7/v9 and other architecture-specific work. These are the public Kbase/Mesa integration patches and reference source, not Faux123's private 192-patch series. The submodule is fetched by this project's existing recursive submodule checkout.

## Heap renewal and memory investigation leads

Public patch candidates inspected:

- `patches/csf-v11/102-renew-the-kbase-tiler-heap-without-a-graphics-drain.patch`: changes renewal to avoid a graphics drain, using two heap descriptor slots and retirement tracking. It is a structural change, not a threshold-only tuning.
- `patches/csf-v11/192-destroy-retired-kbase-tiler-heaps-on-the-heap-thread.patch`: moves safe retired-heap destruction off the submitting thread.
- `patches/csf-v11/223-driver-memory-accounting-panvk-debug-mem.patch`: adds detailed BO, heap-context, BC-store and VkDeviceMemory accounting for diagnosing memory growth.
- `patches/csf-v11/224-smaller-kbase-tiler-heaps-and-bounded-term-backlog.patch`: reduces initial tiler heap chunks and bounds the retired-heap TERM backlog. This is directly relevant to heap churn and retained heap memory.

These patches were inspected as source references. They have **not** been blindly applied to the MC7 branch: they touch queue lifecycle, heap descriptors, memory accounting and multiple shared files, and must be ported against this branch's existing Kbase implementation with compile checks. The existing MC7 `KBASE_TILER_HEAP_RENEW_WORK=131072` tuning remains separate and is not proof of a fix.

## Device scope and validation

Faux123 v1.1.9's release notes say the build was tested on Mali-G57, G77, G610 and G710; they also explicitly mention a remaining partial-screen rendering issue on Mali-G720. The public kbase patch source includes newer CSF work, but neither that fact nor FauxVkDB feature checks proves correctness on this Xiaomi Mali-G720 MC7. All MC7-specific changes require build and device validation.

## References

- Faux123 public source README: https://github.com/faux123/panvk-faux123-driver-rg556
- Faux123 v1.1.9 release: https://github.com/faux123/panvk-faux123-driver-rg556/releases/tag/v1.1.9
- Public Kbase patch source: https://github.com/zenithblue-oss/panvk-kbase-android

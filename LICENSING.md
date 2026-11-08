# Licensing and attribution

This repository contains components under different terms. A GitHub licence badge or the application licence does not replace the component notices.

## Application code

The application is derived from M-VAVE FM1 Open V14, commit `4c7496daac04a95ff10d1afdcc8f9ead2dbabc41`. Its GPL-3.0-only licence includes the additional permission to link the FM1 binary SDK. The full original text is retained in [LICENSE.md](LICENSE.md), and source-file notices remain in place. BAILE modifications to that code retain the same terms.

The GPL linking exception is specific to the SDK named in that permission. It does not turn the binary SDK into GPL software or disclose proprietary engine source.

## SDK and component notices

[THIRD_PARTY.md](THIRD_PARTY.md) is retained verbatim from the base and contains the component notices and full licence texts. In particular, M-VAVE grants binary redistribution of its proprietary engine for FM1 development/use under the stated FM1-only terms, including commercial and non-commercial redistribution, subject to notices and other applicable component licences.

The bundled V15 boot/update/recovery resources are identified there as Apache-2.0. Other selected components retain MIT, Apache-2.0, BSD-2-Clause and their respective runtime terms. No rights beyond those notices are claimed here. SDK manifest hashes allow readers to verify the unmodified payload.

An optional original V16 file is a user-provided build input, hash-checked by the tool; it is not bundled or relicensed by this repository.

## Supplied artwork and Tamborzão samples

The visual references and Tamborzão source project were supplied by Mulú for BAILE. The compact art, the source mockups/crops, the embedded sample-bank bytes and their compiled-header copies contain those supplied assets.

No separate open-content licence for these images or recordings has been assigned in this repository. The application GPL does not grant an independent asset-reuse licence. Obtain the relevant rights holder's permission for reuse of the supplied images/recordings beyond rights already held. This notice does not assert ownership of third-party source material or replace any applicable original asset terms.

Screenshots show BAILE rendering those assets, and carry the same asset considerations. They are emulator captures, not hardware photographs.

## Documentation and project tools

BAILE-authored build scripts, portable tests and documentation are distributed under GPL-3.0-only, retaining any existing upstream notice and exception where applicable. The packaging implementation adapts the source packager described in [THIRD_PARTY.md](THIRD_PARTY.md), which also retains its applicable MIT terms.

SLOOP was a reference for documentation organization only; BAILE does not claim to inherit SLOOP's code, licence, installation guarantees or features. Manufacturer and project names are used for identification; no endorsement is implied.

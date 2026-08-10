# Commit-pinned reference repositories

This folder holds complete GitHub source archives for offline architecture study and
structural uniformity. They are isolated from runtime code so humans and agents do
not mistake them for locally maintained dependencies.

Before using a snapshot:

1. Read `REPOSITORY_REGISTER.csv` and `SNAPSHOT_PROVENANCE.md`.
2. Verify the file against `CHECKSUMS.sha256`.
3. Read the upstream root license and any nested third-party notices.
4. Consult `docs/research/reference-repositories/ADOPTION_MAP.md`.
5. Re-check the current upstream project, vulnerabilities and license before reuse.

Do not build every archive as part of this project. Extract only the repository being
studied into a temporary directory; do not edit the archive. These archives include
source only, not Git history, submodule contents, model weights or datasets.

MentraOS and Holohub are split into parts smaller than 100 MB for ordinary GitHub
storage. Reconstruct them outside the project before opening:

```bash
REFERENCE_DIR="$PWD"
cat snapshots/mentraos-6aa07607dbc7.tar.gz.* > /tmp/mentraos-6aa07607dbc7.tar.gz
cat snapshots/holohub-53cb66a1ae40.tar.gz.* > /tmp/holohub-53cb66a1ae40.tar.gz
(cd /tmp && shasum -a 256 -c "$REFERENCE_DIR/ORIGINAL_ARCHIVES.sha256")
```

Example integrity check:

```bash
cd third_party/reference-repositories
shasum -a 256 -c CHECKSUMS.sha256
```

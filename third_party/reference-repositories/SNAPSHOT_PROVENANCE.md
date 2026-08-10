# Snapshot provenance

Generated on 2026-07-17 from GitHub's unauthenticated public repository and commit
APIs and GitHub commit archive endpoints. Each archive URL had the form:

`https://github.com/OWNER/REPOSITORY/archive/FULL_COMMIT_SHA.tar.gz`

The exact commits, branches, upstream URLs, reported root licenses and byte sizes are
in `REPOSITORY_REGISTER.csv`; locally calculated SHA-256 values are in
`CHECKSUMS.sha256`. Archive contents were checked for a root license file.

The MentraOS and Holohub archives were byte-split after download so no stored file
exceeds GitHub's normal 100 MB limit. `ORIGINAL_ARCHIVES.sha256` records the complete
pre-split archive hashes; `CHECKSUMS.sha256` records each stored part.

## Important limitations

- GitHub commit archives omit `.git` history.
- Git submodule contents may not be present.
- A permissive root license does not remove obligations for nested dependencies.
- Upstream source does not imply medical-device clearance, clinical performance,
  cybersecurity fitness, privacy compliance or compatibility with this hardware.
- No dataset, pretrained weight, patient media, binary SDK or credential was added.
- Re-run license, dependency, vulnerability and regulatory review before adoption.

The archives are evidence of what was reviewed, not a claim that the code is safe or
approved for an operating room.

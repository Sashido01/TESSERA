# Inventory — stage II experiment

[Русский — оригинал](INVENTORY.md) | **English — translation**

`python scripts/inventory.py --root <project-root>` is a separate Project Audit tool candidate. Run only from a trusted installed skill on an explicitly selected stable snapshot. It neither modifies the project nor executes its code. Stdout JSON contains relative paths, sizes, modification times, extensions, stack markers and scope boundaries. File names can contain confidential data; do not transmit the JSON to external services without authorization.

Default limits: 10,000 entries and depth 32 (maximum allowed 50,000 and 64). Excluded names appear in `excluded_names`; actual exclusions in `gaps`. `SCOPED_COMPLETE` means the declared metadata scope was traversed, not that the audit is complete. Any detected unexpected boundary yields `PARTIAL`, exit 1. Invalid input/root access yields exit 2. Known links and reparse points are not followed; different devices are not traversed. Verified on temporary Linux trees; Windows junction handling tested only with a synthetic attribute, native Windows remains NOT_VERIFIED.

`metadata_sha256` hashes sorted path/size/mtime records, directories, exclusions and limits. It is NOT a content hash: byte changes retaining size and mtime are not detected (tested negative control). `content_integrity=NOT_VERIFIED` always. This is not proof that the project is unchanged or that execution is safe. There is no atomic snapshot; path substitution races, same-device mounts/bind mounts, unchanged metadata, network filesystems and JSON output size are not fully controlled. Use a trusted stable snapshot; this is not a sandbox. Exact hashing of authorized files is a separate subsequent task.

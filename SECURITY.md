# Security and privacy

OpenHumanity v0.1 is experimental local-first software, not a hardened public service.

## Trust boundaries

- A valid signature establishes control of a signing key, not real-world identity, truth, authority or the reliability of a source.
- Record identifiers detect alterations relative to trusted identifiers. They do not prevent withholding, deletion, conflicting revisions or misinformation.
- Local browser access assumes a trusted device and operating-system account. The signing server keeps a decrypted key in memory while running.
- The local browser server binds to loopback and checks request hosts, origins and tokens. Do not expose it using a tunnel or reverse proxy.
- Peer sharing exports every signed record in the selected database. Use a separate, intentionally shareable database. The prototype peer server does not authenticate clients. Do not expose it directly to the internet.
- Imported records are untrusted even when signatures are valid. Do not automatically execute or fetch sources.

## Private data and recovery

Keep encrypted PEM keys and SQLite files outside publicly served directories and restrict filesystem access. Database contents are not encrypted by OpenHumanity. Avoid collecting sensitive personal information. A record distributed to peers cannot reliably be recalled.

Back up the encrypted signing key and its passphrase separately. There is no password reset. Stop all node processes before copying a database, or use the SQLite backup API. Restore backups into a separate directory and confirm that records and identity work before replacing live files. Signed JSON exports preserve records, not private signing keys.

## Reporting

During private development, report suspected vulnerabilities directly to the repository owner. Do not publish proof-of-concept exploits or sensitive data in issues. Public deployment requires a separate security review, access controls, abuse handling and operational limits.

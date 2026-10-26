# Shared release identity

Lab, Site and production builders resolve the same version from the selected source commit:
`1.38.<first-parent commit count>`. The release ID appends the first twelve source SHA characters.
The full source revision remains authoritative; compare both version and revision when checking equality.
Full history is mandatory; shallow builds fail instead of guessing. Rebuilding or promoting a pinned source
keeps its version. Main advances the counter; branch builds are candidates and must not be presented as main releases.

`runtime_info.software_release` is the comparable software identity in Lab and Site.
Site's top-level deployment ID and mirror SHA continue to describe its separate hosting deployment.
An unsigned installed manifest does not prove deployment attestation or that a desktop MCP process restarted.
Lab and production payload digests can differ because they expose different maturity scopes.

Every source change on main prepares both a Lab artifact and a Site source artifact using that exact Lab.
Generated Marketplace snapshot commits are excluded to prevent a packaging loop. Production promotion
must preserve the Lab version, release ID and source revision, in addition to passing existing runtime evidence gates.

Marketplace snapshots still require their package PR merged. The repository setting allowing Actions to
create PRs must be enabled for automatic PR creation; workflow permissions alone cannot grant it.
Site artifacts are prepared automatically, but live publication must use the native Sites workflow described
in SITES-PUBLISHING.md. A GitHub merge or uploaded artifact is not a successful Site deployment.
A running Desktop MCP process may keep an old package until it reconnects; runtime_info reveals its actual version.

To measure production lag, compare its software_release with the latest main artifact. For exact source
lag use `git rev-list --first-parent --count PROD_SOURCE..MAIN_SOURCE` after confirming PROD_SOURCE is an ancestor.
Do not subtract hosting deployment version numbers or interpret unequal payload digests as release inequality.

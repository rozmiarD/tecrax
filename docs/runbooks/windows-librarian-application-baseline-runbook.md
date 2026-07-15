# Windows librarian application baseline runbook

This runbook defines a public-safe packaging and pilot gate for a librarian
Windows endpoint. It does not download software, contain private installer
artifacts, deploy Group Policy, join a domain, or authorize a live change.

## Ownership and boundaries

Tecrax owns the infrastructure-domain package vocabulary, observations,
detection requirements, smoke tests and stop conditions. RExecOp may later
coordinate an approved lifecycle, GovEngine owns admission and SCLite owns
canonical evidence and receipts. This runbook must not duplicate those roles.

Keep outside Git:

- private endpoint and user inventories;
- proprietary installers and redistribution-restricted binaries;
- license files, individualized application configuration and credentials;
- AV package tokens, Wazuh enrollment material and Zabbix PSKs;
- exact internal hostnames, groups, shares, printers and server addresses.

## Package manifest gate

Every package needs an exact-artifact lab record before deployment:

- official publisher source URI and acquisition date;
- approved version, architecture and installer type;
- SHA-256 or publisher hash plus Authenticode signer where applicable;
- exact machine-wide install and uninstall commands;
- accepted success and reboot exit codes;
- exact detection rule using package identity, registry and file version;
- update owner and proof that a second updater will not compete;
- user-data preservation rule;
- rollback artifact and rollback command;
- non-administrator smoke and post-reboot smoke.

Do not infer ProductCode, service names, uninstall strings, command switches or
exit codes from a different version. Unknown values are a stop condition, not
placeholders to fill from memory.

## Initial role stack

The initial librarian role stack is:

- Bitdefender Endpoint Security Tools;
- Wazuh agent and Zabbix agent;
- Firefox ESR and Chrome Enterprise Stable;
- managed Thunderbird ESR;
- LibreOffice;
- 7-Zip, VLC, IrfanView, Notepad++ and SumatraPDF;
- the separately controlled SOWA client and its approved modules.

Microsoft Edge, WebView2, Windows PowerShell 5.1, supported Windows components,
Visual C++ runtimes and device drivers are dependencies, not debloat targets.
Local role exceptions belong in private operator policy and must not be silently
converted into packages installed on every endpoint.

## Preparation order

Use this order on one operator-supervised pilot:

1. Prove supported Windows lifecycle, domain readiness, free space, pending
   reboot state, local and per-user installs, running processes and preserved
   user/application data.
2. Validate existing Bitdefender health. Add Wazuh and Zabbix separately, with
   compatibility and central-console health proof after each agent.
3. Install Firefox ESR and Chrome Enterprise, then validate ADMX/policy readback
   separately from application detection.
4. Install LibreOffice and Thunderbird ESR. Treat IMAP configuration and local
   mail archives as a separate per-user migration contract.
5. Install 7-Zip, Notepad++, IrfanView, SumatraPDF and VLC.
6. Deploy SOWA only after its proprietary package gate is complete.
7. Reboot only when an exact installer or policy requires it, then run the full
   login and application smoke.

Do not reinstall a healthy security or monitoring agent merely to normalize its
installer. First reconcile its identity, policy, version and central health.

## Product-specific minimums

Use only the primary vendor documentation when building exact manifests:

- [Firefox Enterprise](https://firefox-admin-docs.mozilla.org/guides/getting-started/)
  and [Mozilla policy templates](https://support.mozilla.org/kb/customizing-firefox-using-group-policy-windows);
- [Chrome Enterprise deployment](https://support.google.com/chrome/a/answer/7650032)
  and [Chrome policy management](https://support.google.com/chrome/a/answer/187202);
- [Thunderbird policy templates](https://thunderbird.github.io/policy-templates/);
- [LibreOffice enterprise deployment](https://wiki.documentfoundation.org/images/3/36/EN_Enterprise.pdf);
- [7-Zip downloads](https://www.7-zip.org/download.html);
- [Notepad++ command-line reference](https://npp-user-manual.org/docs/command-prompt/);
- [IrfanView FAQ and licensing](https://www.irfanview.com/faq.htm);
- [SumatraPDF installer arguments](https://www.sumatrapdfreader.org/docs/Installer-cmd-line-arguments);
- [VLC Windows packages](https://www.videolan.org/vlc/download-windows.html);
- [Bitdefender BEST installation](https://www.bitdefender.com/business/support/en/77212-157497-install-security-agents---standard-procedure.html);
- [Wazuh Windows deployment variables](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/deployment-variables/deployment-variables-windows.html);
- [Zabbix Windows MSI installation](https://www.zabbix.com/documentation/current/en/manual/installation/install_from_packages/win_msi).

Browser and Thunderbird profiles are not application detection. Never delete a
profile as part of install, update, uninstall or rollback. Default applications,
file associations and browser extensions need separate policy and smoke gates.

## SOWA proprietary package gate

SOWA remains a separate business-critical contract. Before packaging, record:

- the approved vendor artifact and deployment entitlement;
- exact client edition/version, modules and updater;
- machine-wide and per-user state boundaries;
- runtime dependencies, services, tasks, shortcuts and network requirements;
- private custody for individualized configuration and license material;
- vendor-supported install, update, rollback and recovery behavior.

The public package manifest may reference a private artifact identifier but must
not embed the artifact, license or configuration. Preserve the approved public
desktop shortcut set and smoke every shortcut target. Vendor-delivered remote
support must remain an on-demand QuickSupport tool without an unattended-access
service.

SOWA smoke must launch all required modules as a non-administrator and prove the
correct environment. Any transaction against production data requires a separate
test procedure and operator approval; read-only navigation is the default smoke.

## Stop conditions

Stop packaging or rollout when:

- Windows is unsupported and no active, documented ESU or time-bounded migration
  exception exists;
- the official artifact, hash/signature or publisher cannot be verified;
- install, detection, update ownership or rollback is unproven for the exact
  version;
- an active per-user install or conflicting product has no migration plan;
- a security installer would remove another product or change firewall/Defender
  behavior outside the approved scope;
- a secret, license or private configuration would enter Git, GPO, logs or chat;
- an agent creates a duplicate identity or is not healthy centrally;
- default-app changes or user-data preservation are not understood;
- SOWA dependencies, configuration, licensing or vendor method remain unknown;
- the smoke would write to production business data without separate approval.

## Pilot success

The generic package is `packaging-ready` only after every exact-artifact manifest
passes lab validation. The endpoint is `operational-ready` only when:

- all required machine-wide packages are detected under a standard user;
- browsers and managed policies, office/PDF/media utilities and Thunderbird
  launch without UAC or unmanaged update prompts;
- Bitdefender, Wazuh and Zabbix are healthy with unique central identities;
- SOWA and every required module/shortcut pass their functional smoke;
- existing user data, application settings and printer functionality remain
  available;
- rollback artifacts exist and rollback does not delete user or business data.

## Tecrax artifact decision

Current activation level: `L1 - public-safe runbook`.

Do not add an executable helper until exact artifacts have been tested and at
least two successful pilots prove a repeated command shape. Any future helper
may validate bounded manifests and emit observations; it must not carry secrets,
invent package commands or become a competing software-deployment engine.

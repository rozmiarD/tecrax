from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_apply_requires_expected_current_name(tmp_path: Path) -> None:
    identity = tmp_path / "identity"
    known_hosts = tmp_path / "known_hosts"
    identity.write_text("fixture", encoding="utf-8")
    known_hosts.write_text("fixture", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/prepare-windows-ad-pilot-endpoint.sh"),
            "--apply",
            "--host",
            "fixture.invalid",
            "--user",
            "operator",
            "--identity-file",
            str(identity),
            "--known-hosts",
            str(known_hosts),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Missing required argument: --expected-current-name" in result.stderr


def test_windows_helper_embeds_fail_closed_hostname_gate(tmp_path: Path) -> None:
    identity = tmp_path / "identity"
    known_hosts = tmp_path / "known_hosts"
    identity.write_text("fixture", encoding="utf-8")
    known_hosts.write_text("fixture", encoding="utf-8")
    capture = tmp_path / "powershell.ps1"
    fake_ssh = tmp_path / "ssh"
    fake_ssh.write_text('#!/usr/bin/env bash\ncat > "$CAPTURE"\n', encoding="utf-8")
    fake_ssh.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["CAPTURE"] = str(capture)

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/prepare-windows-ad-pilot-endpoint.sh"),
            "--apply",
            "--host",
            "fixture.invalid",
            "--user",
            "operator",
            "--identity-file",
            str(identity),
            "--known-hosts",
            str(known_hosts),
            "--expected-current-name",
            "CURRENT-LT-001",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    script = capture.read_text(encoding="utf-8")
    assert "$ComputerSystem.Name -ne $ExpectedCurrentName" in script
    assert "$ExpectedCurrentName = 'CURRENT-LT-001'" in script


def test_windows_helper_uses_explicit_ad_dns_and_ntp_client_mode(tmp_path: Path) -> None:
    identity = tmp_path / "identity"
    known_hosts = tmp_path / "known_hosts"
    identity.write_text("fixture", encoding="utf-8")
    known_hosts.write_text("fixture", encoding="utf-8")
    capture = tmp_path / "powershell.ps1"
    fake_ssh = tmp_path / "ssh"
    fake_ssh.write_text('#!/usr/bin/env bash\ncat > "$CAPTURE"\n', encoding="utf-8")
    fake_ssh.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["CAPTURE"] = str(capture)

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/prepare-windows-ad-pilot-endpoint.sh"),
            "--host",
            "fixture.invalid",
            "--user",
            "operator",
            "--identity-file",
            str(identity),
            "--known-hosts",
            str(known_hosts),
            "--dns-server",
            "ad-dns.example.invalid",
            "--ntp-server",
            "ntp.example.invalid",
            "--domain",
            "ad.example.invalid",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    script = capture.read_text(encoding="utf-8")
    assert "$DomainDnsServer = if ($DnsServers.Count -gt 0)" in script
    assert '$ManualPeer = "$NtpServer,0x8"' in script
    assert "Resolve-DnsName $Domain -Type SOA @DomainResolve" in script
    assert "Resolve-DnsName \"_ldap._tcp.dc._msdcs.$Domain\" -Type SRV @DomainResolve" in script


def test_samba_csv_and_groups_are_preflighted_before_first_mutation(tmp_path: Path) -> None:
    csv_path = tmp_path / "users.csv"
    csv_path.write_text(
        "login,given_name,surname,email,groups\n"
        "user01,Example,One,user01@example.invalid,GG_Staff\n"
        "user02,Example,Two,user02@example.invalid,GG_Missing\n",
        encoding="utf-8",
    )
    log = tmp_path / "samba.log"
    fake = tmp_path / "samba-tool"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$SAMBA_LOG\"\n"
        "if [[ \"$1 $2 $3\" == 'group show GG_Missing' ]]; then exit 1; fi\n"
        "if [[ \"$1 $2\" == 'user show' ]]; then exit 1; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["SAMBA_LOG"] = str(log)

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/provision-samba-ad-users.sh"),
            "--apply",
            "--csv",
            str(csv_path),
            "--user-ou",
            "OU=Staff,OU=Users,OU=ORG",
            "--password-stdin",
        ],
        input="temporary-fixture-password\n",
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 2
    assert "Missing required group: GG_Missing" in result.stderr
    assert "user create" not in log.read_text(encoding="utf-8")

# rhel-hardening

Ansible tooling to harden Red Hat Enterprise Linux 8 and 9 servers to a CIS Level 1 Server baseline, prove the result with OpenSCAP, and patch the same servers in rings with health checks and a rollback record. It is the tooling behind two runbooks:

- [SOP-LNX-001](../../linux-administration/SOP-LNX-001-hardening-rhel-baseline-ansible-openscap.md): hardening with the `rhel_baseline` role, checked by an OpenSCAP scan, kept as hashed evidence.
- [SOP-LNX-002](../../linux-administration/SOP-LNX-002-rhel-patching-maintenance-windows.md): patch rings, maintenance windows, live kernel patching, rollback and SLA reporting.

Written for RHEL 8 and 9. CI runs the unit tests and an Ansible syntax check on every playbook; run the dry run in SOP-LNX-001 on a canary before the first apply.

## What it does

| Piece | What it does |
|---|---|
| `roles/rhel_baseline` | Applies the baseline in eleven tagged areas, each with its own on/off variable. Preflight refuses changes that would lock you out. The last task lists every pending reboot. Idempotent, and safe to run with `--check --diff` |
| `playbooks/site.yml` | Applies the role to the hosts in `--limit` |
| `playbooks/evidence.yml` | Installs `openscap-scanner` and `scap-security-guide`, runs `oscap xccdf eval` with the chosen profile against `ssg-rhel8-ds.xml` or `ssg-rhel9-ds.xml`, fetches the ARF and HTML results, summarises them and writes `SHA256SUMS` |
| `playbooks/patch.yml` | Patches a ring in serial batches with `max_fail_percentage: 0`: health check, security errata, reboot only when `dnf needs-restarting -r` says so, health check again, and a per host record with the dnf transaction ID |
| `playbooks/livepatch.yml` | Subscribes kernels to live patches (`dnf kpatch auto`) and installs the live patch for the running kernel |
| `playbooks/patch_report.yml` | Collects `dnf updateinfo` from every host and scores the outstanding security errata against the SLA |
| `tools/scap_summary.py` | Turns an OpenSCAP ARF or XCCDF result file into `report.md`, `summary.json` and `findings.json`, applying dated exceptions. Python 3 standard library only |
| `tools/patch_report.py` | Turns the collected `dnf updateinfo` output into `compliance.md` and `compliance.json`. Python 3 standard library only |

## Layout

```text
tools/rhel-hardening/
  ansible.cfg                    run ansible-playbook from this folder
  requirements.yml               ansible.posix, community.general
  inventory/
    hosts.example.yml            copy to hosts.yml (git ignores hosts.yml)
    group_vars/                  all, rhel_web, container_hosts, ring0, ring1
    host_vars/canary-01.yml      per host example
  playbooks/
    site.yml                     apply the baseline
    evidence.yml                 OpenSCAP scan and evidence folder
    patch.yml                    ringed patching
    livepatch.yml                live kernel patches
    patch_report.yml             SLA compliance report
    tasks/health_check.yml       url, port, service and command checks
  roles/rhel_baseline/
    defaults/main.yml            every variable, with comments
    tasks/                       main.yml, preflight.yml, one file per area, report.yml
    templates/                   sshd, audit rules, modprobe
    handlers/main.yml
  exceptions/exceptions.example.yml
  tools/scap_summary.py
  tools/patch_report.py
  tests/                         unittest suite and fixtures
```

`evidence/` and `reports/` are created on the control node when the playbooks run. Both are in `.gitignore`: keep them in your evidence store, not in this repository.

## Quick start

Requirements on the control node: `ansible-core` 2.15 or later, Python 3.9 or later. On the hosts: RHEL 8 or 9, registered for updates, an admin account with an SSH key and sudo.

```bash
cd tools/rhel-hardening
ansible-galaxy collection install -r requirements.yml
cp inventory/hosts.example.yml inventory/hosts.yml     # then edit the hosts and groups
```

The commands below are the ones in SOP-LNX-001, in order:

```bash
# 2. Baseline scan before any change
ansible-playbook playbooks/evidence.yml --limit canary-01 -e scap_profile=cis_server_l1

# 3. Dry run on the canary; read the SSH, firewalld and PAM diffs
ansible-playbook playbooks/site.yml --limit canary-01 --check --diff

# 4. SSH and authentication first; prove a second login and sudo -v before you go on
ansible-playbook playbooks/site.yml --limit canary-01 --tags ssh,auth

# 5. The rest on the canary; read the last task's message for pending reboots
ansible-playbook playbooks/site.yml --limit canary-01

# 6. The group, a few hosts at a time
ansible-playbook playbooks/site.yml --limit rhel_web --forks 5

# 7. Scan again and keep the folder
ansible-playbook playbooks/evidence.yml --limit rhel_web -e scap_profile=cis_server_l1
```

And from SOP-LNX-002:

```bash
# Ring 0 (test): dnf-automatic, turned on by the patching area (group_vars/ring0.yml)
ansible-playbook playbooks/site.yml --limit ring0 --tags patching

# Ring 1 (non-production), weekly window: security errata issued at least 3 days ago
ansible-playbook playbooks/patch.yml -e patch_target=ring1

# Ring 2 (production), monthly window: only the advisories that ring 1 applied, two hosts at a time
ansible-playbook playbooks/patch.yml -e patch_target=ring2_web -e patch_change_id=CHG0012348 \
  -e @reports/patch/<ring 1 run id>/advisories.yml

# Emergency window for critical errata
ansible-playbook playbooks/patch.yml -e patch_target=ring2 -e '{"patch_severities": ["Critical"]}'

# Live kernel patches between windows
ansible-playbook playbooks/livepatch.yml -e patch_target=ring2

# SLA compliance report for every host
ansible-playbook playbooks/patch_report.yml
```

The window times (ring 1 on Tuesday at 20:00, ring 2 monthly) belong to the scheduler that runs these commands, for example an automation controller schedule or a cron job on the control node.

## Variables

The role's full list, with comments, is in [defaults/main.yml](roles/rhel_baseline/defaults/main.yml). These are the ones most sites set.

| Variable | Default | Purpose |
|---|---|---|
| `rhel_baseline_<area>` | `true` | Turn an area off for a host or group, for example `rhel_baseline_firewall: false`. Areas: `ssh`, `auth`, `kernel`, `firewall`, `selinux`, `audit`, `aide`, `crypto`, `services`, `patching` |
| `rhel_baseline_admin_users` | the connecting user | Accounts that must keep SSH access; preflight checks each has a non-empty `~/.ssh/authorized_keys` |
| `rhel_baseline_ssh_password_authentication` | `false` | Set `true` for a host whose admin still signs in with a password |
| `rhel_baseline_ssh_keys_from_command` | `false` | Set `true` when keys come from an `AuthorizedKeysCommand` (for example SSSD), so preflight does not look for the file |
| `rhel_baseline_ssh_permit_root_login` | `"no"` | `PermitRootLogin` value |
| `rhel_baseline_ssh_allow_groups` | `[]` | Written as `AllowGroups` when not empty |
| `rhel_baseline_ssh_extra_settings` | `{}` | Other sshd keywords, for example `{AllowTcpForwarding: "no"}` |
| `rhel_baseline_authselect_features` | `[with-faillock, without-nullok]` | Features enabled on the current authselect profile |
| `rhel_baseline_authselect_force` | `false` | Allow the role to select `rhel_baseline_authselect_profile` on a host whose PAM is not managed by authselect |
| `rhel_baseline_faillock_deny`, `_unlock_time` | `5`, `900` | pam_faillock lockout |
| `rhel_baseline_pwquality_minlen`, `_minclass` | `14`, `4` | Password quality |
| `rhel_baseline_shell_timeout` | `900` | `TMOUT` for interactive shells |
| `rhel_baseline_sysctl` | see defaults | Kernel parameters written to `/etc/sysctl.d/50-rhel-baseline.conf` |
| `rhel_baseline_sysctl_overrides` | `{}` | Merged over `rhel_baseline_sysctl`, for example `{net.ipv4.ip_forward: 1}` on container hosts. A value of `null` drops the key |
| `rhel_baseline_disabled_modules` | cramfs, usb-storage and others | Modules that may not load |
| `rhel_baseline_firewall_services` | `[ssh]` | Services allowed in the zone, for example `[ssh, https]` on web servers. Preflight refuses a list without `ssh` |
| `rhel_baseline_firewall_ports` | `[]` | Extra ports, for example `["8443/tcp"]` |
| `rhel_baseline_firewall_prune` | `true` | Remove services that are not in the list (cockpit and dhcpv6-client on a default install) |
| `rhel_baseline_firewall_zone` | `""` | Zone to manage; empty means the default zone |
| `rhel_baseline_selinux_state` | `enforcing` | A host where SELinux is disabled goes to permissive with a full relabel first |
| `rhel_baseline_audit_immutable` | `false` | Add `-e 2` so audit rules cannot change until reboot |
| `rhel_baseline_kernel_args` | `[audit=1, audit_backlog_limit=8192]` | Added to every boot entry and to `/etc/default/grub` |
| `rhel_baseline_crypto_policy` | `DEFAULT` | System-wide crypto policy; `LEGACY` is refused |
| `rhel_baseline_fips` | `false` | Turn on FIPS mode (needs a reboot) |
| `rhel_baseline_services_disabled` | avahi, cups, rpcbind and others | Units stopped, disabled and masked when installed |
| `rhel_baseline_packages_absent` | telnet, tftp, rsh and others | Packages removed |
| `rhel_baseline_patching_automatic` | `false` | Ring 0: dnf-automatic applies security errata daily |
| `rhel_baseline_patching_kpatch` | `false` | Subscribe kernels to live patches |
| `rhel_baseline_reboot_if_needed` | `false` | Reboot at the end of the run when a reboot is pending |
| `scap_profile` | `cis_server_l1` | Evidence playbook: SCAP Security Guide profile, short or full ID |
| `scap_exceptions_file` | `exceptions/exceptions.yml` | Evidence playbook: used when the file exists |
| `evidence_fail_on` | `none` | Evidence playbook: `high` fails the host on a high-severity FAIL without an exception; `fail` on any FAIL |
| `patch_target` | none, required | Patch playbooks: group or host to patch |
| `patch_serial`, `patch_max_fail_percentage` | `2`, `0` | Patch playbook: batch size and failure tolerance (set with `-e`) |
| `patch_min_errata_age_days` | `0` (ring 1: `3`) | Only security errata issued at least this many days ago |
| `patch_advisories` | `[]` | Only these advisories; `reports/patch/<run id>/advisories.yml` sets it for the next ring |
| `patch_severities` | `[]` | Only these severities, for example `[Critical]` |
| `patch_mode` | `security` | `all` applies every update, not only security errata |
| `patch_allow_reboot` | `true` | Reboot when `dnf needs-restarting -r` says one is needed |
| `patch_health_checks` | `[{type: service, name: sshd}]` | Checks before and after patching: `url`, `port`, `service` or `command` (see [health_check.yml](playbooks/tasks/health_check.yml)) |
| `patch_pre_tasks_file`, `patch_post_tasks_file` | `""` | Task files run before patching and after the health checks, for example to leave and rejoin a load balancer pool |
| `patch_change_id` | `""` | Change record written into each patch record |

## Tags and controls

Run one area with `--tags <tag>`. Preflight and the pending reboot report run with every tag.

| Tag | What it changes | NIST SP 800-53 R5 |
|---|---|---|
| `preflight` | Nothing. Checks RHEL 8 or 9, ansible-core 2.15, an `authorized_keys` file for each admin user before password login is turned off, `ssh` in the firewall list, and the sshd drop-in `Include` on RHEL 9 | CM-3, CM-6 |
| `ssh` | Login banner; on RHEL 9 `/etc/ssh/sshd_config.d/40-baseline.conf`, on RHEL 8 a block between the `rhel_baseline` markers at the top of `sshd_config`; root login off, key only, `MaxAuthTries`, idle timeout, host key permissions. Validated with `sshd -t` before sshd reloads | AC-6(2), AC-7, AC-8, AC-17, AC-17(2), IA-2, SC-10 |
| `auth` | authselect features `with-faillock` and `without-nullok`, `faillock.conf`, `pwquality.conf`, password ageing and `UMASK` in `login.defs`, `TMOUT`, sudo `use_pty` and log file | AC-7, AC-11, AC-12, IA-5(1), AU-12 |
| `kernel` | sysctl hardening, module blacklist, core dumps off | CM-6, CM-7, SC-5, SC-7, SI-16 |
| `firewall` | firewalld installed and running, only the listed services and ports in the zone | SC-7, CM-7, AC-4 |
| `selinux` | SELinux `enforcing` with the `targeted` policy; a disabled host is relabelled in permissive first | AC-3, AC-3(3), AC-6 |
| `audit` | auditd and rsyslog running, `auditd.conf` limits, audit rules, `audit=1` and `audit_backlog_limit` on the kernel command line, persistent journal | AU-2, AU-3, AU-4, AU-5, AU-9, AU-12 |
| `aide` | AIDE installed, audit tools watched, first database built, daily check scheduled | SI-7, SI-7(1) |
| `crypto` | System-wide crypto policy, optional FIPS mode, no sshd override on RHEL 8 | SC-8, SC-12, SC-13, IA-7 |
| `services` | Unneeded services masked, legacy packages removed, chronyd running, cron and at limited to root | CM-7, CM-7(1), AU-8 |
| `patching` | `gpgcheck=1`, `installonly_limit=3`, `dnf-plugins-core`; on ring 0 dnf-automatic for security errata; optional live patching | SI-2, SI-2(2), CM-11 |

The OpenSCAP scan and its evidence support CA-2, CA-7 and RA-5, and the SHA-256 manifest supports AU-9. The patch playbooks support SI-2, SI-2(2), SI-2(3), CM-3, CM-4 and CP-10.

## Evidence output

`playbooks/evidence.yml` writes one folder per host and run on the control node:

```text
evidence/<run id, UTC>/<host>/
  arf.xml        OpenSCAP ARF results: the record of the scan
  report.html    OpenSCAP HTML report
  report.md      findings for people: counts, expired exceptions, FAIL, WARN, ACCEPTED
  summary.json   scan metadata and counts
  findings.json  every finding, PASS included
  host.json      host, OS release, kernel, profile, scap-security-guide version, oscap exit code
  SHA256SUMS     check with: cd evidence/<run id>/<host> && sha256sum -c SHA256SUMS
```

`oscap` exits with 2 when at least one rule failed. That is a result, not an error, and the playbook treats it as success; exit code 1 (the scan could not run) fails the host.

How `scap_summary.py` maps each rule result, with the title, severity and NIST SP 800-53 references taken from the SCAP Security Guide benchmark inside the ARF file:

| oscap result | Severity | Finding | Listed in report.md |
|---|---|---|---|
| fail | high or medium | FAIL | yes |
| fail | low or unknown | WARN | yes |
| error, unknown | any | WARN (could not evaluate) | yes |
| pass, fixed | any | PASS | findings.json only |
| notapplicable, notselected, notchecked, informational | any | counted, not a finding | count in the header |

### Exceptions

Copy [exceptions.example.yml](exceptions/exceptions.example.yml) to `exceptions/exceptions.yml`. Each entry needs `rule`, `reason`, `owner` and `expires` (YYYY-MM-DD); `hosts` (names or patterns such as `web-*`) and `reference` are optional. JSON with the same fields also works.

A FAIL or WARN with a matching exception becomes ACCEPTED until the end of its expiry date. After that the finding counts again with its original status, and `report.md` lists the exception under "Expired exceptions". The scan keeps reporting accepted rules, which is intended. Exceptions for rules that now pass are listed so they can be closed.

The tool also runs on its own:

```bash
python3 tools/scap_summary.py evidence/<run id>/<host>/arf.xml \
  --host <host> --exceptions exceptions/exceptions.yml --sha256sums --fail-on high
```

Exit codes: 0 summarised, 1 the input could not be read, 3 the `--fail-on` threshold was met.

### Patch records

`playbooks/patch.yml` writes `reports/patch/<run id>/<host>.json` with the kernel before and after, the dnf transaction IDs, the advisories applied and still outstanding, whether the host rebooted, and the rollback commands. `<host>.dnf-history.txt` keeps `dnf history info` for the transaction, and `advisories.yml` lists what the run applied so the next ring can take exactly that set. `playbooks/patch_report.yml` writes `reports/compliance/<run id>/compliance.md` with each host's outstanding errata by severity and the overdue ones against the SLA (Critical 7 days, Important 30, Moderate and Low 31; 2 days for a CVE listed in a KEV file given to `tools/patch_report.py --kev`).

## Rollback

Every area is tagged, so roll back only what broke. Set the area off for the host (for example `rhel_baseline_firewall: false`) so the next run leaves it alone, then revert by hand, or restore the snapshot taken in the window.

| Area | Revert by hand |
|---|---|
| `ssh` | RHEL 9: delete `/etc/ssh/sshd_config.d/40-baseline.conf` and `systemctl restart sshd` from the console. RHEL 8: remove the block between the `# BEGIN rhel_baseline managed block` and `# END rhel_baseline managed block` markers in `/etc/ssh/sshd_config`, then restart sshd |
| `auth` | `authselect disable-feature with-faillock` (and `without-nullok`); `faillock --user <name> --reset` for a locked account; remove `/etc/profile.d/50-rhel-baseline-tmout.sh` and `/etc/sudoers.d/50-rhel-baseline` |
| `kernel` | Delete `/etc/sysctl.d/50-rhel-baseline.conf` and run `sysctl --system`, or set the key in `rhel_baseline_sysctl_overrides` and re-run the tag; delete `/etc/modprobe.d/50-rhel-baseline.conf` to allow the modules |
| `firewall` | `firewall-cmd --permanent --zone=<zone> --add-service=<service>` and `firewall-cmd --reload` for a service that was removed |
| `selinux` | Find the denial with `ausearch -m AVC -ts recent` and fix the file context (`semanage fcontext`, `restorecon`) or the boolean. Set `rhel_baseline_selinux_state: permissive` only as a short-term measure; do not disable SELinux |
| `audit` | Delete `/etc/audit/rules.d/50-rhel-baseline.rules` and run `augenrules --load` (after a reboot if the rules were immutable); `grubby --update-kernel=ALL --remove-args="audit=1 audit_backlog_limit=8192"` |
| `aide` | Delete `/etc/cron.d/rhel_baseline_aide`; `dnf remove aide` if it is not wanted at all |
| `crypto` | `update-crypto-policies --set <previous policy>` and reboot; `fips-mode-setup --disable` and reboot |
| `services` | `systemctl unmask <unit>` and `systemctl enable --now <unit>`; reinstall a removed package with `dnf install` |
| `patching` | `systemctl disable --now dnf-automatic.timer` on ring 0 |
| Patches | `dnf history undo <transaction id>` from the patch record; for a kernel, boot the previous one from GRUB and `grubby --set-default /boot/vmlinuz-<version>`; anything worse, restore the recovery point |

## Tests

```bash
python3 -m unittest discover -s tools/rhel-hardening/tests      # from the repository root
```

The tests use small hand-made ARF, XCCDF, exception and `dnf updateinfo` fixtures in `tests/fixtures`. Static checks used before a release:

```bash
cd tools/rhel-hardening
for p in playbooks/*.yml; do ansible-playbook -i inventory/hosts.example.yml --syntax-check "$p"; done
ansible-lint
```

## License

The code in this folder is under the MIT License; see [LICENSE](LICENSE). The rest of the repository keeps its own license.

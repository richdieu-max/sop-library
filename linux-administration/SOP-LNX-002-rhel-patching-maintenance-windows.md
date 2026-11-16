# SOP-LNX-002 · Patching RHEL servers in rings, with maintenance windows and rollback

Keep RHEL 8 and 9 servers inside the patch SLA without surprise outages. Security errata go to a test ring first and to production in maintenance windows. Reboots happen only when `dnf needs-restarting` says one is needed, and every run leaves a record of what changed and how to undo it. This is the Linux counterpart of [SOP-EM-005](../endpoint-management/SOP-EM-005-windows-update-rings-patch-compliance.md).

**Family:** Linux administration · **Covers:** patch rings, the SLA clock, errata selection with `dnf updateinfo`, an Ansible patch play with serial batches and health checks, live kernel patching, rollback with `dnf history`, and compliance reporting · **Does not cover:** content lifecycle in Red Hat Satellite (a note at the end says what changes when Satellite is used), or major version upgrades (Leapp).

## Shape

![Errata published by Red Hat flow into three rings: ring 0 test servers patched automatically by dnf-automatic within a day, ring 1 non-production in the weekly window, ring 2 production in the monthly window plus emergency windows for critical errata; each ring runs the Ansible patch play in serial batches with a health check, and the compliance report counts outstanding security errata against the SLA](diagrams/sop-lnx-002-1.svg)

| Ring | Hosts | When | How |
|---|---|---|---|
| 0 · Test | Lab copies of each server role | Daily | `dnf-automatic`, security updates applied (the `patching` area of [rhel-hardening](https://github.com/richdieu-max/rhel-hardening)) |
| 1 · Non-production | Dev, test, staging | Weekly window, Tuesday 20:00 | Ansible patch play, all security errata at least 3 days old |
| 2 · Production | Production | Monthly window, plus an emergency window for critical errata | Ansible patch play, the errata that passed ring 1 |

| Severity (Red Hat) | SLA from release to production |
|---|---|
| Critical | 7 days, or 48 hours if exploited in the wild (CISA KEV) |
| Important | 30 days |
| Moderate and low | Next monthly window |

## Before you start

| Item | Requirement |
|---|---|
| Subscriptions | Hosts registered (`subscription-manager status`) and able to reach their repositories or Satellite |
| Change | Standard change for rings 0 and 1; a normal change for each production window, `CHG0012348` |
| Backups | A recovery point from the last 24 hours ([SOP-AWS-004](../aws-procedures/SOP-AWS-004-multi-region-backup-disaster-recovery.md) or the hypervisor equivalent), or a snapshot for single-server systems |
| Health checks | Each server role has a check the play can run (a URL, a port, a service, a query) |
| Load balancing | Clustered roles leave a pool before they are patched; the play uses `serial` so one batch at a time is out |

## Steps

### Before the window

1. **See what is outstanding** on a sample host from each role:

   ```bash
   dnf updateinfo summary --security          # counts by severity
   dnf updateinfo list --security --sec-severity Critical,Important
   dnf updateinfo info RHSA-2026:0001         # the advisory, CVEs and packages
   ```

2. **Check ring 1.** Confirm that ring 1 ran clean last week, and that no application owner reported a problem.

### In the window (Ansible)

```yaml
- name: Patch production, two hosts at a time
  hosts: ring2_web
  become: true
  serial: 2
  max_fail_percentage: 0
  tasks:
    - name: Apply security errata
      ansible.builtin.dnf:
        name: "*"
        security: true
        state: latest
      register: patched

    - name: Is a reboot needed?
      ansible.builtin.command: dnf needs-restarting -r
      register: needs_reboot
      changed_when: false
      failed_when: needs_reboot.rc not in [0, 1]

    - name: Reboot when needed
      ansible.builtin.reboot:
        reboot_timeout: 900
      when: needs_reboot.rc == 1

    - name: Health check
      ansible.builtin.uri:
        url: "https://{{ inventory_hostname }}/health"
        status_code: 200
      retries: 10
      delay: 15
      register: health
      until: health.status == 200
```

`serial: 2` with `max_fail_percentage: 0` stops the play after the first batch that fails its health check, so the rest of production keeps running unpatched while you investigate.

![The patch SLA clock from Red Hat's advisory to production for critical, important and moderate errata, with the ring gates in between; and the rollback path: dnf history undo for a package regression, boot the previous kernel from GRUB for a kernel regression, restore from backup for anything else](diagrams/sop-lnx-002-2.svg)

### Kernel fixes without a reboot

For critical kernel CVEs between windows, live patching applies the fix to the running kernel:

```bash
dnf install kpatch-dnf && dnf kpatch auto     # subscribe to live patches for the running kernel
kpatch list                                   # loaded live patches
```

Live patches cover only selected critical and important kernel CVEs, and only for supported kernel releases. The full kernel update and reboot still happen in the next window.

## Verify

1. `dnf updateinfo list --security --sec-severity Critical,Important` returns nothing on every patched host.
2. `dnf history info last` shows the transaction, with the package versions before and after.
3. The compliance report (Insights, Satellite, or `dnf updateinfo summary --security` collected by Ansible) shows each ring within its SLA.

## Roll back

| What broke | Undo |
|---|---|
| A package update | `dnf history undo <transaction-id>` restores the previous versions, if they are still in the repositories |
| A new kernel | Pick the previous kernel in the GRUB menu (from the console), then make it the default with `grubby --set-default /boot/vmlinuz-<version>` |
| Anything worse | Restore the recovery point or snapshot taken before the window |

RHEL keeps three kernels by default (`installonly_limit=3` in `/etc/dnf/dnf.conf`), so there is always a previous one to boot.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `dnf updateinfo` lists nothing on a host that is clearly behind | No updateinfo metadata: the host is on a mirror without errata, or not registered. Check `subscription-manager repos --list-enabled` |
| The play stops after the first batch | A health check failed. The batch is patched and the rest are not, so fix forward on that batch or roll it back, then continue |
| `needs-restarting -r` says a reboot is needed every time | A core library or the kernel was updated and the host has not rebooted since; reboot it in the window |
| Packages held back | A version lock (`dnf versionlock list`) or `exclude=` in a repository file. Confirm the hold is still wanted |

**With Red Hat Satellite:** rings become lifecycle environments (Test → Non-production → Production), and the errata promoted to each environment become the content view versions. The patch play stays the same, and the SLA report comes from Satellite's errata views.

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | SI-2, SI-2(2), SI-2(3) | Flaw remediation with a measured time from release to install |
| | CM-3, CM-4 | Changes tested in earlier rings and approved before production |
| | CP-10 | A defined rollback for each kind of failure |
| NIST CSF 2.0 | ID.RA-01, PR.PS-02 | Vulnerabilities identified; software maintained |
| CIS Critical Security Controls v8 | 7.3, 7.4 | Automated OS patch management and remediation |

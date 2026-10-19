# SOP-AZ-107 · Validating logging and proving every alert fires

Inventory the log sources and retention, confirm the archive is immutable, and fire every alert rule with a harmless, reversible action so each one is matched to its who, what and when in the workspace. A rule that has never fired may have a typo in its operation name, point at the wrong scope or email a mailbox nobody reads; the only proof is to make it fire.

**Family:** Azure landing zone series · **Covers:** log source inventory, retention and archive lock state, alert rule review, a controlled alert-fire test and the audit trail · **Does not cover:** building the alert rules or the workspace.

## Flow

Nobody trusts a smoke alarm because it has a green light. You press the test button and listen. This procedure presses the button on every alert.

![A script in a dedicated test resource group makes reversible changes; the activity log records who, what and when, Log Analytics receives it, the alert rule fires and the action group reaches a person, while data export keeps a 7-year record in the WORM archive; each fire is then matched to its timestamp](diagrams/sop-az-107-1.svg)

| Source | Captured by | Where it goes |
|---|---|---|
| Subscription activity log | Diagnostic setting | Workspace |
| Root management group activity log | Diagnostic setting set by API | Workspace |
| Key Vault, storage, vaults | Resource diagnostic settings (audit) | Workspace |
| VM syslog and performance | Azure Monitor Agent and a data collection rule | Workspace |
| Long-term record | Data export | WORM archive |

## Before you start

| Item | Requirement |
|---|---|
| Read logs and rules | Log Analytics Reader and Monitoring Reader; no write |
| Fire alerts | Contributor on a dedicated test resource group, only with written approval and only for the window |
| Receive alerts | Member of the action group mailbox, or a copy of it |
| Risk | The alert test makes real changes, even though each is reversed. Run it only inside a written test window and only in a dedicated test resource group |
| Test resource group | Name agreed and tagged |

## Steps

1. **Inventory the log sources.** For each resource open **Monitoring › Diagnostic settings** and confirm a setting sends audit logs to the central workspace. Repeat for the subscription (Activity log export) and the root management group (template only). Run KQL query 1 to see which tables are actually receiving rows.

   ```kql
   union withsource=Table *
   | where TimeGenerated > ago(1d)
   | summarize Rows = count(), Last = max(TimeGenerated) by Table
   | order by Rows desc
   ```

2. **Record retention.** Open the workspace › **Settings › Tables** (or **Usage and estimated costs › Data retention**) and record interactive and total retention. Open the archive storage account › **Containers** and record each container's time-based retention policy and lock state.
3. **List the alert rules.** Open **Monitor › Alerts › Alert rules**. Expect one activity-log alert per destructive or privileged operation, plus scheduled-query rules for guardrail changes and the workload.
4. **Fire every alert.** With written approval run `SOP-07-alert-test.ps1` in the dedicated test resource group. Each action is harmless and reversed at the end (create and delete a lock, add and remove an NSG rule), and the script writes a test log with the UTC time of each action.

   ```powershell
   function Mark($what) { $log.Add([pscustomobject]@{ Action = $what;
     UtcTime = (Get-Date).ToUniversalTime().ToString('o'); By = (Get-AzContext).Account.Id }) }
   New-AzResourceGroup -Name $TestRg -Location $Location -Tag @{ Owner='<owner>'; Client='<client>' } | Out-Null
   $nsg = New-AzNetworkSecurityGroup -Name nsg-alerttest -ResourceGroupName $TestRg -Location $Location; Mark 'write-nsg'
   New-AzResourceLock -LockName test-lock -LockLevel CanNotDelete -ResourceGroupName $TestRg -Force | Out-Null
   Remove-AzResourceLock -LockName test-lock -ResourceGroupName $TestRg -Force | Out-Null; Mark 'del-lock'
   Remove-AzResourceGroup -Name $TestRg -Force | Out-Null; Mark 'cleanup'
   $log | Export-Csv "./alert-test-log-$(Get-Date -Format yyyyMMddTHHmmZ).csv" -NoTypeInformation
   ```

5. **Match fires to the log and close out.** Wait 5 to 15 minutes. In **Monitor › Alerts** confirm each rule fired. In the workspace run KQL query 2 to show who, what and when for each test action, and put the alert time beside the action time. Remove the test resource group, confirm its delete fired its own alert, and hash the test log into the manifest. Record every time in UTC from the platform, not from a laptop clock: that is what makes the trail contemporaneous under ALCOA+ and 21 CFR Part 11.

   ```kql
   AzureActivity
   | where TimeGenerated > ago(7d)
   | where CategoryValue == "Administrative" and ActivityStatusValue in~ ("Success", "Succeeded")
   | where OperationNameValue has_any ("/delete", "roleAssignments/write", "policyAssignments", "policyExemptions", "locks/")
   | project TimeGenerated, Caller, CallerIpAddress, OperationNameValue, _ResourceId, CorrelationId
   | order by TimeGenerated desc
   ```

The query template set also holds the guardrail-change alert query (scheduled query rule, severity 1, every 15 minutes), a Key Vault data-plane access summary, and a query that lists every fired alert with its timestamp for the test evidence.

## Verify

| Check | Pass |
|---|---|
| Alerts | Every alert rule has a fired timestamp in the test log |
| Audit trail | Activity log rows show caller, operation and UTC time for each test action |
| Archive | Archive containers show a time-based retention policy; lock state recorded |
| Clean-up | Test resource group removed and its delete is in the log |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Alert never fires | Operation name typo, wrong scope (subscription vs management group) or the rule is disabled |
| Alert fires but no email | Action group email not confirmed, or the mailbox filters it |
| Guardrail change not in the workspace | Root management group diagnostic setting missing |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | AU-2, AU-3 Event logging and content | Sources inventoried; caller, operation and time captured |
| | AU-6, SI-4 Review and system monitoring | Every alert fired once and matched to its log row |
| | AU-8 Time stamps | Platform UTC times, not a laptop clock |
| | AU-9, AU-11 Protection and retention | Immutable archive; retention recorded |
| ISO/IEC 27001:2022 | A.8.15, A.8.16, A.8.17 | Logging; monitoring activities; clock synchronisation |
| HIPAA Security Rule | 164.312(b) | Audit controls recording activity |
| 21 CFR Part 11 | §11.10(e) | Secure, time-stamped audit trail of who, what and when |

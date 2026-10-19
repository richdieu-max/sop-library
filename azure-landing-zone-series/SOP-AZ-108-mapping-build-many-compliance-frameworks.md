# SOP-AZ-108 · Mapping one build to many compliance frameworks

Build one control matrix and crosswalk across NIST CSF 2.0, NIST SP 800-53 R5, ISO/IEC 27001:2022, the HIPAA Security Rule and a PCI DSS boundary attestation, with every row backed by hashed evidence. Auditors for different frameworks ask different questions about the same thing; if each framework gets its own evidence the work multiplies and the answers drift apart.

**Family:** Azure landing zone series · **Covers:** policy and Defender compliance exports, the crosswalk, a PCI DSS boundary attestation and the evidence package · **Does not cover:** a PCI assessment, or controls the build does not implement.

## How it fits together

A single receipt can support expense claims in several departments. The control is the purchase, the evidence file is the receipt, and each framework column is a department that files it.

![Policy and Defender exports, hashed into a manifest, back one crosswalk row (an internal control ID, its Azure implementation and its evidence file), which maps to NIST CSF 2.0, NIST SP 800-53 R5, ISO/IEC 27001:2022, the HIPAA Security Rule and a PCI DSS v4 boundary column](diagrams/sop-az-108-1.svg)

| Framework | Granularity | Source of the mapping |
|---|---|---|
| NIST CSF 2.0 | Outcomes (for example DE.CM-09) | Framework text |
| NIST SP 800-53 R5 | Controls (AU-2) | Azure initiative groups |
| ISO/IEC 27001:2022 | Annex A controls (A.8.15) | Azure initiative groups |
| HIPAA Security Rule | Safeguards (164.312(b)) | HITRUST/HIPAA initiative |
| PCI DSS v4 | Requirements; boundary only here | Attestation letter |

## Before you start

| Item | Requirement |
|---|---|
| Export compliance | Reader and Security Reader at the root; read only |
| Add standards in Defender | Security Admin on the subscription; adds a view and changes no resource |
| Accept the mapping | Client approver, who signs the PCI boundary letter |
| Initiatives | Framework initiatives assigned in Audit (SOP-AZ-101) |
| Evidence | Evidence manifest from the build and validation runs |
| Risk register | Current |
| Rule | Map only what is built. Do not add rows for controls the build does not implement: a crosswalk that claims more than the evidence shows fails at the first sample |

## Steps

1. **Export policy compliance per initiative.** Open **Policy › Compliance**, set the scope to the product root and select each framework initiative. Use **Export to CSV**, or run `SOP-08-compliance-export.ps1` to export every initiative with its control groups.

   ```powershell
   param([string]$RootMg = '<org>-<product>', [string]$Out = './compliance-export')
   foreach ($a in 'nist-800-53-r5','iso-27001','hipaa-hitrust','pci-dss','cis-azure-foundations') {
     Get-AzPolicyState -ManagementGroupName $RootMg -Filter "PolicyAssignmentName eq '$a'" -Top 5000 |
       Select-Object @{n='Control';e={$_.PolicyDefinitionGroupNames -join ';'}}, PolicyDefinitionName,
         ComplianceState, @{n='Resource';e={($_.ResourceId -split '/')[-1]}} |
       Export-Csv "$Out/02-$a.csv" -NoTypeInformation
   }
   Get-ChildItem $Out | Get-FileHash -Algorithm SHA256 |
     Select-Object Hash, @{n='File';e={Split-Path $_.Path -Leaf}} | Export-Csv "$Out/MANIFEST.csv" -NoTypeInformation
   ```

   The script also writes `01-summary-by-initiative.csv` with non-compliant resource and policy counts per assignment.
2. **Add the standards in Defender for Cloud.** Open **Defender for Cloud › Regulatory compliance › Manage compliance standards** and select the subscription. Add NIST SP 800-53 R5, ISO 27001, HIPAA HITRUST and PCI DSS v4, then use **Download report** for each.
3. **Write and map the control rows.** In `SOP-08-crosswalk.template.csv` write one row per built control, with the Azure implementation and the evidence file. Fill the five framework columns: use the initiative group names first, then check each against the framework text.

   ```csv
   Control ID (internal),Control statement,NIST CSF 2.0,NIST SP 800-53 R5,ISO/IEC 27001:2022 Annex A,HIPAA Security Rule,PCI DSS v4 (boundary),Azure implementation,Evidence file,Status
   LOG-01,Activity log streamed to central workspace,DE.CM-09,AU-2 / AU-6,A.8.15,164.312(b),10.2.1,activity-to-law diagnostic setting,diag-settings.json,Built
   NET-01,No public IPs on network interfaces,PR.IR-01,SC-7,A.8.20,164.312(e)(1),1.3.1,deny-nic-public-ip policy,policy-compliance.csv,Built
   BAK-01,Backups geo-redundant to paired region,PR.DS-11,CP-9,A.8.13,164.308(a)(7)(ii)(A),N/A,RSV GRS + cross-region restore,rsv-config.json,Built
   ```

4. **Write the PCI boundary attestation.** State that card data is handled by the payment processor and is not stored, processed or transmitted by the tenant. List the controls that keep it that way (hosted payment page or redirect, no card fields, limited egress). Say plainly this is a boundary statement, not a PCI assessment. Scope is a control: a clear boundary keeps the tenant out of PCI scope, and any change that lets card data touch the platform reopens it.
5. **Package the evidence.** Hash every export into one manifest and reference its version from the crosswalk. Move every non-compliant row to the risk register, not into a footnote.

## Verify

| Check | Pass |
|---|---|
| Evidence | Every crosswalk row names an evidence file in the manifest |
| Gaps | Non-compliant counts in the export match the risk register |
| PCI | The PCI letter names the processor boundary and is signed |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Initiative shows no control groups | Older initiative version. Reassign the current built-in version |
| Defender and Policy numbers differ | Different scopes or evaluation times. Export both at the same scope on the same day |
| Auditor rejects a mapping | The control is mapped by name only. Add the evidence file and the exact setting it proves |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST CSF 2.0 | GV.OC, GV.PO | Organisational context and policy expressed as one control set across frameworks |
| NIST SP 800-53 R5 | CA-2 Control assessments | Each built control assessed against exported evidence |
| | CA-7 Continuous monitoring | Policy and Defender compliance exported per framework |
| | PL-2 System security and privacy plans | One crosswalk records how each control is implemented |
| ISO/IEC 27001:2022 | 6.1.3, 9.2 | Risk treatment and statement of applicability inputs; internal audit evidence |
| HIPAA Security Rule | 164.308(a)(1)(ii)(A), 164.308(a)(8) | Risk analysis and periodic evaluation |
| PCI DSS v4 | 12.5.2 | Scope documented in a signed boundary attestation |

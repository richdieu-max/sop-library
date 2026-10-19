# SOP Library · Field Guide Series

**36 standard operating procedures · 802 pages · 12 technology families**

Step-by-step field guides from my work across Microsoft Azure, Entra ID, Intune, security operations, regulated (GxP) lab IT and Windows support. Each one teaches the concepts first, then gives the procedure in the portal, as PowerShell / CLI, and at scale (Group Policy, Intune, templates), and ends with verification, rollback, troubleshooting and the control frameworks it supports.

> **Sanitized reference edition.** Client names, hostnames, tenant IDs and ticket numbers are replaced with placeholders (Contoso, documentation IP ranges, sample change numbers). Microsoft's own built-in role, policy and app IDs are left as they are because the scripts need them.

![Skill map: nine areas of work and the SOPs that document each one](diagrams/skill-map.svg)

Start with the **[catalog and index (SOP-000)](SOP-000_SOP_Library_Catalog_and_Index.pdf)**, or jump to a family below. PDFs open in the browser.

## Catalog


### Identity & Access

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| ID-001 | [Building a Conditional Access and MFA Baseline in Microsoft Entra ID](identity-access/SOP-ID-001_Building_a_Conditional_Access_and_MFA_Baseline_in_Microsoft_Entra_ID.pdf) | Replace security defaults with a named, testable Conditional Access set: emergency access, legacy auth blocked, MFA for all, phishing-resistant MFA for admins. | 23 |
| ID-002 | [Managing the Joiner-Mover-Leaver Account Lifecycle in Microsoft Entra ID](identity-access/SOP-ID-002_Managing_the_Joiner-Mover-Leaver_Account_Lifecycle_in_Microsoft_Entra_ID.pdf) | Joiner-mover-leaver driven from the HR record: birthright access and a Temporary Access Pass on hire, access moved on role change, clean offboarding. | 24 |

### Endpoint Management

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| EM-001 | [Deploying Defender for Endpoint to macOS with Intune](endpoint-management/SOP-EM-001_Deploying_Defender_for_Endpoint_to_macOS_with_Intune.pdf) | Defender for Endpoint on macOS five ways (Intune, Graph PowerShell, Settings Catalog, local script, Jamf Pro), verified down to mdatp health. | 27 |
| EM-002 | [Enrolling macOS Devices into Microsoft Intune](endpoint-management/SOP-EM-002_Enrolling_macOS_Devices_into_Microsoft_Intune.pdf) | macOS enrollment: Company Portal, Automated Device Enrollment through Apple Business Manager, direct enrollment, plus a readiness check script. | 27 |
| EM-003 | [Enforcing Multi Admin Approval for Intune Wipe Retire Delete](endpoint-management/SOP-EM-003_Enforcing_Multi_Admin_Approval_for_Intune_Wipe_Retire_Delete.pdf) | Two-person rule for Intune wipe, retire and delete, in the admin center or Graph PowerShell, with a request-notification flow. | 24 |
| EM-004 | [Provisioning Windows Devices with Windows Autopilot and Intune](endpoint-management/SOP-EM-004_Provisioning_Windows_Devices_with_Windows_Autopilot_and_Intune.pdf) | Windows Autopilot end to end: hardware hash, ZTDId dynamic group, deployment profile and Enrollment Status Page, sealed laptop to user. | 22 |
| EM-005 | [Managing Windows Update Rings and Patch Compliance with Intune](endpoint-management/SOP-EM-005_Managing_Windows_Update_Rings_and_Patch_Compliance_with_Intune.pdf) | Update rings with Windows Update for Business: pinned feature versions, expedited zero-day fixes, driver control, monthly patch compliance against an SLA. | 24 |

### Endpoint Agents & Protection

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| EP-001 | [Deploying an Endpoint Management Agent Tanium Client](endpoint-agents/SOP-EP-001_Deploying_an_Endpoint_Management_Agent_Tanium_Client.pdf) | Install, register and verify an endpoint management agent (Tanium) manually, silently, remotely and at scale with Intune Win32 or ConfigMgr. | 21 |
| EP-002 | [Removing a Legacy Antivirus Agent Before EDR Migration](endpoint-agents/SOP-EP-002_Removing_a_Legacy_Antivirus_Agent_Before_EDR_Migration.pdf) | Remove a legacy antivirus agent (Trend Micro) before EDR migration, by console, vendor tool or scripted mass removal, then prove it is gone. | 22 |

### Security Operations

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| SEC-001 | [Running a Vulnerability Remediation Program with Qualys and Microsoft Defender](security-operations/SOP-SEC-001_Running_a_Vulnerability_Remediation_Program_with_Qualys_and_Microsoft_Defender.pdf) | Vulnerability remediation with Qualys and Microsoft Defender: one reconciled queue, exploit-led priorities, SLAs by tier, dated exceptions. | 23 |
| SEC-002 | [Containing a Compromised Microsoft 365 Account](security-operations/SOP-SEC-002_Containing_a_Compromised_Microsoft_365_Account.pdf) | Contain a compromised Microsoft 365 account: preserve evidence, contain in a fixed order across Entra ID and Exchange Online, scope, recover. | 23 |

### Governance & Compliance

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| GOV-001 | [Change Control and Objective Evidence for GxP and 21 CFR Part 11 Systems](governance/SOP-GOV-001_Change_Control_and_Objective_Evidence_for_GxP_and_21_CFR_Part_11_Systems.pdf) | Change control for GxP and 21 CFR Part 11 systems: classify, assess impact, plan test and rollback, e-signed Quality approval, objective evidence. | 25 |

### Microsoft Azure · Procedures

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| AZ-001 | [Creating and Securing a Microsoft Azure Tenant](azure-procedures/SOP-AZ-001_Creating_and_Securing_a_Microsoft_Azure_Tenant.pdf) | Create a tenant and apply a security and governance baseline four ways: portal, Graph + Az PowerShell, Azure CLI / Bicep, configuration as code. | 28 |
| AZ-002 | [Deploying a Hardened Azure VM in a Data Residency Region](azure-procedures/SOP-AZ-002_Deploying_a_Hardened_Azure_VM_in_a_Data_Residency_Region.pdf) | Trusted Launch Windows Server VM with encryption at host, no public IP, backup and monitoring, kept in-region by Azure Policy. | 27 |
| AZ-003 | [Cloning an Azure Virtual Machine](azure-procedures/SOP-AZ-003_Cloning_an_Azure_Virtual_Machine.pdf) | Clone a VM: snapshot to managed disk to new VM via portal, PowerShell, CLI or Compute Gallery, with secure access and rollback. | 19 |
| AZ-004 | [Azure Point-to-Site VPN with Entra ID](azure-procedures/SOP-AZ-004_Azure_Point-to-Site_VPN_with_Entra_ID.pdf) | Point-to-site VPN with Entra ID sign-in: an MFA-protected OpenVPN tunnel into a private network, plus certificate auth and the user connection. | 28 |
| AZ-005 | [Multi-Region Backup and Disaster Recovery in Azure](azure-procedures/SOP-AZ-005_Multi-Region_Backup_and_Disaster_Recovery_in_Azure.pdf) | Two-region backup and DR for VMs and SQL with Azure Backup, Veeam for Azure and Site Recovery, proven by restore testing. | 27 |

### Microsoft Azure · Landing Zone Build & Assessment Series

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| AZ-101 | [Building an Azure Landing Zone as Code](azure-landing-zone-series/SOP-AZ-101_Building_an_Azure_Landing_Zone_as_Code.pdf) | Landing zone as code: management groups, group-based RBAC, Policy guardrails, central logging with an immutable archive, hub network. | 17 |
| AZ-102 | [Deploying a Repeatable Customer Stamp](azure-landing-zone-series/SOP-AZ-102_Deploying_a_Repeatable_Customer_Stamp.pdf) | A repeatable customer stamp: private spoke, Key Vault read by managed identity, customer-managed disk keys, geo-redundant backup. | 15 |
| AZ-103 | [Threat Modeling an Azure Build with STRIDE](azure-landing-zone-series/SOP-AZ-103_Threat_Modeling_an_Azure_Build_with_STRIDE.pdf) | STRIDE threat model of the deployed build: trust boundaries, data flows and attack surface reviewed at every boundary. | 11 |
| AZ-104 | [Hardening Identity and Access in Azure](azure-landing-zone-series/SOP-AZ-104_Hardening_Identity_and_Access_in_Azure.pdf) | Identity hardening: Entra groups, roles at management group scope, PIM, Conditional Access and a role-to-permission matrix tested with real accounts. | 11 |
| AZ-105 | [Scanning for Secrets and Supply-Chain Risk](azure-landing-zone-series/SOP-AZ-105_Scanning_for_Secrets_and_Supply-Chain_Risk.pdf) | Secrets and supply chain: gitleaks, Trivy and Dependabot across full history, a licence inventory and a Key Vault posture check. | 10 |
| AZ-106 | [Assessing Network Segmentation and Container Hosting](azure-landing-zone-series/SOP-AZ-106_Assessing_Network_Segmentation_and_Container_Hosting.pdf) | Network segmentation and container hosting: effective routes, NSG rules, public exposure, host hardening, scored against CIS and Defender for Cloud. | 10 |
| AZ-107 | [Validating Logging and Proving Every Alert Fires](azure-landing-zone-series/SOP-AZ-107_Validating_Logging_and_Proving_Every_Alert_Fires.pdf) | Logging validation: source inventory, retention, alerts on destructive actions, immutability, and a controlled test that fires every alert. | 12 |
| AZ-108 | [Mapping One Build to Many Compliance Frameworks](azure-landing-zone-series/SOP-AZ-108_Mapping_One_Build_to_Many_Compliance_Frameworks.pdf) | One control matrix crosswalked to NIST CSF 2.0, SP 800-53 R5, ISO 27001:2022, HIPAA and a PCI DSS boundary, every row backed by hashed evidence. | 10 |

### Microsoft 365

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| M365-001 | [Migrating File Shares to Teams and SharePoint](microsoft-365/SOP-M365-001_Migrating_File_Shares_to_Teams_and_SharePoint.pdf) | File shares to Teams and SharePoint: scan, clean up, migrate with Migration Manager or SPMT (GUI and PowerShell), then cut over. | 29 |

### Cloud Migration

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| MIG-001 | [Lift and Shift Migration of a Label Printing Server](cloud-migration/SOP-MIG-001_Lift_and_Shift_Migration_of_a_Label_Printing_Server.pdf) | Rehost a BarTender label server with AWS Application Migration Service or Azure Migrate, or rebuild it, with tested cutover and rollback. | 27 |

### Regulated Lab IT

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| LAB-001 | [Modernizing a Windows 7 Lab Application onto Windows 11](regulated-lab-it/SOP-LAB-001_Modernizing_a_Windows_7_Lab_Application_onto_Windows_11.pdf) | Move an instrument-control application off Windows 7 onto Windows 11: compatibility mode, shims, isolated Hyper-V and more. | 27 |
| LAB-002 | [Installing Registering and Patching a Lab Compliance Data Agent](regulated-lab-it/SOP-LAB-002_Installing_Registering_and_Patching_a_Lab_Compliance_Data_Agent.pdf) | Register, install, connect and hotfix a GxP data-capture agent interactively, silently, remotely (BeyondTrust PRA) and at scale. | 27 |
| LAB-003 | [Requesting and Provisioning a Regulated GxP Lab Workstation](regulated-lab-it/SOP-LAB-003_Requesting_and_Provisioning_a_Regulated_GxP_Lab_Workstation.pdf) | A regulated lab workstation from funding to retirement: standard, qualified, break-fix and decommission paths through ITSM. | 26 |

### Label Printing

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| LBL-001 | [Fixing Undersized Labels Zebra DPI Mismatch](label-printing/SOP-LBL-001_Fixing_Undersized_Labels_Zebra_DPI_Mismatch.pdf) | Fix undersized labels caused by a Zebra driver DPI mismatch via Print Management, PowerShell, PrintUI/pnputil or print-server policy. | 28 |
| LBL-002 | [Static IP Reservation and Network Label Printer Integration](label-printing/SOP-LBL-002_Static_IP_Reservation_and_Network_Label_Printer_Integration.pdf) | Give a network label printer a reserved address and connect it to Windows, BarTender and the LIMS, four ways. | 23 |

### Windows Desktop Support

| SOP | Title | What it covers | Pages |
|---|---|---|---|
| WIN-001 | [Troubleshooting USB Serial COM Port Connectivity](windows-support/SOP-WIN-001_Troubleshooting_USB_Serial_COM_Port_Connectivity.pdf) | USB-to-serial and COM port repair five ways: Device Manager, CMD, PowerShell with pnputil, a power-management fix, Intune Remediations. | 28 |
| WIN-002 | [Restoring DHCP Client and Domain Connectivity](windows-support/SOP-WIN-002_Restoring_DHCP_Client_and_Domain_Connectivity.pdf) | From "no network, no domain" back to working: Services and Event Viewer, sc / ipconfig / nltest, a PowerShell repair, a controlled rejoin. | 26 |
| WIN-003 | [Restoring Mapped Network Drive Access](windows-support/SOP-WIN-003_Restoring_Mapped_Network_Drive_Access.pdf) | Restore mapped drives on Windows 11: Workstation service and SMB client, net use / cmdkey, SMB cmdlets, Group Policy or Intune at scale. | 27 |
| WIN-004 | [Windows Command Line Toolkit for Support Engineers](windows-support/SOP-WIN-004_Windows_Command_Line_Toolkit_for_Support_Engineers.pdf) | The everyday Windows support commands in CMD and PowerShell, run remotely with Invoke-Command and at scale with Intune Remediations. | 24 |

## What every procedure contains

| Chapter | What you get |
|---|---|
| Concepts you need first | The model behind the task, with figures, so the steps make sense and can be adapted |
| Access, prerequisites and planning | Minimum roles, licensing, a prerequisites checklist and a risk table |
| Methods | The procedure in the portal or GUI, then as PowerShell / CLI / KQL, then at scale |
| Verification, rollback, troubleshooting | A checklist that proves the result, the safe way back, symptom → cause → fix tables |
| Summary, glossary and review | Key points, review questions, terms and the control frameworks supported |

## Coverage by framework

| NIST SP 800-53 Rev. 5 family | Procedures |
|---|---|
| AC · Access Control | ID-001, ID-002, AZ-104, EM-003, AZ-004 |
| IA · Identification and Authentication | ID-001, AZ-001, AZ-004, AZ-104 |
| PS · Personnel Security | ID-002 |
| CM · Configuration Management | GOV-001, EM-002, EM-004, EM-005, LAB-001, LAB-003, AZ-101, AZ-102, EP-001 |
| SI · System and Information Integrity | EM-005, SEC-001, EM-001, EP-002, LAB-002 |
| RA · Risk Assessment | SEC-001, AZ-103 |
| IR · Incident Response | SEC-002 |
| AU · Audit and Accountability | AZ-107, SEC-002, GOV-001 |
| CP · Contingency Planning | AZ-005, AZ-003 |
| SC · System and Communications Protection | AZ-002, AZ-004, AZ-106, LBL-002 |
| SA / SR · Acquisition and Supply Chain | AZ-105, GOV-001 |
| CA · Assessment, Authorization and Monitoring | AZ-108, SEC-001 |

| Regulation or benchmark | Procedures |
|---|---|
| FDA 21 CFR Part 11 / EU GMP Annex 11 (GxP) | GOV-001, LAB-001, LAB-002, LAB-003, ID-001 |
| CIS Microsoft 365 / Intune benchmarks | ID-001, EM-002, EM-005 |
| CIS Critical Security Controls v8 (Control 7) | SEC-001, EM-005 |

## Related

- [endpoint-identity-runbooks](https://github.com/richdieu-max/endpoint-identity-runbooks): short-form versions of AZ-001, AZ-004, AZ-005, EM-001 and EM-003
- [azure-posture-check](https://github.com/richdieu-max/azure-posture-check): the read-only evidence script referenced by the AZ-1xx series
- [security-assessment-toolkit](https://github.com/richdieu-max/security-assessment-toolkit): the workbook behind AZ-103 to AZ-108

---

© Rich Dieu IT Solutions LLC · [richdieu.com](https://richdieu.com).

# SOP-AZ-103 · Threat modeling an Azure build with STRIDE

Find the trust boundaries, data flows and attack surface of a deployed Azure environment and review each boundary with STRIDE, from the infrastructure and identity layer only. Every threat ends up with a control and evidence, or a rated, registered gap the client signs off.

**Family:** Azure landing zone series · **Covers:** a read-only inventory, boundary mapping, STRIDE per boundary, risk rating and client sign-off · **Does not cover:** application code review, or out-of-scope systems such as the payment processor.

## How it fits together

A threat model answers four questions: what are we protecting, where can it be attacked, what could go wrong, and what stops it. For an infrastructure review the answers come from what is deployed (networks, identities, vaults, gateways), not from source code. Think of a building inspector who walks the doors between areas with different owners rather than opening every drawer: a trust boundary is one of those doors, and STRIDE is the checklist read at each one.

![Users reach the App Gateway WAF in the hub (B1), the gateway reaches the app VM in the spoke (B2), the VM reads Key Vault over a private endpoint (B3) and calls integrations through NAT (B4), operators write to the control plane (B5) and backups copy to the paired region (B6); the six STRIDE questions are asked at each boundary](diagrams/sop-az-103-1.svg)

| ID | Boundary | What crosses it |
|---|---|---|
| B1 | Internet to gateway | User and webhook HTTPS |
| B2 | Gateway to app VM | HTTP on the app port |
| B3 | App VM to Key Vault | Secret reads over the private endpoint |
| B4 | App VM to internet egress | Calls to integrations on 443 |
| B5 | Operator to control plane | Role, policy and resource writes |
| B6 | Backup to paired region | Recovery points |

| Letter | Threat | Question at the boundary |
|---|---|---|
| S | Spoofing | Can someone pretend to be a trusted caller? |
| T | Tampering | Can data be changed in transit or at rest? |
| R | Repudiation | Could someone deny doing it, for lack of a log? |
| I | Information disclosure | Can data reach someone who should not see it? |
| D | Denial of service | Can the service be overwhelmed or cut off? |
| E | Elevation of privilege | Can a low role become a high one? |

## Before you start

| Item | Requirement |
|---|---|
| Read the environment | Reader at the product root; no step needs write access |
| Network topology | Reader plus Network Watcher in the region (Network Watcher is enabled per region) |
| Approve the model | A named client approver with authority to accept risk |
| Independence | The reviewer is not the person who built the environment. The builder attends the workshop to answer design questions but does not rate their own work |
| Inputs | Design document and data flow diagrams from the build; risk matrix agreed (likelihood 1 to 3, impact 1 to 3) |
| Workshop | Booked with the builder, the reviewer and a client representative |
| Scope | Out-of-scope items written down (for example payment processor, application code) |

## Steps

1. **Inventory the environment.** Run `SOP-03-architecture-inventory.ps1` with Reader access; it changes nothing. It writes networks, peerings, NSG rules, public IPs, private endpoints and each managed identity's roles to one JSON file. Record the printed SHA-256 hash in the workshop notes.

   ```powershell
   param([string]$Out = "./threat-model-inputs-$(Get-Date -Format yyyyMMdd).json",
         [string]$ResourceGroupLike = '<product>-*')
   $rgs = Get-AzResourceGroup | Where-Object ResourceGroupName -like $ResourceGroupLike
   $inv = [ordered]@{}
   $inv.PublicIPs = Get-AzPublicIpAddress | Select-Object Name, ResourceGroupName,
       @{n='AttachedTo';e={$_.IpConfiguration.Id -replace '.*/providers/',''}}
   $inv.PrivateEndpoints = Get-AzPrivateEndpoint | Select-Object Name,
       @{n='Target';e={($_.PrivateLinkServiceConnections.PrivateLinkServiceId -split '/')[-1]}}
   # ... VNets and peerings, NSG rules, managed identity role assignments ...
   $inv | ConvertTo-Json -Depth 6 | Set-Content $Out
   Get-FileHash $Out -Algorithm SHA256 | Select-Object Hash, Path   # record with the workshop notes
   ```

2. **See how the resources connect.** Open the stamp resource group › **Resource visualizer** and confirm which resources talk to which: VM to NIC to subnet, private endpoints to vault and storage, disk set to vault. For the network view open **Network Watcher › Topology**.
3. **Mark the trust boundaries.** List every place data crosses from one zone of control to another, starting from B1 to B6 above. Open each spoke **Virtual network › Peerings** to confirm which networks can reach which. The spoke should peer only with the hub; with no spoke-to-spoke path, customer stamps cannot reach each other.
4. **Run STRIDE per boundary.** Ask the six questions at every boundary. Write one row per real threat in `SOP-03-threat-model.template.csv`, with the existing control and the evidence file that proves it. A threat with no control is a gap: leave the control column empty rather than guessing.

   ```csv
   Boundary ID,Boundary,From (zone),To (zone),Data crossing,STRIDE,Threat,Existing control (evidence),Gap,Likelihood (1-3),Impact (1-3),Rating,Risk ID
   B1,Internet to gateway,Internet,Hub: gateway subnet,HTTPS requests,S,Spoofed client / credential stuffing on the sign-in path,WAF rate-limit rule on /api/auth (WAF policy export),WAF in Detection until UAT ends,2,3,High,R-xx
   B4,App VM to internet egress,Spoke: app subnet,Internet (NAT),HTTPS to integrations,I,Data exfiltration to any host on 443,NAT gateway + NSG 443 outbound,No FQDN allow-list,2,3,High,
   ```

   If the review finds data already at risk (for example an open inbound rule to a data port), report it to the client within one business day; do not wait for the final report.
5. **Rate, register and sign off.** Rate each row as likelihood times impact: 7 to 9 High, 4 to 6 Medium, 1 to 3 Low. Every High row gets a risk register ID and an owner role. Walk the client approver through the boundaries and gaps, and record approval with name, role and date on the sign-off page.

## Verify

| Check | Pass |
|---|---|
| Boundary coverage | Every boundary in the diagram has at least one row |
| Evidence | Every control names an evidence file that exists and is hashed |
| Risk register | Every High row has a risk register ID |
| Approval | The sign-off page is signed |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Resource visualizer is empty | The account lacks Reader on the resource group, or the browser blocked the blade. Use the inventory JSON |
| Topology shows no peerings | Network Watcher is not enabled in that region, or the hub is in another subscription you cannot read |
| Workshop stalls on application questions | Write them down as out of scope with an owner; the infrastructure model does not answer them |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST CSF 2.0 | ID.RA | Risks to the deployed environment identified, rated and registered |
| NIST SP 800-53 R5 | RA-3 Risk assessment | Likelihood times impact rating per threat, with client sign-off |
| | SA-8 Security engineering principles | Trust boundaries reviewed against the design |
| | SA-11 Developer testing and evaluation | Independent reviewer; the builder does not rate their own work |
| ISO/IEC 27001:2022 | A.5.7, A.8.27 | Threat intelligence applied to the build; secure architecture principles checked at each boundary |

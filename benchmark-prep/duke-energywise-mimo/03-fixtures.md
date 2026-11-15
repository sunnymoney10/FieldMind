# Synthetic MIMO fixture guide

Twenty fictional records are labeled MIMO-S01 through S20. They are not actual Brian-list records, examples derived from customer data or current Duke program claims. Addresses use fictional unit labels, `Exampleton, ZZ 00000`; account/device references begin SYN/SYNTH. Source URLs use the reserved `.invalid` domain and must not be fetched.

Researcher inputs: `fixtures/prospects.synthetic.json` and `source-packets.synthetic.json`. Reviewer-only expected distinctions: `reviewer-key.synthetic.json`. Do not show the key while timing the researcher. All sixty snippets are written fixtures, not retrieved evidence. Even a clear synthetic listing is source-reported information, not an automatically accepted identity or verified authority.

| IDs | Main rehearsal challenge |
|---|---|
| S01–S05 | Exact suite support, shared building, uncertain rebrand, vacancy contradiction/DNC, single candidate acceptance |
| S06–S10 | Multiple historical references, possible simultaneous meters, unclassified premise/account ID, neighbor-suite account, account hold |
| S11–S15 | Old thermostat columns, building-only permit, renovation contradiction, landlord/shared facilities hypothesis, old comfort report |
| S16–S20 | Owner/account authority split, corporate/local operator split, ambiguous building restriction, partial release, explicit release retained |

Every record has independent fields for:

- **Historical participation:** what the old fictional list reports about the previous occupant/account; unknown effective dates stay null.
- **Historical equipment:** original Device/Thermostat labels, including empty fields; `remains_installed` and current compatibility remain unknown.
- **Current occupant:** candidate names and exact suite uncertainty; no automatic accepted business ID.
- **Current account:** no current account reference is established; historical references do not prove a sequence, continuity or who is authorized now.
- **Current HVAC:** actual installed equipment, controls and thermostat count remain unknown; building permits and hypotheses are separately sourced.
- **Current program eligibility:** always `not_established`; current official rule/version is null.

Five authority categories stay separate: business ownership, business operations, utility-account authority, property authority and HVAC/facilities authority. Some fixtures support a qualified hypothesis; none converts that into verified decision authority. The key tests correct restraint as well as useful sourced information.

The twenty synthetic records have sixteen hypothetical research candidates and four gate-only controls. This is deliberate; it is not a shortcut to a sixteen-case real benchmark. All real-processing permissions remain ungranted for every fixture. Do not import this preparation format into the live application or the B2A repository proof.

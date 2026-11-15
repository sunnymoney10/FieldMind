# Test list 001: results (Nov 14, 2026)

The list was built from real public Raleigh businesses with made-up premise IDs, account numbers and device fields. It follows Brian's CSV format and contains none of his records. The answer key (`reviewer/answer_key.md`) was written before any pipeline research. The same agent wrote the key and ran the research, so this is a functional test, not a blind accuracy measurement.

| Row | Trap | What FieldMind showed | Result |
|---|---|---|---|
| T1 505 W Jones St, listed "Tobacco Road Sports Cafe" | Turnover | Occupant is **Clouds Brewing** (found), with "Listed as: Tobacco Road" kept as list information. Tobacco Road is marked closed (historical). First question: "Who owns Clouds Brewing, and do they decide on the utility account?" | Pass |
| T2 4325 Glenwood Ave, listed "Brio Italian Grille" | Turnover, chain, mall with 200+ tenants | **Disputed**. Brio's own page still lists the location (undated) against dated closure reports from Sep 2025 and Oct 2026. Maggiano's is pending. The mall has many tenants, and Macerich is the landlord. Label: "Occupant unconfirmed". | Pass |
| T3 8831 Six Forks Rd, listed "Zest Cafe" | Turnover with a future tenant | Zest closed at the end of 2025. Paris Baguette (franchisee) is targeting summer 2027. The landlord lists the space as available. No current operator. | Pass |
| T4 305 Church at North Hills St Ste 900, listed "Marshall & Taylor PLLC" | Wrong suite | Suite 900 is not confirmed. Sources placing the firm in Suite 1250 are **not merged** and are listed as alternatives. First question: "Sources put Marshall & Taylor PLLC at … Suite 1250, not Ste 900. Is the list's suite out of date, or is a different business in Ste 900?" | Pass |
| T5 "Do Not Contact" row | Suppression | Skipped by `pilot.py prepare` and never researched. The app shows "Suppressed on list". | Pass |

**Score: 5 of 5 traps handled.** Three of those passes depend on rule fixes made during this test (see below).

## Measured
- **Time per premise:** 30, 37, 47 and 57 seconds. The median is 47 s, against a 1,200 s cap. That's agent time only; a person checking the brief isn't included.
- **Effort:** 2–3 searches and 0–1 page fetch per premise. No retrieval failures.
- **Cost:** $0 extra.
- **App import:** schema valid, 4 of 4 matched. The list was unchanged: nothing was added, approved or unsuppressed. No page errors.

## Problems found, and what changed
1. **Old owners carried over to the new business (T1).** An inference that Tobacco Road's owners decide for Clouds Brewing was accepted. Fixed: inferences can no longer assign decision authority, or move facts from one business to another.
2. **Other mall tenants accepted (T2).** With no suite on the list, a different tenant in another suite (Fleming's, Ste 5004) was accepted as a candidate occupant. Fixed: at a multi-tenant address with no suite on the list, another business named in a specific suite is rejected.
3. **Mismatches not shown to the rep (T4).** The worker rejected the Suite 1250 sources correctly, but the brief didn't say why. Fixed: Question 1 now lists the alternatives that weren't merged, and Question 5 asks about the suite mismatch.
4. **My own extraction miss (T3).** I left the address field off the franchisee claim, so the worker rejected a valid claim. I left the run as it was rather than fixing it after the fact.

Worker tests: 24 of 24 pass, including new tests for fixes 1 and 2. Pilot helper tests: 6 of 6 pass. The Videri control run was rebuilt and is unchanged.

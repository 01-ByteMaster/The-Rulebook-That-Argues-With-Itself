# Planted Contradictions — Tracking Doc

**Not ingested by the retrieval pipeline.** This is a reference doc for the build/test team to confirm the corpus contains exactly the contradictions the spec requires, and to know what a correct `conflict` response should cite for each.

---

## Contradiction 1 — `CG-ATTENDANCE` (3-way group)

| Section ID | File | Claim |
|---|---|---|
| `ATT-2` | `01_attendance_policy.md` | Minimum attendance to sit the exam is **75%**. |
| `ATT-5-MEDICAL` | `01_attendance_policy.md` | With an approved medical certificate, minimum attendance drops to **60%**. |
| `EXAM-7-COMMITTEE` | `exam_regulations.pdf` | The Examination Committee may **waive the attendance requirement entirely**, at its discretion, independent of the 75%/60% figures. |

**Test question:** *"What is the minimum attendance percentage I need to sit my exam?"* <br>
**Expected response type:** `conflict` <br>
**Expected passages cited:** all three of the above (`conflict_group: CG-ATTENDANCE`) <br>
**Why it's a genuine contradiction, not just detail-layering:**
**Explanation :** All three sections speak to the same question — "what attendance % do I need?" — and give three different, not-obviously-reconcilable answers (a hard floor, a reduced floor for one subgroup, and a discretionary override that can go below both). None of the three sections cross-references or subordinates the others, so a reader following any single section would come away with a different, confidently-stated number.

---

## Contradiction 2 — `CG-HOSTEL-REFUND` (2-way group, independent topic)

| Section ID | File | Claim |
|---|---|---|
| `HOSTEL-4-REFUND-A` | `02_hostel_handbook.md` | Deposit refunds are processed **within 15 working days** of vacating + no-dues sign-off. |
| `FEE-5-REFUND-B` | `fee_deadlines_table.md` | No refunds of any kind are processed **after the 10th of the month** in which the student vacates, regardless of exit date — which can silently override or delay the 15-working-day promise depending on when in the month a student leaves. |

**Test question:** *"If I leave the hostel early, when do I get my deposit back?"* <br>
**Expected response type:** `conflict` <br>
**Expected passages cited:** both of the above (`conflict_group: CG-HOSTEL-REFUND`) <br>
**Why it's a genuine contradiction:** 
**Explanation** : `HOSTEL-4-REFUND-A` promises a fixed, predictable turnaround measured from the student's own paperwork completion. `FEE-5-REFUND-B` imposes a hard monthly batch cutoff that is indifferent to that timeline and can push the actual refund out well past 15 working days depending on when in the month the student vacates. A student cannot combine the two into one consistent answer — the two sections use different, uncoordinated clocks. 

---

## Contradiction 3 — `CG-SCHOLARSHIP-RENEWAL` (2-way group, independent topic)

| Section ID | File | Claim |
|---|---|---|
| `SCH-4-GPA-A` | `03_scholarship_policy.md` | Renewal requires CGPA ≥ **6.5**, assessed **annually** (end of second semester). |
| `SCH-6-GPA-B` | `03_scholarship_policy.md` | Satisfactory standing for continued support requires CGPA ≥ **7.0**, assessed **every semester**. |

**Test question:** *"What GPA do I need to keep my scholarship?"* <br>
**Expected response type:** `conflict` <br>
**Expected passages cited:** both of the above (`conflict_group: CG-SCHOLARSHIP-RENEWAL`) <br>
**Why it's a genuine contradiction:** different numeric thresholds (6.5 vs. 7.0) AND different assessment cadences (annual vs. every semester), issued by different offices (Financial Aid vs. Registrar) with no explicit statement of which one governs. A student at, say, 6.8 CGPA in one semester would be "fine" under SCH-4-GPA-A's logic and "flagged" under SCH-6-GPA-B's.

---

## Non-contradictions to watch for (should NOT be misclassified as conflicts)

These are topically adjacent to the above but are deliberately consistent — the retrieval/classification layer should not accidentally group them:

- `ATT-3` (attendance calculation method) and `ATT-4` (shortage notification tiers at 85%/80%/75%) are procedural detail, not competing thresholds — both agree the operative eligibility floor is 75% (before the medical/committee exceptions). `conflict_group: null` for both.
- `HOSTEL-8` mentions the refund process (`HOSTEL-4-REFUND-A`) in the context of disciplinary cancellation, but doesn't restate a different number — it's a cross-reference, not a second claim. `conflict_group: null`.
- `SCH-5` (suspension/cancellation grounds) references both GPA sections but doesn't assert its own threshold. `conflict_group: null`.
- `FEE-4` (tuition refund window: full refund in weeks 1–2, 50% in weeks 3–6, none after) is a genuinely different refund (tuition, not hostel deposit) with its own internally consistent tiered schedule — it should not be pulled into `CG-HOSTEL-REFUND`. `conflict_group: null`.

# Running the FieldMind pilot on your computer (option A)

You need a Mac or PC with Python 3.11+ and Claude Code.

1. Unzip `fieldmind-worker.zip` into a folder you control, for example `~/FieldMind`.
2. Optional, but it fixes the blocked-page gap:
   `pip install crawl4ai && crawl4ai-setup`
3. Check the setup with the synthetic data:
   `python3 tests/test_worker.py && python3 tests/test_pilot.py`
4. Put Brian's CSV in the folder. Then prepare research folders. Start with 2, not 20:
   `python3 pilot/pilot.py prepare brian_list.csv runs --limit 2`
   This writes only refs, names and addresses. Suppressed rows are skipped and listed in `runs/prepare-log.json`.
5. Open Claude Code in the folder and say: "Start the FieldMind pilot on the prepared runs." It reads `CLAUDE.md` and follows its rules.
6. When it's done, run:
   `python3 pilot/pilot.py merge runs pilot-research.json`
   Import that file in FieldMind (center button, then Import).
7. Check each brief against what you see in the field. Use the field-check questions on the visit form.

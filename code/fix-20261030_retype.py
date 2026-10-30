#!/usr/bin/env python3
"""nm000413 fix-20261030: retype depth contacts recorded on Nihon Kohden scalp/system slots.

Evidence is the channel-name sequence of each released file (the release's own channel lists):
  rule A  'EEG <S><n>-Ref' or 'POL <S><n>' typed EEG, where the same file has SEEG contacts 'POL <S><m>'
          of the same shaft label <S>  -> SEEG (the shaft continues on the NK 'EEG ...-Ref' slots,
          e.g. EEG A1-Ref, EEG A2-Ref, POL A3 ... POL A10; EEG F1-Ref ... EEG F10-Ref, POL F11 ... POL F16;
          P029: EEG Fp1-Ref, EEG Fp2-Ref, POL Fp3 ... POL Fp12)
  rule B  'POL E<n>' (plain integer n) typed MISC, when the file has >= 4 such contacts numbered 1..N
          without gaps and no other unprimed 'E' shaft -> SEEG (shaft E between D and F; 'POL E' without a
          number, the Nihon Kohden system reference input, stays MISC; 'POL E<n>-<k>' stays MISC).
  rule C  label 'Fp' numbered above 2 (no scalp position Fp3+) with numbers 1..N without gaps -> depth shaft
          'Fp' (used through rule A).
  rule D  'EEG <L><n>-Ref' (single letter L, n = 1..N, N >= 6) filling an alphabetical gap in the file's shaft
          letters (L-1 and L+1 are shafts, L is not) -> shaft L (P010, P020: F1-F8/F10 between E and G).
  Rule A also covers 'EEG <S><n>-Ref' typed EEG when POL <S> continues the numbering (Tp7-Tp10-Ref in P029).
Rows that change get status_description unchanged; only the 'type' column changes. Prints a TSV log.
"""
import csv, glob, io, os, re, sys
from collections import defaultdict

root = sys.argv[1]
log = []
for f in sorted(glob.glob(f"{root}/sub-*/ieeg/*_channels.tsv")):
    txt = open(f, newline="").read()
    rows = list(csv.reader(io.StringIO(txt), delimiter="\t"))
    hdr = rows[0]; ti = hdr.index("type"); ni = hdr.index("name")
    seeg_shafts = defaultdict(set); via = {}
    for r in rows[1:]:
        m = re.fullmatch(r"POL (.+?)(\d+)", r[ni])
        if m and r[ti] == "SEEG":
            seeg_shafts[m.group(1)].add(int(m.group(2)))
    # rule C: label 'Fp' with contact numbers above 2 (Fp3...: no such scalp position in the 10-20/10-10
    # systems) -> a depth shaft named Fp; its contacts 1..N (EEG Fp1-Ref, EEG Fp2-Ref, POL Fp3 ...) are SEEG
    # when the numbers run 1..N without gaps.
    fp = sorted(int(m.group(2) or m.group(4)) for r in rows[1:]
                for m in [re.fullmatch(r"(?:EEG (Fp)(\d+)-Ref|POL (Fp)(\d+))", r[ni])] if m)
    if fp and max(fp) > 2 and fp == list(range(1, len(fp) + 1)):
        seeg_shafts["Fp"].update(fp); via["Fp"] = "C"
    e_nums = sorted(int(m.group(1)) for r in rows[1:] for m in [re.fullmatch(r"POL E(\d+)", r[ni])] if m and r[ti] == "MISC")
    e_ok = len(e_nums) >= 4 and e_nums == list(range(1, len(e_nums) + 1)) and "E" not in seeg_shafts
    # rule D: 'EEG <L><n>-Ref' with a single capital letter L, n = 1..N without gaps (N >= 6), where L itself is
    # not an SEEG shaft but the letters before and after it are (an alphabetical gap in the shaft names, e.g. P010
    # and P020: shafts A B C D [E] G H I, with EEG F1-Ref ... EEG F8-Ref on the scalp slots) -> shaft L, SEEG.
    have = set(k for k in seeg_shafts if re.fullmatch(r"[A-Z]", k)) | ({"E"} if e_ok else set())
    fam = defaultdict(list)
    for r in rows[1:]:
        m = re.fullmatch(r"EEG ([A-Z])(\d+)-Ref", r[ni])
        if m and r[ti] == "EEG":
            fam[m.group(1)].append(int(m.group(2)))
    for L, nums in fam.items():
        nums = sorted(nums)
        if L not in have and len(nums) >= 6 and nums == list(range(1, len(nums) + 1)) \
                and chr(ord(L) - 1) in have and chr(ord(L) + 1) in have:
            seeg_shafts[L].update(nums); via[L] = "D"
    changed = 0
    for r in rows[1:]:
        name, typ = r[ni], r[ti]
        m = re.fullmatch(r"(?:EEG (.+?)(\d+)-Ref|POL (.+?)(\d+))", name)
        new = None
        if m and typ == "EEG":
            shaft = m.group(1) or m.group(3)
            if shaft in seeg_shafts:
                new, rule = "SEEG", via.get(shaft, "A")
        if typ == "MISC" and e_ok and re.fullmatch(r"POL E\d+", name):
            new, rule = "SEEG", "B"
        if new:
            log.append((os.path.relpath(f, root), name, typ, new, rule)); r[ti] = new; changed += 1
    if changed:
        out = io.StringIO(); w = csv.writer(out, delimiter="\t", lineterminator="\n"); w.writerows(rows)
        open(f, "w", newline="").write(out.getvalue())
w = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
w.writerow(["file", "name", "old_type", "new_type", "rule"]); w.writerows(log)

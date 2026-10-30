"""Units n/a receipt: unit statements in the release, header and table units, and the stored-to-table band-power ratios.

Usage: python 2026-10-30_units-na.py <nm000413 root> <nm000413 git clone> <PR head> <dir with the release sourcedata>
"""

import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import h5py
import mne
import numpy as np
import openpyxl
import pandas as pd
import scipy.io
import scipy.signal

REV = "origin/main"
TABLES = "derivatives/dre-lzsh-results/1f -results"
SOURCE = "sourcedata/zenodo-17272689"
# bands and mains-bin replacement as in code/dre-lzsh-release/1f code/fit_whole copy.ipynb
BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "l_gamma": (30, 80),
    "hf": (80, 500),
}
CLOSE = (0.5, 2.0)
UNIT = re.compile(
    r"\bunits?\b|volt|[µμu]v\b|\bmv\b|\bnv\b|\bgains?\b|calib|physical|dimension|\bscal(e|ed|ing)\b",
    re.IGNORECASE,
)
SMALL = 100_000  # MAT variables above this many elements are signal matrices, not metadata


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def git(clone: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else "n/a"


def blob(clone: Path, rev: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", clone, "show", f"{rev}:{rel}"], capture_output=True, check=True).stdout


def same_as_main(clone: Path, rel: str, path: Path) -> bool:
    """sha256 = git-annex key for annexed files, byte-identical blob otherwise."""
    pointer = blob(clone, REV, rel)
    if pointer.startswith(b"/annex/objects/SHA256E-"):
        return pointer.rsplit(b"--", 1)[-1].startswith(sha256(path).encode())
    return path.read_bytes() == pointer


def strings(x) -> list[str]:
    """Field names and text values of a loaded MAT variable."""
    if isinstance(x, scipy.io.matlab.mat_struct):
        return [s for f in x._fieldnames for s in (f, *strings(getattr(x, f)))]
    if isinstance(x, np.ndarray) and x.dtype == object:
        return [s for e in x.flat for s in strings(e)]
    if isinstance(x, np.ndarray) and x.dtype.kind == "U":
        return [str(e) for e in x.flat]
    return [x] if isinstance(x, str) else []


def mat_layout(path: Path) -> tuple[str, list[str]]:
    """Variable layout (names, classes, struct fields) and the names and strings of every non-signal variable."""
    if h5py.is_hdf5(path):
        parts, texts = [], []

        def visit(name, obj):
            cls = obj.attrs.get("MATLAB_class", b"").decode()
            texts.append(name)
            if not name.startswith("#refs#"):
                parts.append(f"{name}({cls})")
            if isinstance(obj, h5py.Dataset) and cls == "char" and obj.size <= SMALL:
                texts.append("".join(map(chr, obj[()].ravel())))

        with h5py.File(path) as h:
            h.visititems(visit)
        return "v7.3: " + " ".join(sorted(parts)), texts
    variables = scipy.io.whosmat(path)
    small = [n for n, shape, _ in variables if np.prod(shape) <= SMALL]
    mat = scipy.io.loadmat(path, variable_names=small, struct_as_record=False, squeeze_me=True)
    parts, texts = [], []
    for name, _, cls in variables:
        fields = getattr(mat.get(name), "_fieldnames", None)
        parts.append(f"{name}({cls}{'{' + ','.join(fields) + '}' if fields else ''})")
        texts += [name, *(strings(mat[name]) if name in mat else [])]
    return " ".join(sorted(parts)), texts


def xlsx_rows(path: Path) -> list[tuple]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return [row for ws in wb.worksheets for row in ws.iter_rows(values_only=True)]


def xlsx_strings(path: Path) -> list[str]:
    return [v for row in xlsx_rows(path) for v in row if isinstance(v, str)]


def unit_hits(texts) -> list[str]:
    return sorted({t for t in texts if UNIT.search(t)})


def release_sources(clone: Path, source_root: Path) -> None:
    files = git(clone, "ls-tree", "-r", "--name-only", REV, "--", SOURCE).splitlines()
    layouts, hits, n_same = Counter(), {}, 0
    for rel in files:
        if rel.endswith(".json"):  # in git
            record = json.loads(blob(clone, REV, rel))
            texts = [str(v) for v in record.get("metadata", record).values()]
            layouts["Zenodo record JSON (title, description, ...)"] += 1
        else:
            path = source_root / rel
            n_same += same_as_main(clone, rel, path)
            layout, texts = mat_layout(path) if rel.endswith(".mat") else ("xlsx", xlsx_strings(path))
            layouts[layout] += 1
        if found := unit_hits(texts):
            hits[rel] = found
    print(f"\n## Release files under {SOURCE} at {REV}: {len(files)} (other than the JSON, same as {REV}: {n_same})")
    print("| layout (variables with MATLAB class and struct fields) | files |")
    print("|---|---:|")
    for layout, n in sorted(layouts.items(), key=lambda kv: -kv[1]):
        print(f"| {layout} | {n} |")
    print(f"files with a unit/scale/gain name or text: {len(hits)} {hits}")


def release_code_and_tables(clone: Path, head: str, root: Path) -> None:
    code = git(clone, "ls-tree", "-r", "--name-only", head, "--", "code/dre-lzsh-release").splitlines()
    hits = {}
    for rel in code:
        text = blob(clone, head, rel).decode("utf-8", errors="replace")
        if rel.endswith(".ipynb"):  # cell sources and text outputs
            cells = json.loads(text)["cells"]
            outputs = [o.get("text", o.get("data", {}).get("text/plain", "")) for c in cells for o in c.get("outputs", [])]
            text = "\n".join("".join(x) for x in [c["source"] for c in cells] + outputs)
        if found := unit_hits(text.splitlines()):
            hits[rel] = found
    print(f"\n## Release code at the PR head: {len(code)} files; files with a unit/scale/gain word: {len(hits)} {hits}")
    tables = sorted((root / "derivatives").rglob("*.xlsx"))
    n_same = sum(same_as_main(clone, p.relative_to(root).as_posix(), p) for p in tables)
    columns = sorted({str(v) for p in tables for v in xlsx_rows(p)[0]})
    hits = {p.relative_to(root).as_posix(): f for p in tables if (f := unit_hits(xlsx_strings(p)))}
    print(f"## Release result tables (derivatives): {len(tables)} xlsx, same as {REV}: {n_same}")
    print(f"column names: {columns}")
    print(f"tables with a unit/scale/gain word in any cell: {len(hits)} {hits}")


def units_at_head(clone: Path, head: str, root: Path) -> None:
    tsvs = [t for t in git(clone, "ls-tree", "-r", "--name-only", head).splitlines() if t.endswith("_channels.tsv")]
    rows = pd.concat(pd.read_csv(io.BytesIO(blob(clone, head, t)), sep="\t", dtype=str, keep_default_na=False)
                     for t in tsvs)
    same = sum(blob(clone, head, t) == blob(clone, REV, t) for t in tsvs)
    print(f"\n## channels.tsv at the PR head {git(clone, 'rev-parse', head)}: {len(tsvs)} files, "
          f"byte-identical to {REV}: {same}")
    print(f"rows per (type, units): {rows.groupby(['type', 'units']).size().to_dict()}")
    vhdrs = sorted(root.glob("sub-*/ieeg/*_ieeg.vhdr"))
    units, n_same = Counter(), 0
    for p in vhdrs:
        n_same += same_as_main(clone, p.relative_to(root).as_posix(), p)
        section = p.read_text(encoding="utf-8").split("[Channel Infos]")[1].split("\n[")[0]
        units.update(line.split(",")[-1] for line in section.splitlines() if re.match(r"Ch\d+=", line))
    print(f"headers: {len(vhdrs)} .vhdr, sha256 = annex key: {n_same}; channel-record units: {dict(units)}")


def band_power(x: np.ndarray, sfreq: float) -> pd.DataFrame:
    freqs, psd = scipy.signal.welch(x, fs=sfreq, nperseg=int(sfreq))
    for col in np.arange(50, psd.shape[1] - 50, 50):
        for i in range(-3, 3):
            psd[:, col + i] = (psd[:, col + i - 1] + psd[:, col + i + 1]) / 2
    return pd.DataFrame({b: psd[:, (freqs >= lo) & (freqs <= hi)].mean(1) for b, (lo, hi) in BANDS.items()})


def compare(root: Path, clone: Path, state: str) -> pd.DataFrame:
    rows, unmatched, n_same = [], [], 0
    for scans in sorted(root.glob("sub-*/sub-*_scans.tsv")):
        sub = scans.parent.name[4:]
        folder = root / TABLES / f"{state} state" / sub
        tables = {p.name.lower(): p for p in folder.glob("*.xlsx")}
        for run in pd.read_csv(scans, sep="\t").query("state == @state").itertuples():
            stem = Path(run.source_file).stem.lower()
            names = (f"{stem}.xlsx", f"{stem}_psd.xlsx", f"new_{stem}.xlsx")
            table = next((tables[n] for n in names if n in tables), None)
            if table is None:
                unmatched.append(f"{sub} {stem}")
                continue
            vhdr = scans.parent / run.filename
            eeg = vhdr.with_suffix(".eeg")
            n_same += same_as_main(clone, eeg.relative_to(root).as_posix(), eeg)
            # header unit 'unscaled', resolution 1: MNE returns the stored values
            raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
            ours = band_power(raw.get_data(), raw.info["sfreq"])
            ours.index = pd.Index(raw.ch_names)
            theirs = pd.read_excel(table).drop_duplicates("channel_name")
            theirs = theirs.set_index("channel_name")[list(BANDS)]
            common = ours.index.intersection(theirs.index)
            ratio = ours.loc[common] / theirs.loc[common].astype(float)
            rows.append(ratio.assign(sub=sub, run=vhdr.name))
    ratios = pd.concat(rows)
    print(f"\n## {state}: {ratios.run.nunique()} runs with a same-name table, sha256 = annex key: {n_same}")
    print(f"runs without a same-name table: {', '.join(unmatched)}")
    return ratios


def summarize(ratios: pd.DataFrame, title: str) -> None:
    per_sub = ratios.groupby("sub")[list(BANDS)].median()
    n_ch = ratios.groupby("sub").size()
    n_runs = ratios.groupby("sub").run.nunique()
    print(f"\n### median (stored / table) band power per participant, {title}")
    print("| sub | runs | channels | " + " | ".join(BANDS) + " |")
    print("|---|---:|---:|" + "---:|" * len(BANDS))
    for sub, r in per_sub.iterrows():
        cells = " | ".join(f"{v:.3g}" for v in r)
        print(f"| {sub} | {n_runs[sub]} | {n_ch[sub]} | {cells} |")
    inside = per_sub.apply(lambda c: c.between(*CLOSE))
    print(f"\nparticipants with the median in [{CLOSE[0]}, {CLOSE[1]}], per band:")
    print(inside.sum().to_dict())
    print(f"in all {len(BANDS)} bands: {inside.all(1).sum()} of {len(per_sub)}")
    print(f"not in all bands: {', '.join(per_sub.index[~inside.all(1)])}")
    print(f"range of the per-participant medians: {per_sub.min().min():.3g} to {per_sub.max().max():.3g}")


def main(root: Path, clone: Path, head: str, source_root: Path) -> None:
    print(f"mne {mne.__version__}, numpy {np.__version__}, scipy {scipy.__version__}, h5py {h5py.__version__}")
    print(f"{REV} of the clone: {git(clone, 'rev-parse', REV)}")
    release_sources(clone, source_root)
    release_code_and_tables(clone, head, root)
    units_at_head(clone, head, root)
    for state in ("ictal", "interictal"):
        summarize(compare(root, clone, state), f"{state} runs")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))

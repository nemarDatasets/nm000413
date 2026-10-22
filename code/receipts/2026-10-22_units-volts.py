"""Welch band power of the stored nm000413 runs vs the release's per-channel PSD tables.

Usage: python 2026-10-22_units-volts.py <nm000413 root> <nm000413 git clone>
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import scipy.signal

REV = "origin/main"
TABLES = "derivatives/dre-lzsh-results/1f -results"
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def git(clone: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else "n/a"


def band_power(x: np.ndarray, sfreq: float) -> pd.DataFrame:
    freqs, psd = scipy.signal.welch(x, fs=sfreq, nperseg=int(sfreq))
    for col in np.arange(50, psd.shape[1] - 50, 50):
        for i in range(-3, 3):
            psd[:, col + i] = (psd[:, col + i - 1] + psd[:, col + i + 1]) / 2
    return pd.DataFrame(
        {
            b: psd[:, (freqs >= lo) & (freqs <= hi)].mean(1)
            for b, (lo, hi) in BANDS.items()
        }
    )


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
            rel = vhdr.with_suffix(".eeg").relative_to(root).as_posix()
            key = git(clone, "cat-file", "-p", f"{REV}:{rel}").rsplit("--", 1)[-1]
            n_same += key.startswith(sha256(root / rel))
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
    n_runs = ratios.run.nunique()
    print(
        f"\n## {state}: {n_runs} runs with a same-name table, sha256 = annex key: {n_same}"
    )
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
    lo, hi = per_sub.min().min(), per_sub.max().max()
    print(f"range of the per-participant medians: {lo:.3g} to {hi:.3g}")
    print(f"max |log10(median)|: {np.abs(np.log10(per_sub)).max().max():.1f}")


def main(root: Path, clone: Path) -> None:
    print(f"mne {mne.__version__}, numpy {np.__version__}, scipy {scipy.__version__}")
    print(f"{REV} of the clone: {git(clone, 'rev-parse', REV)}")
    tsvs = sorted(root.glob("sub-*/ieeg/*_channels.tsv"))
    types = pd.concat(pd.read_csv(p, sep="\t", usecols=["type"]) for p in tsvs)
    print(f"channels.tsv files: {len(tsvs)}")
    print(f"rows per type: {types.type.value_counts().to_dict()}")
    for state in ("ictal", "interictal"):
        summarize(compare(root, clone, state), f"{state} runs")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

# Receipt: channels.tsv units: V for SEEG/EEG/ECG

**Claim**: the stored SEEG/EEG/ECG values are in volts. The release's own code reads the source EDFs with MNE (volts), and its per-channel PSD tables agree with the stored values in scale. The PR sets V on the 19845 SEEG/EEG/ECG rows of the 190 channels.tsv.

**PR**: nemarDatasets/nm000413#3, receipt on top of head `977c5dbc`.

## Source
- Release code: Zenodo record 17272689 (doi:10.5281/zenodo.17272689, `DRE-LZSH.zip`), copied verbatim to `code/dre-lzsh-release/1f code/fit_whole copy.ipynb`. Its sha256 `5d51ddfb…b3c882c7` equals its entry in `sourcedata/b3w2_provenance_c-drelzsh.json`. The lines that make the tables:
  ```
  raw = mne.io.read_raw_edf(file_path,encoding='latin1',preload=True)
  raw.filter(None, 999, fir_design='firwin')
  raw.notch_filter(np.arange(50, s_freqs // 2 - 1, 50), fir_design='firwin',notch_widths=4)
  eeg_data = raw.get_data()[:, start_sample:end_sample]
  freqs, psd = welch(eeg_data, fs=s_freqs, nperseg=s_freqs)
  cols_to_replace = np.arange(50, psd.shape[1]-50, 50)   # each mains bin -3..+2 replaced by the mean of its neighbours
  delta=[0.5,4] theta=[4,8] alpha=[8,13] beta=[13,30] l_gamma=[30,80] hf=[80,500]
  band_power = np.mean(psd[:, band_mask], axis=1)
  ```
  MNE `read_raw_edf` returns volts, so the tables are band powers of volt-scaled signals.
- Tables: `derivatives/dre-lzsh-results/1f -results/{ictal,interictal} state/<P>/*.xlsx` (194 files). Each sha256 equals its entry in `sourcedata/b3w2_provenance_c-drelzsh.json`, checked with `hashlib.sha256` (194/194).
- NEMAR nm000413 `origin/main` `a24b585ad6b41e492d184d765002067bb814d3e4`: the 190 `sub-*/ieeg/*_channels.tsv` and the 182 BrainVision runs compared below. Each `.eeg` sha256 equals its git-annex key at that commit (182/182).

## Method
- Reader: MNE 1.13.2 `read_raw_brainvision`, `get_data()`. The header unit is 'unscaled' with resolution 1, so this returns the stored values with no scaling.
- Runs paired with the release table of the same name in the same state folder (`<stem>.xlsx`, `<stem>_psd.xlsx` or `new_<stem>.xlsx`, case-insensitive). The 8 runs without a same-name table are listed in the result.
- Band power as in the notebook: scipy 1.18.1 `welch(x, fs, nperseg=fs)` on the whole stored run, the same mains-bin replacement and the same six bands. The notebook's 999 Hz low-pass, notch filter and `sz_S..sz_T` crop are not applied, because the crop limits are not released.
- Ratio = stored / table band power per channel (channels matched by name). Per participant: the median ratio per band over all paired runs, counted as close when it is within [0.5, 2]. Volts vs µV differs by 1e6 in amplitude, i.e. 1e12 in power.

## Result
Rows per type in the 190 channels.tsv: SEEG 18368, EEG 1284, ECG 193 (19845 set to V), MISC 1225 (n/a).

Ictal: 91 runs with a same-name table (sha256 = annex key: 91). No table for: P001 sz4-1, P013 sz1, P013 sz3, P017 sz5-1.

| sub | runs | channels | delta | theta | alpha | beta | l_gamma | hf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P001 | 4 | 352 | 0.865 | 0.866 | 0.961 | 0.91 | 1.02 | 1.12 |
| P002 | 4 | 456 | 1.01 | 1.39 | 1.46 | 1.43 | 1.34 | 0.968 |
| P003 | 3 | 408 | 1.13 | 1.37 | 1.45 | 1.45 | 1.34 | 1.47 |
| P004 | 1 | 76 | 1.09 | 1.4 | 1.42 | 1.49 | 0.679 | 0.302 |
| P005 | 3 | 318 | 0.861 | 1.29 | 1.13 | 0.981 | 0.808 | 0.659 |
| P006 | 4 | 424 | 1.25 | 0.848 | 1.25 | 1.3 | 1.27 | 1.37 |
| P007 | 2 | 232 | 0.127 | 0.118 | 0.0924 | 0.0654 | 0.122 | 1.13 |
| P008 | 3 | 276 | 1.03 | 1 | 1 | 1.01 | 1.07 | 1.11 |
| P009 | 2 | 136 | 0.895 | 0.907 | 0.903 | 0.906 | 1.14 | 1.58 |
| P010 | 4 | 440 | 0.794 | 0.832 | 0.896 | 0.976 | 1.06 | 1.1 |
| P011 | 2 | 240 | 0.919 | 0.891 | 0.928 | 0.873 | 0.978 | 0.98 |
| P012 | 5 | 800 | 1.21 | 0.868 | 1.11 | 1.14 | 1.1 | 1.41 |
| P013 | 1 | 102 | 2.81 | 2.51 | 2.04 | 2.42 | 2.26 | 2.81 |
| P014 | 5 | 444 | 4.5 | 0.984 | 0.295 | 0.343 | 0.506 | 0.879 |
| P015 | 1 | 100 | 0.972 | 1.15 | 1.13 | 1.27 | 1.52 | 1.57 |
| P016 | 3 | 360 | 1.27 | 1.14 | 1.15 | 1.31 | 1.4 | 1.34 |
| P017 | 3 | 372 | 1.01 | 1.06 | 1.09 | 1.08 | 1.14 | 1.16 |
| P018 | 5 | 540 | 0.529 | 0.0772 | 0.0222 | 0.0161 | 0.397 | 0.683 |
| P019 | 3 | 348 | 0.873 | 0.799 | 0.771 | 0.767 | 0.858 | 0.889 |
| P020 | 1 | 84 | 0.0946 | 0.00654 | 0.00133 | 0.000841 | 0.00529 | 0.188 |
| P021 | 7 | 616 | 0.927 | 1.02 | 1.19 | 1.37 | 1.18 | 1.14 |
| P022 | 3 | 228 | 0.935 | 0.98 | 1.09 | 1.09 | 1.06 | 1.22 |
| P023 | 4 | 416 | 0.849 | 0.98 | 1.05 | 0.968 | 1.06 | 1.11 |
| P024 | 3 | 342 | 0.85 | 0.951 | 0.968 | 1.02 | 1.15 | 1.1 |
| P025 | 3 | 330 | 0.841 | 0.375 | 0.226 | 0.217 | 0.485 | 1.24 |
| P026 | 3 | 378 | 1.39 | 0.861 | 0.829 | 0.854 | 1.07 | 1.21 |
| P027 | 2 | 292 | 0.738 | 0.858 | 0.944 | 0.896 | 1.06 | 1.21 |
| P028 | 4 | 336 | 0.993 | 0.934 | 1.11 | 1.09 | 1.18 | 1.21 |
| P029 | 3 | 360 | 0.799 | 0.914 | 0.898 | 0.961 | 1.11 | 1.1 |

- All six bands in [0.5, 2] for 22 of 29 participants. The exceptions are P004, P007, P013, P014, P018, P020 and P025.
- Per-participant medians range from 0.000841 to 4.5 (max |log10| 3.1).

Interictal: 91 runs with a same-name table (sha256 = annex key: 91). No table for: P001 sz4, P017 sz4, P017 sz5, P021 sz8-9.

| sub | runs | channels | delta | theta | alpha | beta | l_gamma | hf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P001 | 4 | 352 | 1 | 1 | 1 | 1 | 1.09 | 1.09 |
| P002 | 3 | 342 | 1 | 1 | 1 | 1 | 1.09 | 1.38 |
| P003 | 3 | 408 | 1 | 1 | 1 | 1 | 1.13 | 1.18 |
| P004 | 1 | 76 | 1 | 1 | 1 | 1 | 1.08 | 1.1 |
| P005 | 3 | 318 | 1 | 1 | 1 | 1 | 1.07 | 1.09 |
| P006 | 4 | 424 | 0.833 | 0.942 | 0.904 | 0.961 | 1.05 | 1.11 |
| P007 | 2 | 232 | 1 | 1 | 1 | 1 | 1.1 | 1.17 |
| P008 | 3 | 276 | 1 | 1 | 1 | 1 | 1.07 | 1.09 |
| P009 | 2 | 136 | 1 | 1 | 1 | 1 | 1.08 | 1.1 |
| P010 | 4 | 440 | 0.843 | 0.843 | 0.916 | 0.962 | 1.05 | 1.1 |
| P011 | 2 | 240 | 1 | 1 | 1 | 1 | 1.07 | 1.1 |
| P012 | 5 | 800 | 1 | 1 | 1 | 1 | 1.09 | 1.32 |
| P013 | 1 | 102 | 0.981 | 0.925 | 0.923 | 0.956 | 1.07 | 1.09 |
| P014 | 5 | 444 | 1 | 1 | 1 | 1 | 1.07 | 1.1 |
| P015 | 1 | 100 | 0.826 | 0.891 | 0.916 | 0.968 | 1.13 | 1.1 |
| P016 | 3 | 360 | 1 | 1 | 1 | 1 | 1.08 | 1.11 |
| P017 | 3 | 372 | 1 | 1 | 1 | 1 | 1.06 | 1.09 |
| P018 | 5 | 540 | 0.824 | 0.896 | 0.908 | 0.957 | 1.5 | 2.03 |
| P019 | 3 | 348 | 1 | 1 | 1 | 1 | 1.08 | 1.12 |
| P020 | 2 | 168 | 1 | 1 | 1 | 1 | 1.07 | 1.1 |
| P021 | 6 | 528 | 0.988 | 0.998 | 1 | 1 | 1.07 | 1.09 |
| P022 | 3 | 228 | 1 | 1 | 1 | 1 | 1.22 | 1.11 |
| P023 | 4 | 416 | 0.798 | 0.938 | 0.971 | 0.953 | 1.05 | 1.09 |
| P024 | 3 | 342 | 1 | 1 | 1 | 1 | 1.08 | 1.1 |
| P025 | 3 | 330 | 0.804 | 0.867 | 0.912 | 0.96 | 1.07 | 1.15 |
| P026 | 3 | 378 | 1 | 1 | 1 | 1 | 1.11 | 1.09 |
| P027 | 2 | 292 | 0.837 | 0.884 | 0.905 | 0.978 | 1.1 | 1.14 |
| P028 | 5 | 414 | 1 | 1 | 1 | 1 | 1.06 | 1.09 |
| P029 | 3 | 360 | 1.03 | 0.991 | 0.987 | 0.997 | 1.1 | 1.43 |

- All six bands in [0.5, 2] for 28 of 29 participants (P018 hf 2.03).
- Per-participant medians range from 0.798 to 2.03 (max |log10| 0.3).

Reading:
- Every per-participant ratio is within 3.1 decades of 1. Stored values in µV would put them near 1e12, so the stored values are on the volt scale of the authors' MNE output.
- The interictal tables match almost exactly. Ictal ratios spread more, which is expected because the authors' tables come from a filtered, cropped window (see Method).
- The README at the PR head said "median band-power ratio 0.5-2 in 29/29 participants". It now gives the figures above.

## Coverage
190 of 190 channels.tsv (row types). 182 of 190 runs compared: every run that has a same-name release table (91 ictal + 91 interictal, all 29 participants). The 8 runs without one are listed above.

## Reproduce
```
uv run --no-project --python 3.12 --with mne==1.13.2 --with scipy --with pandas --with openpyxl python code/receipts/2026-10-22_units-volts.py <nm000413 root> <nm000413 git clone>
```
Run on 2026-10-22 (Slurm job 13451104) on a NEMAR copy of the data. The clone, at `origin/main` `a24b585`, was used for the annex keys.

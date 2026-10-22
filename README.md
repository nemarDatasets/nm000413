[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000413-blue)](https://doi.org/10.82901/nemar.nm000413)

# DRE-LZSH: SEEG benchmark dataset for drug-resistant epilepsy

Stereo-EEG (SEEG) segments from **29 patients with drug-resistant epilepsy** (P001-P029). For each patient there are
seizure (ictal) segments and interictal segments, plus clinical information and channel-level epileptogenic-zone (EZ)
annotations. Re-packaged in iEEG-BIDS from the authors' public release (Zenodo record
[17272689](https://doi.org/10.5281/zenodo.17272689), "DRE-LZSH: A SEEG Benchmark Dataset and Pilot Exploration for
Advancing Precision Medicine in Drug-Resistant Epilepsy", CC-BY-4.0). The record describes itself as "the public
dataset, running code and results for our paper". No article was found at conversion time (2026-10-08), and the record
does not name the hospital.

## Participants
`participants.tsv` reproduces the release table `information list/clinical information.xlsx`: sex, age at surgery, age
at onset, MRI code (P/N), number of seizures, electrodes and contacts, EZ, therapy and Engel outcome (all patients
Engel I). It also includes the channel numbers of `information list/channel level EZ annotations.xlsx` (EZ channels and
deleted, or bad, channels) verbatim. The release does not say whether these numbers index the channel order of the
`.mat` files or the original montage. Some deleted-channel numbers exceed the number of channels in a file, so they are
not mapped onto `channels.tsv`.

**Note on P014 (added 2026-10-09).** In the release file `information list/channel level EZ annotations.xlsx`, the row of P014 (EZ "Right occipital pole, medial posterior cingulate gyrus, and mid-posterior hippocampus") has exactly the same EZ channel list (`11 23 24 18 19 21 35 ... 112-118`) and deleted-channel list (`5 6 20 38 121 122`) as P007 (EZ "Left inferior frontal gyrus, posterior middle frontal gyrus, and part of the orbitofrontal cortex"). Nine of these numbers (112-118, 121, 122) are larger than the channel count of every P014 file (85 or 107 channels; the clinical table gives 86 contacts). The P014 row is therefore probably a copy of the P007 row in the release. `participants.tsv` reproduces the release unchanged (checked against the deposit on 2026-10-09); do not use the P014 `ez_channel_ids` and `deleted_channel_ids` without confirmation from the authors.

## Recordings
- `task-ictal`: release folder `ictal state` (seizure segments, typically 40-60 s). `task-interictal`: folder
  `interictal state` (longer segments). `run-<k>` follows the natural order of the release file names (`sz1`, `sz2`, ...,
  `sz4-1`). `sub-<P>/sub-<P>_scans.tsv` gives the source file of every run. The release does not document where an
  ictal segment starts relative to seizure onset, so there are no events.
- 2000 Hz. Channel names are kept verbatim from the export (`POL A'1`, `EEG C3-Ref`, `POL ECG`, ...). Types are
  inferred from the names (SEEG, EEG for the scalp channels, ECG, MISC; see `task-*_channels.json`). Units: volts
  for SEEG/EEG/ECG (MISC left `n/a`). The release's own code (`code/dre-lzsh-release/1f code`) reads the Nihon Kohden
  EDFs with MNE (`raw.get_data()`, volts), and its per-channel PSD tables (`derivatives/dre-lzsh-results/1f -results`)
  agree with the stored values in scale. Per-participant median band-power ratio (stored / table): 0.80-2.03 for the
  interictal runs (all six bands within 0.5-2 for 28 of 29 participants) and 0.0008-4.5 for the ictal runs (22 of 29;
  not P004, P007, P013, P014, P018, P020, P025). Values in µV would give ratios of about 1e12.
- The release stores three MATLAB layouts: `eeg_data` with an MNE-style `info` struct, `data` with `ch_names`, and `data`
  with `channel_names` and a channel count. All three are read as stored. Each segment became one BrainVision run (IEEE
  float32: the stored float64 values rounded to float32), and the round-trip check compares every run with its source.
  No filtering, resampling, re-referencing or channel removal was applied.
- There are no electrode coordinates in the release. `electrodes.tsv` lists the SEEG contact names with `n/a`
  coordinates.

## Other release content
- `derivatives/dre-lzsh-results/`: the authors' result tables (`Results/`: HFO rates and 1/f power-spectrum fits per
  segment), copied verbatim.
- `code/dre-lzsh-release/`: the authors' code (`HFODetector.m` and related scripts, a notebook), copied verbatim.
- `sourcedata/zenodo-17272689/DRE-LZSH/`: the original `.mat` files and the two information-list spreadsheets. The only
  change is that the MATLAB header text "Created on" (file export date, April and June 2025) has its weekday and day
  masked. The provenance JSON gives the SHA-256 of each file before and after masking.

## License

CC-BY-4.0

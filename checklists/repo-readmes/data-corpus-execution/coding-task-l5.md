# L5 Coding Execution Tasks

[L5 Completed - 11.07.2026]

This is the execution log for coding study design across all eligible records in `data/screened-partitions/eligible/`. Use it to track command order, status, batch/run names, and notes while the `L5` coding work progresses.

The eligible records are produced by the `L0` screening post-processing workflow and are split into 61 partitions of up to 10,000 records each.

## Conventions

- Task: `study`
- Reasoning: `low`
- Input partition pattern: `data/screened-partitions/eligible/<number>`
- Run name pattern: `coding_l5_partition_<number>_f1`
- Partition range: `1`–`61`
- Maximum records per partition: `10,000`
- Status values:
  - `Planned`: command is prepared but not started
  - `Submitted`: batch request has been created/submitted
  - `Downloaded`: batch output has been retrieved
  - `Completed`: output has been processed and checked
  - `Blocked`: run needs attention before continuing

## Coding Commands

- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l5_partition_1_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/2 coding_l5_partition_2_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/3 coding_l5_partition_3_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/4 coding_l5_partition_4_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/5 coding_l5_partition_5_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/6 coding_l5_partition_6_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/7 coding_l5_partition_7_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/8 coding_l5_partition_8_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/9 coding_l5_partition_9_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/10 coding_l5_partition_10_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/11 coding_l5_partition_11_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/12 coding_l5_partition_12_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/13 coding_l5_partition_13_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/14 coding_l5_partition_14_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/15 coding_l5_partition_15_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/16 coding_l5_partition_16_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/17 coding_l5_partition_17_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/18 coding_l5_partition_18_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/19 coding_l5_partition_19_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/20 coding_l5_partition_20_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/21 coding_l5_partition_21_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/22 coding_l5_partition_22_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/23 coding_l5_partition_23_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/24 coding_l5_partition_24_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/25 coding_l5_partition_25_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/26 coding_l5_partition_26_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/27 coding_l5_partition_27_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/28 coding_l5_partition_28_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/29 coding_l5_partition_29_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/30 coding_l5_partition_30_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/31 coding_l5_partition_31_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/32 coding_l5_partition_32_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/33 coding_l5_partition_33_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/34 coding_l5_partition_34_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/35 coding_l5_partition_35_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/36 coding_l5_partition_36_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/37 coding_l5_partition_37_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/38 coding_l5_partition_38_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/39 coding_l5_partition_39_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/40 coding_l5_partition_40_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/41 coding_l5_partition_41_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/42 coding_l5_partition_42_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/43 coding_l5_partition_43_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/44 coding_l5_partition_44_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/45 coding_l5_partition_45_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/46 coding_l5_partition_46_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/47 coding_l5_partition_47_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/48 coding_l5_partition_48_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/49 coding_l5_partition_49_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/50 coding_l5_partition_50_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/51 coding_l5_partition_51_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/52 coding_l5_partition_52_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/53 coding_l5_partition_53_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/54 coding_l5_partition_54_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/55 coding_l5_partition_55_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/56 coding_l5_partition_56_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/57 coding_l5_partition_57_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/58 coding_l5_partition_58_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/59 coding_l5_partition_59_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/60 coding_l5_partition_60_f1 --task study --reasoning low`
- `Completed + Downloaded` - `python labelling/orchestrator.py data/screened-partitions/eligible/61 coding_l5_partition_61_f1 --task study --reasoning low`

## Post Processing

`labelling/process_coding.py` infers the task's label column(s) from the batch outputs and writes one file per input partition, keeping the input partitioning as-is (Nth run in `run_names.json[<task>]` -> partition folder `N`).

```bash
# Reads run names from checklists/mappings/run_names.json under key "study"
python labelling/process_coding.py --task study

# Preview which runs are missing datasets / batch outputs, then exit
python labelling/process_coding.py --task study --print-missing

# Process only the runs that are present
python labelling/process_coding.py --task study --skip-missing
```

Output (default folder `data/coding-<task>/`):

- `data/coding-study/<n>/study_<n>_<max_year>-<min_year>.xlsx` — per partition
- `data/coding-study/all/study_all.csv` — combined table
- `data/coding-study/metadata.json` — per-run coverage and label distributions

Add this task's run names to `checklists/mappings/run_names.json` under a key
matching the `--task` value (`study`).

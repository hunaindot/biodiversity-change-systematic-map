# L2 Coding Execution Tasks

This is the execution log for coding threats across all eligible records in `data/screened-partitions/eligible/`. Use it to track command order, status, batch/run names, and notes while the `L2` coding work progresses.

The eligible records are produced by the `L0` screening post-processing workflow and are split into 61 partitions of up to 10,000 records each.

## Conventions

- Task group: `threats`
- Task steps: `threats_l0`, `threats_l1`, `threats_l2`
- Reasoning: `medium`
- Input partition pattern: `data/screened-partitions/eligible/<number>`
- Run name pattern: `coding_l2_partition_<number>_f1`
- Partition range: `1`–`61`
- Maximum records per partition: `10,000`
- Commands per partition: `3`
- Run-name rule: reuse the same run name for `threats_l0`, `threats_l1`, and `threats_l2` within a partition so downstream levels can find earlier outputs
- Status values:
  - `Planned`: command is prepared but not started
  - `Submitted`: batch request has been created/submitted
  - `Downloaded`: batch output has been retrieved
  - `Completed`: output has been processed and checked
  - `Blocked`: run needs attention before continuing

## Coding Commands

### Partition 1

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l2_partition_1_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l2_partition_1_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/1 coding_l2_partition_1_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 2

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/2 coding_l2_partition_2_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/2 coding_l2_partition_2_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/2 coding_l2_partition_2_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 3

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/3 coding_l2_partition_3_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/3 coding_l2_partition_3_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/3 coding_l2_partition_3_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 4

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/4 coding_l2_partition_4_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/4 coding_l2_partition_4_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/4 coding_l2_partition_4_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 5

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/5 coding_l2_partition_5_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/5 coding_l2_partition_5_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/5 coding_l2_partition_5_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 6

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/6 coding_l2_partition_6_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/6 coding_l2_partition_6_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/6 coding_l2_partition_6_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 7

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/7 coding_l2_partition_7_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/7 coding_l2_partition_7_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/7 coding_l2_partition_7_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 8

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/8 coding_l2_partition_8_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/8 coding_l2_partition_8_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/8 coding_l2_partition_8_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 9

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/9 coding_l2_partition_9_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/9 coding_l2_partition_9_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/9 coding_l2_partition_9_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 10

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/10 coding_l2_partition_10_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/10 coding_l2_partition_10_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/10 coding_l2_partition_10_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 11

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/11 coding_l2_partition_11_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/11 coding_l2_partition_11_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/11 coding_l2_partition_11_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 12

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/12 coding_l2_partition_12_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/12 coding_l2_partition_12_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/12 coding_l2_partition_12_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 13

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/13 coding_l2_partition_13_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/13 coding_l2_partition_13_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/13 coding_l2_partition_13_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 14

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/14 coding_l2_partition_14_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/14 coding_l2_partition_14_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/14 coding_l2_partition_14_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 15

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/15 coding_l2_partition_15_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/15 coding_l2_partition_15_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/15 coding_l2_partition_15_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 16

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/16 coding_l2_partition_16_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/16 coding_l2_partition_16_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/16 coding_l2_partition_16_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 17

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/17 coding_l2_partition_17_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/17 coding_l2_partition_17_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/17 coding_l2_partition_17_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 18

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/18 coding_l2_partition_18_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/18 coding_l2_partition_18_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/18 coding_l2_partition_18_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 19

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/19 coding_l2_partition_19_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/19 coding_l2_partition_19_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/19 coding_l2_partition_19_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 20

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/20 coding_l2_partition_20_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/20 coding_l2_partition_20_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/20 coding_l2_partition_20_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 21

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/21 coding_l2_partition_21_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/21 coding_l2_partition_21_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/21 coding_l2_partition_21_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 22

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/22 coding_l2_partition_22_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/22 coding_l2_partition_22_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/22 coding_l2_partition_22_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 23

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/23 coding_l2_partition_23_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/23 coding_l2_partition_23_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/23 coding_l2_partition_23_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 24

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/24 coding_l2_partition_24_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/24 coding_l2_partition_24_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/24 coding_l2_partition_24_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 25

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/25 coding_l2_partition_25_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/25 coding_l2_partition_25_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/25 coding_l2_partition_25_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 26

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/26 coding_l2_partition_26_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/26 coding_l2_partition_26_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/26 coding_l2_partition_26_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 27

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/27 coding_l2_partition_27_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/27 coding_l2_partition_27_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/27 coding_l2_partition_27_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 28

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/28 coding_l2_partition_28_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/28 coding_l2_partition_28_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/28 coding_l2_partition_28_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 29

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/29 coding_l2_partition_29_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/29 coding_l2_partition_29_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/29 coding_l2_partition_29_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 30

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/30 coding_l2_partition_30_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/30 coding_l2_partition_30_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/30 coding_l2_partition_30_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 31

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/31 coding_l2_partition_31_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/31 coding_l2_partition_31_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/31 coding_l2_partition_31_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 32

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/32 coding_l2_partition_32_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/32 coding_l2_partition_32_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/32 coding_l2_partition_32_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 33

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/33 coding_l2_partition_33_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/33 coding_l2_partition_33_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/33 coding_l2_partition_33_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 34

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/34 coding_l2_partition_34_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/34 coding_l2_partition_34_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/34 coding_l2_partition_34_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 35

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/35 coding_l2_partition_35_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/35 coding_l2_partition_35_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/35 coding_l2_partition_35_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 36

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/36 coding_l2_partition_36_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/36 coding_l2_partition_36_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/36 coding_l2_partition_36_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 37

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/37 coding_l2_partition_37_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/37 coding_l2_partition_37_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/37 coding_l2_partition_37_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 38

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/38 coding_l2_partition_38_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/38 coding_l2_partition_38_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/38 coding_l2_partition_38_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 39

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/39 coding_l2_partition_39_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/39 coding_l2_partition_39_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/39 coding_l2_partition_39_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 40

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/40 coding_l2_partition_40_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/40 coding_l2_partition_40_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/40 coding_l2_partition_40_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 41

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/41 coding_l2_partition_41_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/41 coding_l2_partition_41_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/41 coding_l2_partition_41_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 42

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/42 coding_l2_partition_42_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/42 coding_l2_partition_42_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/42 coding_l2_partition_42_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 43

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/43 coding_l2_partition_43_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/43 coding_l2_partition_43_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/43 coding_l2_partition_43_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 44

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/44 coding_l2_partition_44_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/44 coding_l2_partition_44_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/44 coding_l2_partition_44_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 45

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/45 coding_l2_partition_45_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/45 coding_l2_partition_45_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/45 coding_l2_partition_45_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 46

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/46 coding_l2_partition_46_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/46 coding_l2_partition_46_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/46 coding_l2_partition_46_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 47

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/47 coding_l2_partition_47_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/47 coding_l2_partition_47_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/47 coding_l2_partition_47_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 48

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/48 coding_l2_partition_48_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/48 coding_l2_partition_48_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/48 coding_l2_partition_48_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 49

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/49 coding_l2_partition_49_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/49 coding_l2_partition_49_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/49 coding_l2_partition_49_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 50

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/50 coding_l2_partition_50_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/50 coding_l2_partition_50_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/50 coding_l2_partition_50_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 51

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/51 coding_l2_partition_51_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/51 coding_l2_partition_51_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/51 coding_l2_partition_51_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 52

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/52 coding_l2_partition_52_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/52 coding_l2_partition_52_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/52 coding_l2_partition_52_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 53

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/53 coding_l2_partition_53_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/53 coding_l2_partition_53_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/53 coding_l2_partition_53_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 54

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/54 coding_l2_partition_54_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/54 coding_l2_partition_54_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/54 coding_l2_partition_54_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 55

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/55 coding_l2_partition_55_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/55 coding_l2_partition_55_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/55 coding_l2_partition_55_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 56

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/56 coding_l2_partition_56_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/56 coding_l2_partition_56_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/56 coding_l2_partition_56_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 57

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/57 coding_l2_partition_57_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/57 coding_l2_partition_57_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/57 coding_l2_partition_57_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 58

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/58 coding_l2_partition_58_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/58 coding_l2_partition_58_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/58 coding_l2_partition_58_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 59

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/59 coding_l2_partition_59_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/59 coding_l2_partition_59_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/59 coding_l2_partition_59_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 60

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/60 coding_l2_partition_60_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/60 coding_l2_partition_60_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/60 coding_l2_partition_60_f1 --task threats_l2 --reasoning medium --batch-size 5000`

### Partition 61

- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/61 coding_l2_partition_61_f1 --task threats_l0 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/61 coding_l2_partition_61_f1 --task threats_l1 --reasoning medium --batch-size 5000`
- `Planned` - `python labelling/orchestrator.py data/screened-partitions/eligible/61 coding_l2_partition_61_f1 --task threats_l2 --reasoning medium --batch-size 5000`

## Post Processing

`labelling/process_coding.py` infers the task label columns from the batch outputs and writes one file per input partition, keeping the input partitioning as-is (Nth run in `run_names.json[<task>]` -> partition folder `N`). For threats, the composite task folds `threats_l0`, `threats_l1`, and `threats_l2` outputs into one file.

```bash
# Reads run names from checklists/mappings/run_names.json under key "threats"
python labelling/process_coding.py --task threats

# Preview which runs are missing datasets / batch outputs, then exit
python labelling/process_coding.py --task threats --print-missing

# Process only the runs that are present
python labelling/process_coding.py --task threats --skip-missing
```

Output (default folder `data/coding-<task>/`):

- `data/coding-threats/<n>/threats_<n>_<max_year>-<min_year>.xlsx` — per partition
- `data/coding-threats/all/threats_all.csv` — combined table
- `data/coding-threats/metadata.json` — per-run coverage and label distributions

Add this task group's run names to `checklists/mappings/run_names.json` under the composite key matching the post-processing `--task` value (`threats`).


Run name convention as used in labelling package:
<train|dev|test>-<l0-6>-<dd.mm.yyyy>-<1..9>


Sample runs to submit all tasks for labelling as per labelling.py:

```
python labelling/orchestrator.py  data/labels/l0/train train-l0-110226-1 --task screening
python labelling/orchestrator.py  data/labels/l1/train train-l1-110226-1 --task driver
python labelling/orchestrator.py  data/labels/l2/train train-l2-110226-1 --task threats
python labelling/orchestrator.py  data/labels/l3/train train-l3-110226-1 --task geography
python labelling/orchestrator.py  data/labels/l4/train train-l4-110226-1 --task ecosystems
python labelling/orchestrator.py  data/labels/l5/train train-l5-110226-1 --task study
python labelling/orchestrator.py  data/labels/l6/train train-l6-110226-1 --task taxa
```

---

Dataset_labels: For creating train, test, dev splits
run for specific labels and create data in data/labels

`python3 -m datasets_labels --labels l0,l1`

yt

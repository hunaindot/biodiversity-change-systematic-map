# Review of protocol consistency checks

- Primary metrics:
  - Per label and aggregated: Precision, Recall, F1, Cohen's Keppa
  - Aggregated summaries: [macro, micro, weighted]

  - Tp/ Fp/ Fn/ Tn defintions
    tp = |truth ∩ pred|
    fp = |pred - truth|
    fn = |truth - pred|
    tn = |label_universe - (truth ∪ pred)|
  - Keppa-per-label and interpretations:
    Raw agreement to be very high: tp+tn/N where TN is quite large
    A lot of that agreement comes from the label being absent in many rows
    kappa corrects for that chance/background agreement using Pe:
    P(True positives)_ P(Predicted positives) + P(True negatives)_ P(Predicted negatives)
    Pe exepected to be lower

    Final Keppa being Po - Pe / (1-Pe)

- Consistency Checks
  CC1: What are human labelled baseline metrics when comparing abstract based labelling v. expert labels? (No LLM execution required here)
  [Data: data/consistency-check-datasets/data-coding/annotated_coding_dataset.xlsx]

  CC2: Compare LLM Labels v. Reference Expert Labels in forms of Train, Dev, Test sets

# General Notes

- Status
  [Completed]: Implies that run is run is executed, data is download, and evals are added

# CC2 Executions (For each Label)

## L1 - Driver

### Dev set execution in order

python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_low_f1 --task driver
python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_medium_f1 --task driver
python labelling/orchestrator.py data/labels/l1/dev l1_dev_010726_high_f1 --task driver

### What performs well in dev (based on F1 xx)

### Train set execution - Reasoning = x

### Test set execution

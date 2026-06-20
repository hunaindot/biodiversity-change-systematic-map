# Review of protocol consistency checks

- Primary metric = Recall
  TP/ TP + FP where TP is the "Eligible" label.
- CC1 = Compare LLM Labels v. Reference Expert Labels in forms of Train, Dev, Test sets
- CC2 = Compare LLM Labels v. Mnaual Labels assigned based on abstract reading

- Cmd to run eval: python -m evals_local l0_train_140626_low_f1 --tasks screening

## [Train, Dev, Test] Commands to reproduce

### Dev sets executed for different reasoning [low, medium, high] (In order)

python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_low_f1 --task screen
python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_medium_f1 --task screen
python labelling/orchestrator.py data/labels/l0/dev l0_dev_010726_high_f1 --task screen

### Train set executed for reasoning with highest recall

python labelling/orchestrator.py data/labels/l0/train l0_train_010726_medium_f1 --task screen

### Test set executed for reasoning with highest recall

python labelling/orchestrator.py data/labels/l0/test l0_test_010726_medium_f1 --task screen

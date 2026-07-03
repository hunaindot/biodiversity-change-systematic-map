# Token Cost Planned

This note summarizes estimated GPT-5 nano Batch API token costs using the current `010726` test-set batch outputs.

## Assumed Pricing

Prices are assumed from the GPT-5 nano Batch API pricing shown by the user:

| Token type | Price per 1M tokens |
|---|---:|
| Uncached input | $0.025 |
| Cached input | $0.003 |
| Output | $0.20 |

## Token Fields

| Field | Meaning |
|---|---|
| Cached input avg | Average input tokens per record that were served from prompt cache. |
| Uncached input avg | Average input tokens per record billed at the normal input rate. Computed as `input_tokens - cached_tokens`. |
| Output avg | Average output tokens per record. This includes reasoning tokens. |
| Cost / 1M records | Estimated cost to process 1,000,000 records of that output type, using the average token counts from the test set. |

Formula:

```text
cost_per_1M_records =
  cached_input_avg * 0.003
  + uncached_input_avg * 0.025
  + output_avg * 0.20
```

Because the token averages are already per record and prices are per 1M tokens, multiplying by 1,000,000 records and dividing by 1,000,000 tokens cancels out.

## Estimated Cost By Test Output

| Test output | Records | Cached input avg | Uncached input avg | Output avg | Cost / 1M records |
|---|---:|---:|---:|---:|---:|
| L0 test medium / screening | 482 | 2909.48 | 491.70 | 1968.43 | $414.71 |
| L1 test low / driver | 837 | 1424.06 | 542.33 | 245.57 | $66.94 |
| L2 test medium / threats_l0 | 124 | 5949.94 | 482.29 | 977.13 | $225.33 |
| L2 test medium / threats_l1 | 110 | 770.33 | 1613.67 | 3231.07 | $688.87 |
| L3 test low / geography | 469 | 2271.80 | 408.33 | 460.04 | $109.03 |
| L4 test high / ecosystems_realm | 839 | 0.00 | 1167.20 | 988.25 | $226.83 |
| L5 test low / study | 950 | 1994.37 | 491.93 | 861.10 | $190.50 |
| L6 test high / taxa | 146 | 250.74 | 1813.71 | 3601.86 | $766.47 |

## Planned Full-Pipeline Token Volume

This estimate assumes 2.4 million `L0` screening records and 0.25 million records for each downstream output. `L2` has two outputs, `threats_l0` and `threats_l1`, so both are counted separately.

| Pipeline output | Planned records | Input tokens | Cached input | Uncached input | Output tokens | Reasoning tokens | Visible output | Total tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L0 screening | 2.40M | 8,162.81M | 6,982.75M | 1,180.08M | 4,724.23M | 4,449.70M | 274.54M | 12,887.04M |
| L1 driver | 0.25M | 491.60M | 356.01M | 135.58M | 61.39M | 48.42M | 12.97M | 552.99M |
| L2 threats_l0 | 0.25M | 1,608.06M | 1,487.48M | 120.57M | 244.28M | 229.68M | 14.61M | 1,852.34M |
| L2 threats_l1 | 0.25M | 596.00M | 192.58M | 403.42M | 807.77M | 793.10M | 14.67M | 1,403.77M |
| L3 geography | 0.25M | 670.03M | 567.95M | 102.08M | 115.01M | 92.21M | 22.80M | 785.04M |
| L4 ecosystems_realm | 0.25M | 291.80M | 0.00M | 291.80M | 247.06M | 232.97M | 14.09M | 538.86M |
| L5 study | 0.25M | 621.58M | 498.59M | 122.98M | 215.28M | 167.29M | 47.98M | 836.85M |
| L6 taxa | 0.25M | 516.11M | 62.69M | 453.43M | 900.47M | 880.00M | 20.46M | 1,416.58M |
| Total | 4.15M | 12,957.98M | 10,148.06M | 2,809.95M | 7,315.49M | 6,893.37M | 422.12M | 20,273.47M |

In short, the planned full pipeline burns about **20.27 billion total tokens**, made up of about **12.96 billion input tokens** and **7.32 billion output tokens**.

## Source Outputs

The averages above were calculated from these Batch API test outputs:

| Test output | Source file |
|---|---|
| L0 test medium / screening | `data/artifacts/batch_outputs/l0_test_010726_medium_f1/screening-batch_6a36a8b3c86881909a037a3ac49f8e2b-output.jsonl` |
| L1 test low / driver | `data/artifacts/batch_outputs/l1_test_010726_low_f1/driver-batch_6a37abdbdfe88190a928aa1a9b7d422b-output.jsonl` |
| L2 test medium / threats_l0 | `data/artifacts/batch_outputs/l2_test_010726_medium_f1/threats_l0-batch_6a37b26a8c7c81909b41b297e04f135b-output.jsonl` |
| L2 test medium / threats_l1 | `data/artifacts/batch_outputs/l2_test_010726_medium_f1/threats_l1-batch_6a37b91010cc8190b9d0041942e88f37-output.jsonl` |
| L3 test low / geography | `data/artifacts/batch_outputs/l3_test_010726_low_f1/geography-batch_6a37c05211708190b6887d7715fa98a0-output.jsonl` |
| L4 test high / ecosystems_realm | `data/artifacts/batch_outputs/l4_test_010726_high_f1/ecosystems_realm-batch_6a37ebae30e88190af2742411e326949-output.jsonl` |
| L5 test low / study | `data/artifacts/batch_outputs/l5_test_010726_low_f1/study-batch_6a37cef1c68881908dc8bf2f501e1574-output.jsonl` |
| L6 test high / taxa | `data/artifacts/batch_outputs/l6_test_010726_high_f1/taxa-batch_6a37e1fdc4b481909a0b47f840db5f76-output.jsonl` |

datasets_labels: python3 -m datasets_labels --labels l0,l1
= run for subset l0, l1


0) Reference Data Creators
--------------------------

1. reference_screening_data_creator.py
   Builds the L0 screening labels CSV from the reference Excel file.

   Source: data/consistency-check-datasets/screening/reference_screening_dataset.xlsx
   Output: data/labels/l0/L0) Screening.csv  (2418 rows)

   Run from anywhere:
       python3 datasets_labels/reference_screening_data_creator.py

   Key variables:
       ROOT    — project root, derived from __file__
       SOURCE  — path to the input Excel file
       SHEETS  — list of sheet names (note: "Jaureguiberry" sheet is truncated to 31 chars by Excel)
       LABEL_COL / TARGET_COLS — eligbility + base metadata columns
   Note: Jaureguiberry sheet spells the col "eligibility" (correct); the script
         silently renames it to "eligbility" to match all other sheets.

2. reference_coding_data_creator.py
   Builds L1–L6 label CSVs from the reference coding Excel file.

   Source: data/consistency-check-datasets/data-coding/reference_coding_dataset.xlsx
   Outputs:
       data/labels/l1/L1) driver set.csv
       data/labels/l2/L2) threats set.csv
       data/labels/l3/L3) geography set.csv
       data/labels/l4/L4) ecosystem set.csv
       data/labels/l5/L5) study set.csv
       data/labels/l6/L6) taxa set.csv

   Run from anywhere:
       python3 datasets_labels/reference_coding_data_creator.py

   Key variables:
       ROOT    — project root, derived from __file__
       SOURCE  — path to the input Excel file
       SHEETS  — list of 8 source sheet names
       LABELS  — list of dicts, each with "name", "cols", "out"

4. sample_screening_manual_labels.py
   Draws a stratified random sample of 100 records from the L0 train set
   for manual labelling review. Uses the same stratification logic as the
   train/dev/test splitter (proportional across source strata).

   Source:  data/labels/l0/train/
   Output:  data/consistency-check-datasets/screening/to-manual-label/
       l0_manual_sample.csv
       sample_meta.json  — seed, counts, and strata breakdown

   Run from anywhere:
       python3 datasets_labels/sample_screening_manual_labels.py

   Key variables:
       ROOT      — project root, derived from __file__
       N_SAMPLE  — number of records to sample (default: 100)
       TRAIN_PATH — path to L0 train CSV
   Seed: reads DATASETS_LABELS_SEED from .env, falls back to 42.

3. sample_coding_manual_labels.py
   Draws a stratified random sample of 100 records from each L1–L6 train set
   for manual labelling review. Uses the same stratification logic as the
   train/dev/test splitter (proportional across strata, multi-label as one group).

   Sources: data/labels/l{1..6}/train/
   Outputs: data/consistency-check-datasets/data-coding/to-manual-label/
       l1_manual_sample.csv
       l2_manual_sample.csv
       l3_manual_sample.csv
       l4_manual_sample.csv
       l5_manual_sample.csv
       l6_manual_sample.csv
       sample_meta.json  — seed, counts, and strata breakdown per label

   Run from anywhere:
       python3 datasets_labels/sample_coding_manual_labels.py

   Key variables:
       ROOT      — project root, derived from __file__
       N_SAMPLE  — number of records to sample per label (default: 100)
       TRAIN_PATHS — per-label paths to train CSVs
   Seed: reads DATASETS_LABELS_SEED from .env, falls back to 42.



--------------------------------------------------------------------------------------------------------


1) Overview of Labels L0-L6
--------------------------

My labels dataset structure at path data/labels:

- /l0 = My labels for screening
    Final label is "eligbility" column like ["ELIGIBLE"] or ["NOT_ELIGIBLE"]
    unique primary key is "UT (Unique WOS ID)"

- /l1 = My labels for direct drivers of biodiversity loss
    Final labels is "driver" column like ["Climate Change", "Direct Exploitation and Resource extraction"].
    It's list text like list of different labels of direct drivers of biodiversity loss.
    It's a multi label chosing from 5 unique labels from direct drivers of biodiversity loss
    unique primary key is "UT (Unique WOS ID)"

- /l2 = My labels for two hierarchical levels of threats faced by biodiversity
    Final labels are "threats_l0" and "threats_l1"
    It's list text like list of different labels of threats
    It's a multi label classficaiton
    Null implies that there is no truth to the label. In evaluation, It should be skipped
    unique primary key is "UT (Unique WOS ID)"

- /l3 = My labels for geographical hierarchy.
    Final labels are "region", "sub-region", "country"
    Null implies there is no truth to the label example. In evaluation, it should be skipped
    It's a multi label classficaiton. So one record can have multiple labels.  For example region = ["Africa", "Asia-Pacific"]
    unique primary key is "UT (Unique WOS ID)"

- /l4 = My labels for ecosystems
    Final labels are "realm" and  "biome"
     Null implies there is no truth to the label example. In evaluation, it should be skipped
    It's a multi label classficaiton. So one record can have multiple labels.  For example realm = ["Freshwater", "Terrestrial"]
    unique primary key is "UT (Unique WOS ID)"

- /l5 = My labels for study
    Final labels is "study_design"
     Null implies there is no truth to the label example. In evaluation, it should be skipped
    It's a multi label classficaiton. So one record can have multiple labels.  For example study_design =["Observational", "Modelling"]
    unique primary key is "UT (Unique WOS ID)"

- /l5 = My labels for taxa
    Final labels is "kingdom",	"phylum",	"class",	"order",	"specie"
     Null implies there is no truth to the label example. In evaluation, it should be skipped
    It's a multi label classficaiton. So one record can have multiple labels.
    unique primary key is "UT (Unique WOS ID)"


2) Stratification for Train/Test/Dev split

- For all L0-L6, dedup based on on the unique key in each "UT (Unique WOS ID)". Keep first in case of duplicatates. Save duplicate cases in the respective folder of L0 under a new "in-process" folder

- L0) Screening:
    - Stratify based on col "eligbility"
    - The labels of eligibibility are ["ELIGIBLE"] or ["NOT_ELIGIBLE"]
    - They are imbalanced.
    - Take stratification into account when creating splits

- L1) Driver:
    - Stratify based on "driver" col
    - the col can be single or multi label.
    In single label it can be either of 5 direct drivers:
    ["Climate Change"]
    ["Invasive alien species"]
    ["Pollution"]
    ["Land/sea use change"]
    ["Direct Exploitation and Resource extraction"]

    In multi label it can contain or more combination
    - For single label stratify based in proportion of each in single label
    - Stratify records where there are multiple label as one stratification

- L2) threats:
    - Stratify based on "threats_l0" column. This is highest level hierarchy
    - Just like "driver" in L1 it has cases of single label and multi-label
    - Follow same stratificaiton approach where single labels are stratified in proportion and multi-labels are stratified as one group
    - have all labels of threats in final sets

- L3) geography
    - Stratify based on "region" column. this is highest level hierarcgy
    - Just like "driver" in L1 it has cases of single label and multi-label
    - Follow same stratificaiton approach where single labels are stratified in proportion and multi-labels are stratified as one group
    - all labels of geogrpahy in the final sets


- L4) ecosystems
    - Stratify based on "realm" column. this is highest level hierarcgy
    - Just like "driver" in L1 it has cases of single label and multi-label
    - Follow same stratificaiton approach where single labels are stratified in proportion and multi-labels are stratified as one group
    - Have all levels of geography in final sets

- L5) study
    - Stratify based on "study_design" column. this is highest level hierarcgy
    - Just like "driver" in L1 it has cases of single label and multi-label
    - Follow same stratificaiton approach where single labels are stratified in proportion and multi-labels are stratified as one group
    - Have all levels of study_design in final sets

- L6) taxa
    - startify based on "kingdom"
    - Some rows have now kingdom startify them sep
    - cols= [kingdom	phylum	class	order	specie] when all are null, these rows are not to be in final  sets

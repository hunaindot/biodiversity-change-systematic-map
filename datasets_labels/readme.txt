datasets_labels: python3 -m datasets_labels --labels l0,l1
= run for subset l0, l1


1) Overview of Labels L0-L6

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
    - all abels of geogrpahy in teh final sets


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





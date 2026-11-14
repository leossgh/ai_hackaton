**OSLO ANTIBODIES × AI HACKATHON** 

# **AI × Antibodies** 

Hackathon task description 

6 November 2026 · <u>oslo-ai-antibodies-hackathon.vercel.app</u> 

## **The task** 

For the hackathon, participants have an ambitious task: improve an existing antibody, using the capabilities of Apheris Foundry, Nebius and JapanFold, coupled with multi-modal data from the hackathon organisers. This simulates a real-life scenario of reviving a real-life project from a set of data of different modalities. 

Namely, we want participants to develop a robust antibody pipeline, and show how it performs on a well-known antibody, trastuzumab. Given some amount of multi-modal data, participants can decide to either design a completely new antibody while preserving the original epitope, or make point mutations to an existing antibody while improving its affinity and thermostability. The designs for both modes, which we call **optimisation** and **de novo design** , will be judged by three conditions: 

1. Design should have comparable or better binding to its target, HER2, as measured by SPR. 

2. Design should preserve the binding epitope, as judged by competitive binding assay. 

3. Design should improve an antibody’s thermostability, as a proxy of real-life developability. 

Designs improving only one or two of these properties will be ranked strictly lower than those improving all 3. See judging criteria for details. 

Oslo Antibodies × AI hackathon 

1 



<!-- Start of picture text -->
How a design is tiered<br>Each triangle has one axis per judged property. A tier counts how many improve on trastuzumab.<br>Trastuzumab baseline Design<br>S-tier A-tier B-tier Unsuccessful<br>3 of 3 2 of 3 1 of 3 0 of 3<br>Affinity Affinity Affinity Affinity<br>Before<br>Epitope Thermostability Epitope Thermostability Epitope Thermostability Epitope Thermostability<br>preservation preservation preservation preservation<br>Affinity Affinity Affinity Affinity<br>After<br>Epitope Thermostability Epitope Thermostability Epitope Thermostability Epitope Thermostability<br>preservation preservation preservation preservation<br>A filled vertex marks a property that beat the baseline. Ties and regressions are hollow.<br><!-- End of picture text -->

Figure 1: Tiers are counted per design, against the measured trastuzumab baseline. 

### **Criteria for de novo vs optimisation** 

Briefly, submissions can be of one of three types: VHH, Fab (paired-chain variable fragment) or scFv (the same as Fab, but connected with a linker into one chain). A design is considered **de novo** if it has less than 70% sequence identity to any known antibody in known databases, and those must have at least 2 CDRH3 mutations away from trastuzumab. All other designs are considered **optimisation** designs, and only optimisations with less than 70% CDRH3 identity to trastuzumab and at least 2 mutations from any provided antibody are considered valid. 

Oslo Antibodies × AI hackathon 

2 

###### **How a design is classified and checked** 

Everything below runs inside abguard. The track is decided for you, not chosen by the team. 



<!-- Start of picture text -->
Submitted design<br>Extract antibody sequence<br>immunum strips tags and linkers<br>Shared hard checks — every design<br>• Numbering confidence at least 0.1 (is it an antibody?)<br>• Format is VHH, scFv or Fab<br>• Total length at most 250 amino acids fails<br>• No unpaired cysteines<br>Type-aware identity comparison<br>VHH against known VHHs and heavy chains;<br>scFv and Fab split into paired chains<br>yes Identity to nearest known no<br>antibody under 70%?<br>De novo track Optimisation track<br>Extra check — de novo only fails<br>• At least 2 CDRH3 mutations away from trastuzumab<br>Extra checks — optimisation only fails<br>• CDRH3 identity to trastuzumab under 70%<br>• More than 2 point mutations from any provided antibody<br>Eligible for submission Rejected<br>A design is never moved between tracks. If it misses its track’s criteria it is rejected, not reclassified.<br><!-- End of picture text -->

Figure 2: Classification and hard checks, as implemented in `abguard` . 

Organisers will provide a command-line tool to check design validity. Informally, the tool first extracts the antibody sequence (that is, excludes potential tags and linkers) with the `immunum` library, and then performs a type-aware similarity comparison: a VHH design is compared with known VHHs or heavy chains, while scFvs are split into paired antibodies and compared as paired antibodies. 

## **Supporting data** 

Organisers provide two bodies of data: general VHH–antigen data, and trastuzumab-specific data. 

### **General** 

1. **VHH–antigen true negatives** — unpublished 

   - 454 pairs, 21 of which score AlphaFold3 ipTM at or above 0.7 

   - SPR, no measurable binding 

2. **Non-cognate VHH–antigen interactions** — unpublished 

   - 2 data points 

   - Binary off-target label, no affinity 

3. **Cognate VHH–antigen affinities** — unpublished 

   - 15 data points 

Oslo Antibodies × AI hackathon 

3 

   - SPR, all sub-micromolar 

4. **Cognate and non-cognate VHH–antigen complexes** — published 

   - 1.8M AI-generated structures from 106 cognate and 11,342 non-cognate pairings, predicted by AlphaFold3, Boltz-2 and Chai-1 with 50 samples each 

   - Described in <u>Smorodina et al.</u> · <u>Zenodo</u> · <u>archive.sigma2.no</u> 

These are pairs that were measured and found not to bind, which is what lets you calibrate a structure-prediction confidence filter before trusting it to rank designs. 

### **Trastuzumab** 

1. **CDRH3 variants vs HER2** — published 

   - 524,346 variants, up to 10 mutated positions in CDRH3 

   - FACS, three affinity classes 

   - Published in <u>Chinery et al.</u> · <u>Zenodo</u> 

2. **Optimisation designs** — published 

   - Around 700 designs from the same study, 190 with measurable affinity measured by SPR 

## **Tooling** 

### **Computing environment** 

Each team gets its own virtual machine on Nebius AI Cloud: one NVIDIA H100 GPU, 16 vCPUs, 200 GB RAM and a 500 GB disk, running Ubuntu 24.04 LTS. You connect over SSH. At the start we give each team its machine’s IP address and a private key. 

The machines are shut down at the end of Saturday 14 November. Copy anything you want to keep before then. 

Pre-installed on every machine: 

- **Claude Code** , with credits provided by Anthropic. 

- **Apheris Foundry models** as Docker images, already downloaded. `foundry-toolkit module list` lists them; `Tutorial.html` (Hackathon VM tab) shows how to run each one. 

- **RCSB MCP** , for fast access to known protein structures. 

- **Read-only credentials** for the hackathon data bucket ( `s3://apheris-oslo-hackathon` ). Copy the data you need onto your machine, for example with `aws s3 sync s3://apheris-oslo-hackathon/ <folder> ./data` . We may add more data or scripts there during the event. 

- **`abguard`** , the command-line tool that checks your designs against the hard filters before submission. 

If something doesn’t work on your machine, find the Apheris team on site. 

### **Apheris** 

Apheris Foundry delivers packaged drug-discovery functionality that runs inside the user’s own infrastructure. For the hackathon specifically, multiple models are available. 

#### **Structure prediction** 

**Predict Structure** ( `predict` ) predicts the 3D structure of a complex with a co-folding model. Every model takes the same inputs and gives the same outputs, so you can swap models without changing the rest of your pipeline. It takes a template (a known structure of a related complex, such as trastuzumab bound to HER2) for the models that support one. Each model is its own Docker image on your machine. 

Oslo Antibodies × AI hackathon 

4 

|**Model**|**Weights**|**Template**|
|---|---|---|
|OpenFold3|OpenBind, preview 2|Yes|
|Protenix|v2, v1|Yes|
|Boltz|Boltz-2|Yes|
|Boltz|Boltz-1|No|
|Mol-1|base|Yes|
|ESMFold2|release|No|



#### **Protein design with RFD4-Proteina** 

RFD4-Proteina, from NVIDIA and the Baker Lab, designs a protein’s structure and sequence together. In Foundry it runs as one Docker image per model, in research preview. Each image has these tasks: 

- `design` : generate miniproteins, VHHs, Fv or new CDR loops from an annotated structure. Settings cover the number of designs, the seed, the recycling schedule, sequence randomness, hotspot resampling, partial diffusion (refine an earlier design) and inverse folding (new sequences for a kept backbone). 

- `refold-prepare` : pick your best designs and write the inputs for refolding them with Predict Structure. All the models above are available for refolding. 

- `refold-score` : score those refolds against RFD4-Proteina’s own pass criteria, such as interface PAE, binder pLDDT and RMSD to the design. 

- `finetune` : train the design model further on your own structures, including an antibody task mix. 

Pick the model by choosing its image: 

|**Weight**|**What it is**|**Use it to**|
|---|---|---|
|`release-2026-10-19`|NVIDIA’s general RFD4-<br>Proteina model|Design general proteins and<br>miniproteins|
|`antibody-2026-10-30`|NVIDIA’s antibody model|Design or redesign CDRs on a fixed<br>antibody framework|
|`her2-2026-11-07`|The antibody model, fine-<br>tuned by Apheris on HER2<br>binders from the trastuzumab<br>FACS screen|Redesign trastuzumab’s CDRH3. Set<br>`--sequence-tsr-k`to 2 (balanced) or 1<br>(exploratory) for more varied loops|
|`her2-novel-2026-11-09`|The antibody model, trained<br>by Apheris on pairs of high<br>and low binders from the<br>same screen|Get mostly new CDRH3 loops with<br>the most confident predicted fit to<br>HER2|



On the trastuzumab CDRH3 task, the HER2 weights move designs toward measured binders. The more varied settings give mostly new loops that pass the optimisation challenge’s novelty filter: 

|**Weight and setting**|**Known binders**|**Pass novelty filter**|**Interface error (Å)**|
|---|---|---|---|
|`antibody-2026-10-30`(not fine-tuned)|0%|100%|8.2|
|`her2-2026-11-07`, conservative|21%|0%|9.4|
|`her2-2026-11-07`, balanced|21%|6%|9.1|
|`her2-2026-11-07`, exploratory|0.3%|74%|9.1|



Oslo Antibodies × AI hackathon 

5 

|**Weight and setting**|**Known binders**|**Pass novelty filter**|**Interface error (Å)**|
|---|---|---|---|
|`her2-novel-2026-11-09`|4%|86%|6.8|



These weights only redesign CDRH3. To change other CDRs, use `antibody-2026-10-30` . A known binder fails the novelty filter, so filter designs before ranking them. 

To check designs, run `refold-prepare` on your designs, fold the prepared inputs with any Predict Structure model, then score them with `refold-score` . ESMFold2 works too, but for binders a model that takes a template gives a fairer check, because ESMFold2 folds the target unguided. For the HER2 exercise the pass column stays empty, so rank on `min_ipae` , `iptm` and `binder_plddt` . 

A step-by-step guide with example inputs and a ready-made HER2 script is in the hackathon data bucket under `rfd4-proteina/docs/` . Open `Tutorial.html` . 

### **Nebius Scientific AI platform** 

Nebius Tools is a no-code, agentic platform for protein structure prediction, protein design, and molecular dynamics. It can be used directly in your browser or connected to Claude as a skill. 

You can find all available models and tools in the Apps section of the Workbench, and at <u>sciai.nebius.cloud/models. Setup files will be shared with you in a Slack folder.</u> 

### **JapanFold** 

JapanFold is a drug discovery platform serving open-source bio models at high throughput, with native agent integrations for harnesses like Claude Code and Claude Science. It uniquely complements our toolbox with RoseTTAFold3, OpenDDE and AF2-IG, which can be connected as a skill and called directly from Claude Code. 

### **AMASS** 

AMASS lets participants search scientific papers, clinical trials, patents and drug records with plain-language questions in Claude, and every answer links back to the source. It is useful for checking claims against primary sources and finding leads for antibody design. 

- **Claim your credits.** Each team gets $100 in API credits. One person per team claims them: <u>platform.amass.tech</u> 

- **The AMASS page for the hackathon** , with example use cases and antibody data to start from. 

- **A setup walkthrough** , screen by screen. 

- **How to add AMASS to Claude** , for anyone who does not code. 

- **Short video guides** to the AMASS app. 

Mix and match tools, and divide jobs across platforms. 

Oslo Antibodies × AI hackathon 

6 

## **Design selection criteria** 

Designs should be VHH, scFv or Fab, and must pass our hard filters. After that, teams rank their own designs based on internal criteria of the team. 

### **Hard filters** 

Every submission is checked automatically by a CLI tool, `abguard` , which implements novelty and designability checks for each antibody. A design that fails is not submitted. The constraints known so far: 

- Format: VHH, scFv or Fab. 

- No unpaired cysteines. 

- Somewhat of an antibody: numbering with at least 0.1 confidence with `immunum` . 

- Maximal total length of 250 amino acids (whole length of a single scFv or VHH, or combined for VH and VL). 

- Novelty: under 70% sequence identity to any known antibody for the de novo track, and under 70% CDRH3 sequence identity to trastuzumab plus strictly more than 2 point mutations from any data point provided. 

### **General recommendations** 

For a design to be measured correctly, it needs to be expressed experimentally. While we don’t have any hard filters for that, previous experience of Adaptyv tells us that expression success improved once participants started scoring candidates with Aggrescan 3D, SoluProt, NetSolP, and ProteinMPNN with soluble weights. Please check the whole write-up <u>here.</u> 

## **Ranking and submission** 

### **Pitch day** 

On the hackathon day itself, participants’ pitches will be judged according to the criteria announced at the <u>hackathon website:</u> 

|**Weight**|**Criterion**|
|---|---|
|40%|**Judgment**— clear reasoning behind the molecules you chose.|
|20%|**Execution**— a reproducible pipeline in a GitHub repo.|
|20%|**User fit**— what your design is for, and who needs it.|
|20%|**Path to value**— a credible route to real use, for the molecule or the method.|



Winners of the pitch day will be given extra design submissions, and subsequently a higher chance to win the monetary prize after experimental validation. Namely: 

- Each team gets 4 designs whatever happens. 

- 1st place gets 12 extra designs (16 total). 

- 2nd place gets 8 extra designs (12 total). 

- 3rd place gets 4 extra designs (8 total). 

- Additionally, each of the 6 judges nominates their favourite team with 2 extra designs. 

### **Design submission** 

Prior to pitch evaluation, each team compiles a ranked list of up to 20 designs: 16, assuming they will be winners, plus 4 extra in case of duplication between teams. Teams are free to submit any 

Oslo Antibodies × AI hackathon 

7 

proportion of de novo vs optimisation track designs, as those will be evaluated independently during experimental validation. 

After design submissions are distributed on the pitch day, each team’s top-N submissions will be submitted to Adaptyv for validation. 

#### **Example** 

- 1st place: Team A 

- 2nd place: Team B 

- 3rd place: Team C 

- 4 judges nominate Team D as their favourite 

- 1 judge nominates Team B as their favourite 

- 1 judge nominates Team E as their favourite 

##### **How many designs each team gets tested** 

Worked example. Every team submits a ranked list of up to 20; the top N of that list goes to Adaptyv. 



<!-- Start of picture text -->
Base allocation Pitch placement Judge nomination<br>0 4 8 12 16<br>Team A<br>4 12 16<br>1st place<br>Team B<br>4 8 2 14<br>2nd place, 1 judge<br>Team D<br>4 8 12<br>4 judges<br>Team C<br>4 4 8<br>3rd place<br>Team E<br>4 2 6<br>1 judge<br>All other teams<br>4 4<br>no placement<br><!-- End of picture text -->



<!-- Start of picture text -->
Every team is tested whatever happens. Placement and judge nominations only add to the base four.<br><!-- End of picture text -->

Figure 3: Design distribution for the worked example above. 

## **Experimental evaluation** 

Adaptyv will do cell-free expression of designs and then measure binding while preserving epitope (as measured by competitive binding), and thermostability. 

|**Property**|**How it is measured**|**Who**|
|---|---|---|
|Binding to HER2|SPR|Adaptyv|
|Epitope preservation|Competitive binding against trastuzumab|Adaptyv|
|Thermostability|Direct measurement|Adaptyv|



Finally, we’ll measure these values also for the reference antibody, trastuzumab. That is the baseline every design is compared against. 

### **Post-evaluation ranking** 

Teams will be ranked by number of designs that were able to improve on all three properties (S-tier designs), then on only two properties (A-tier designs), and only 1 property (B-tier). 

Oslo Antibodies × AI hackathon 

8 

- **S-tier** — improves on all three: affinity, epitope preserved, thermostability 

- **A-tier** — improves on two of the three 

- **B-tier** — improves on one of the three 

Teams with most S-tier designs win. If equal, with most A-tier, and so on. Ten designs that each improve one property lose to two designs that improve all three. 

## **Prizes** 

The total prize fund of €3000 will be equally distributed between submissions in two tracks, de novo and optimisation. As a result, participants can either diversify their chances and submit some designs for each track, or bet on one of the tracks only. 

Teams on each track will win €800, €500 and €200 for 1st, 2nd and 3rd place respectively. 

Best Pitch gets an extra $500 prize on the day. 

Based on the pitches, AMASS will also select the team that demonstrates the best use of their platform and award them one month for free. 

Oslo Antibodies × AI hackathon 

9 


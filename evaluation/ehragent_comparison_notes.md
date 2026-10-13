# Positioning the proposed method against EHRAgent

The current result should be described as a **preliminary cross-paper
comparison**. On the current 581-question answerable subset released by the
EHRAgent authors, the proposed method obtains 91.22% execution accuracy and
98.28% completion rate. EHRAgent reports 58.97% success rate and 85.86%
completion rate on 580 MIMIC-III questions.

This is not yet a controlled head-to-head experiment. The proposed method uses
GPT-4o-mini, paraphrased `question` inputs, per-question retrieval of four
nearest training examples, direct SQLite generation, up to three repairs, and
exact execution-result comparison. EHRAgent uses GPT-4-0613, `template`
inputs, four fixed demonstrations plus successful-case long-term memory,
Python tool plans, up to ten interactions, and substring-based answer judging.

For a defensible main-table claim, rerun both systems with:

1. the same 580 question IDs;
2. the same natural-language input field;
3. the same base model and temperature;
4. the same four demonstrations and memory policy;
5. the same maximum interaction budget; and
6. one shared execution-result evaluator.

Until then, avoid claims such as “outperforms EHRAgent by 32.25 points.” A safe
description is: “Under our execution-based evaluation on the current released
581-question subset, the proposed method achieves 91.22% accuracy. EHRAgent
reports 58.97% success rate on its 580-question experimental split; protocol
differences prevent a direct performance claim.”

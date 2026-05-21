# Answer Sheet 2 — Solid Fresher (Depth 2-3 Territory)
> "I know my project reasonably well, I understand ML fundamentals, I want a good score."
> This level will push you to Depth 3-4 in phases 2/3, score 6-7/10 on factual, and land 65-75% overall.

---

## How Scoring Works (Know This)

Every response you give is evaluated on:
- **Understanding score (0-10):** Do you genuinely get it, or are you reciting?
- **Completeness score (0-10):** Did you answer all parts of the question?
- **Accuracy score (0-10):** Are your technical claims correct?
- **Communication score (0-10):** Clear structure, no rambling?

`should_go_deeper = true` fires when your scores are high → the interviewer drills deeper.
`should_give_hint = true` fires when your scores are low → you get a nudge.

**Target for this sheet:** Scores around 6-8. `should_go_deeper` fires 2-3 times per project phase, taking you to depth 3 or 4.

---

## Phase 1 — Background

### Walk me through your background.
"I'm a final-year Computer Science student with a specialization in machine learning. My academic work has been centered around NLP and classification systems, and I've built two end-to-end projects — one in text analysis and one in recommendation systems. I'm comfortable with the full stack from data preprocessing to model evaluation. Outside class, I've been reading about production ML — specifically how to handle model drift and serving infrastructure."

### What made you interested in ML specifically?
"Honestly, it started with a course on statistics where we covered regression — I found it compelling that you could let data inform the model rather than hard-coding logic. Then I started doing Kaggle competitions and realized that the gap between theory and a working model was smaller than I expected. The projects that got me most engaged were the ones where I could see the output in a real UI — it made the engineering feel concrete."

### Tell me about a technical challenge you solved independently.
"In my NLP project, the model was overfitting badly on the training set — 94% train accuracy, 61% validation. I spent two days debugging and found the root cause: I had accidentally let the test labels leak into the feature engineering step because I was fitting a TF-IDF vectorizer on the full dataset before splitting. Fixing that brought validation accuracy to 83%. The lesson was to always use pipelines to prevent data leakage."

---

## Phase 2 & 3 — Project Deep Dive

### Depth 1 — Architecture
"[Project] is a [type] system. At a high level, it has three layers: a data ingestion layer that [X], a modeling layer using [architecture], and a serving layer that [exposes results via API/UI]. The data flows from [source] → [processing] → [model] → [output]. I chose this architecture because it separates concerns cleanly — you can retrain the model without touching the serving code."

### Depth 2 — Technical Decisions
"The core model decision was between [option A] and [option B]. I chose [A] because [specific technical reason — e.g., 'it handles variable-length sequences natively without padding overhead' or 'it gives better calibrated probabilities which mattered for our use case']. I also considered [option C] but rejected it because [training cost / inference latency / data requirement]. The feature engineering choice that made the biggest difference was [specific thing] — without it, the model was [result]; with it, [better result]."

### Depth 3 — Implementation & Metrics
"For training I used AdamW with a learning rate of 2e-5 and a linear warmup schedule over the first 10% of steps — standard for transformer fine-tuning. Batch size was 32, limited by GPU memory. The evaluation metric I optimized for was macro F1-score because the classes were imbalanced — class A had 3x more samples than class B. I tracked training on W&B and used early stopping based on validation F1. The most important hyperparameter was actually the learning rate: too high and the pretrained weights got destroyed, too low and it didn't adapt to the domain."

### Depth 4 — Failure Modes & Production
"The main failure mode was handling out-of-distribution inputs — text from domains very different from our training data. The model would confidently give wrong answers because softmax outputs don't reflect true uncertainty. I partially addressed this by adding a confidence threshold: if max softmax probability was below 0.6, we'd flag it for human review instead of auto-labeling. In production I'd go further and add proper uncertainty quantification — either Monte Carlo dropout or temperature scaling."

### Depth 5 — Theory (if pushed this far)
"The mathematical foundation is the attention mechanism — scaled dot-product attention computes compatibility scores between query and key vectors as (QK^T)/sqrt(d_k), then softmaps those to get weights for the value vectors. The sqrt(d_k) scaling prevents vanishing gradients in the softmax when dimensions are large. Multi-head attention runs this h times in parallel with different learned projections, letting the model attend to information from different representation subspaces simultaneously."

---

## Phase 4 — Factual ML (Solid Level Answers)

**What is the bias-variance tradeoff?**
"It's the fundamental tension between two sources of error. Bias is error from wrong assumptions — a too-simple model that systematically misses patterns. Variance is error from sensitivity to small fluctuations in training data — a too-complex model that memorizes noise. You reduce bias by increasing model complexity, but that increases variance. The optimal model sits at the minimum of their sum, which is total expected error. In practice, you find it through cross-validation."

**What is the vanishing gradient problem?**
"In deep networks, gradients are computed via backprop by chaining partial derivatives layer by layer. If those partial derivatives are repeatedly less than 1 — as happens with sigmoid or tanh activations — the gradient signal shrinks exponentially as you go back through layers. The result is that early layers barely update, making deep networks hard to train. Solutions: ReLU activations (derivative is 1 for positive values), batch normalization, residual connections, or gradient clipping."

**What is cross-entropy loss?**
"Cross-entropy loss measures how well the predicted probability distribution matches the true distribution. For a single sample, it's -sum(y_true * log(y_pred)). For binary classification, it simplifies to -(y*log(p) + (1-y)*log(1-p)). It penalizes confident wrong predictions much more heavily than uncertain wrong predictions, which is why it's preferred over MSE for classification — MSE treats all wrong predictions more uniformly."

**Explain precision and recall. When do you care more about one than the other?**
"Precision is of all the things I predicted positive, how many were actually positive. Recall is of all the actual positives, how many did I catch. They trade off: increasing recall usually decreases precision. You care more about recall when missing a true positive is costly — medical diagnosis, fraud detection, safety systems. You care more about precision when false positives are costly — spam filters (you don't want to delete real email), content moderation at scale."

**What is dropout?**
"Dropout randomly zeros out a fraction p of activations during training, forcing the network to not rely on any single neuron. This acts as a regularizer — it's equivalent to training an ensemble of 2^n different subnetworks and averaging their predictions at inference. You only apply dropout during training; at inference, you scale activations by (1-p) to maintain expected values, or equivalently use inverted dropout which scales during training instead."

---

## Phase 5 — Behavioral (Richer Versions)

### Where do you see yourself in five years?
"I want to be in a role where I'm responsible for end-to-end ML systems in production — not just training models, but owning the full lifecycle including monitoring, retraining triggers, and the data infrastructure that feeds them. Longer term, I'm interested in the intersection of ML and distributed systems — how you serve models at scale with low latency. I think the field is moving toward engineers who can do both the science and the infrastructure, and I want to be in that category."

### Most important challenges you've faced?
"The one that taught me the most was a debugging session on a recommendation system where the offline metrics were great but the online A/B test showed no improvement. Turned out the model was optimizing for click-through rate on items users had already seen, creating a filter bubble. Offline, this looked like good predictions because history is biased toward previously clicked items. The lesson was that offline and online metrics can diverge badly in recommendation — you need to test for novelty and diversity, not just accuracy."

### How do you work in a team?
"I prefer to own a well-defined boundary and coordinate through explicit interfaces. In my last project, the team of three split it so I owned data and preprocessing, one person owned modeling, and one owned the deployment API. We spent the first session agreeing on exactly what format data would flow between components — a JSON schema — so we could work independently for two weeks and then integrate in one day with almost no friction. The key was making the contract between pieces explicit early."

### Do you have any questions for me?
"Two questions: One — what's the highest depth level a candidate typically reaches in the project deep-dive, and what separates candidates who reach depth 4-5 from those who don't? Two — what's the most common gap you see in ML candidates right now — is it more on the theory side, the engineering side, or communication of technical ideas?"

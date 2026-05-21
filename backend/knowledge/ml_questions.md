# ML Interview Questions Bank

## Core ML / Fundamentals

### Q1: What's the trade-off between bias and variance?
**Answer:** If our model is too simple and has very few parameters then it may have high bias and low variance. On the other hand, if our model has a large number of parameters then it's going to have high variance and low bias. We need to find the right balance without overfitting or underfitting the data. This is known as the bias-variance trade-off.
**Category:** Core ML

### Q2: What is gradient descent?
**Answer:** An optimization algorithm used to find the values of parameters of a function that minimizes a cost function. It iteratively moves in the direction of steepest descent as defined by the negative of the gradient. Variants include batch, stochastic (SGD), and mini-batch gradient descent.
**Category:** Core ML

### Q3: Explain over- and under-fitting and how to combat them?
**Answer:** Underfitting occurs when model flexibility is inadequate to capture underlying patterns in data. Overfitting happens when the model is excessively flexible and memorizes training data including noise. Combat underfitting by increasing model complexity, adding features, reducing regularization. Combat overfitting by regularization, dropout, early stopping, data augmentation, or reducing model complexity.
**Category:** Core ML

### Q4: How do you combat the curse of dimensionality?
**Answer:** Feature Selection (selecting only the most relevant features), PCA (Principal Component Analysis for linear dimensionality reduction), Multidimensional Scaling, Locally Linear Embedding, t-SNE for visualization, autoencoders for nonlinear reduction.
**Category:** Core ML

### Q5: What is regularization, why do we use it, and give examples?
**Answer:** A technique that discourages learning a more complex or flexible model to avoid overfitting. L1 (Lasso) adds absolute value of weights to loss — promotes sparsity and feature selection. L2 (Ridge) adds squared weights — shrinks weights toward zero but doesn't eliminate them. Elastic Net combines both L1 and L2.
**Category:** Core ML

### Q6: Explain Principal Component Analysis (PCA)?
**Answer:** PCA is a dimensionality reduction technique that identifies directions (principal components) in which data varies the most. It projects data onto these directions to reduce dimensions while preserving maximum variance. Steps: standardize data, compute covariance matrix, find eigenvalues/eigenvectors, sort by eigenvalue magnitude, project data onto top-k eigenvectors.
**Category:** Core ML

### Q7: What is data normalization and why do we need it?
**Answer:** Rescaling values to fit in a specific range (e.g., 0-1 or standardizing to zero mean and unit variance) to ensure better convergence during gradient-based optimization. Without normalization, features with larger scales dominate the learning process. Common methods: min-max scaling, z-score standardization, robust scaling.
**Category:** Core ML

### Q8: What are the differences between supervised, unsupervised, and reinforcement learning?
**Answer:** Supervised learning uses labeled data to learn a mapping from inputs to outputs (classification, regression). Unsupervised learning finds hidden patterns in unlabeled data (clustering, dimensionality reduction, anomaly detection). Reinforcement learning learns policies through trial-and-error interaction with an environment to maximize cumulative rewards.
**Category:** Core ML

### Q9: What is an imbalanced dataset and how do you handle it?
**Answer:** A dataset where target categories have significantly different proportions. Solutions include: oversampling minority class (SMOTE), undersampling majority class, using appropriate metrics (F1, precision-recall, AUC-ROC instead of accuracy), cost-sensitive learning, ensemble methods like balanced random forests, and data augmentation.
**Category:** Core ML

### Q10: Why do we need validation and test sets? What's the difference?
**Answer:** Training set fits model parameters. Validation set tunes hyperparameters and makes architectural decisions without biasing toward test data. Test set measures final generalization performance on completely unseen data. Using only train/test risks overfitting hyperparameters to the test set.
**Category:** Core ML

### Q11: What is stratified cross-validation and when should you use it?
**Answer:** Cross-validation that preserves the percentage of samples for each class across all folds. Essential when dealing with imbalanced datasets or multi-distribution data, ensuring each fold is representative of the overall dataset distribution.
**Category:** Core ML

### Q12: Why do ensembles typically score higher than individual models?
**Answer:** Different models make different errors on different parts of the data. Combining them compensates for individual weaknesses through averaging (reduces variance) or voting. Techniques include bagging (Random Forest), boosting (XGBoost, AdaBoost), and stacking.
**Category:** Core ML

## Deep Learning

### Q13: Why is ReLU better and more widely used than Sigmoid?
**Answer:** Computational efficiency (simple thresholding vs exponential), reduced likelihood of vanishing gradient problem (gradient is either 0 or 1, not squashed), promotes sparsity in network activations. Variants like Leaky ReLU and GELU address the dying ReLU problem.
**Category:** Deep Learning

### Q14: What is batch normalization and why does it work?
**Answer:** Normalizes layer inputs to have zero mean and unit variance within each mini-batch. Benefits: enables higher learning rates, acts as regularization, reduces sensitivity to initialization, and stabilizes training by reducing internal covariate shift. Applied before or after activation functions.
**Category:** Deep Learning

### Q15: What is the significance of Residual Networks (ResNets)?
**Answer:** Residual connections (skip connections) allow direct feature access from previous layers, enabling training of very deep networks (100+ layers) by mitigating the vanishing gradient problem. The network learns residual functions F(x) = H(x) - x rather than directly learning H(x), making identity mappings easy to learn.
**Category:** Deep Learning

### Q16: What is dropout and how does it work?
**Answer:** During training, randomly sets a fraction of neuron activations to zero. This prevents co-adaptation of neurons, acts as an ensemble of subnetworks, and provides regularization. At inference time, all neurons are active but weights are scaled by the keep probability. Typical rates: 0.2-0.5.
**Category:** Deep Learning

### Q17: Explain the vanishing and exploding gradient problems.
**Answer:** Vanishing gradients: in deep networks, gradients become exponentially small through backpropagation, making early layers learn very slowly. Caused by sigmoid/tanh activations. Solutions: ReLU, residual connections, batch normalization. Exploding gradients: gradients become exponentially large, causing instability. Solutions: gradient clipping, proper initialization (Xavier/He), batch normalization.
**Category:** Deep Learning

### Q18: What is transfer learning and when should you use it?
**Answer:** Using a model pretrained on a large dataset and fine-tuning it for a specific task. Use when: limited labeled data for target task, source and target domains are related, computational resources are limited. Strategies: feature extraction (freeze pretrained layers), fine-tuning (unfreeze some/all layers with small learning rate).
**Category:** Deep Learning

## Natural Language Processing

### Q19: What is the Transformer architecture and why is it important?
**Answer:** A neural architecture based entirely on self-attention mechanisms, replacing recurrence and convolutions. Key components: multi-head self-attention, positional encoding, feed-forward networks, layer normalization. Enables parallel processing of sequences (unlike RNNs), captures long-range dependencies efficiently, and is the foundation for BERT, GPT, and modern LLMs.
**Category:** NLP

### Q20: What is attention mechanism and how does self-attention work?
**Answer:** Attention computes weighted combinations of values based on query-key compatibility. Self-attention: Q, K, V are all derived from the same input. Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V. Multi-head attention runs multiple attention functions in parallel with different learned projections. Enables the model to attend to different parts of the input simultaneously.
**Category:** NLP

### Q21: What is Retrieval-Augmented Generation (RAG)?
**Answer:** RAG combines a retrieval system with a generative model. Documents are chunked, embedded into vectors, and stored in a vector database. At query time, relevant documents are retrieved via similarity search and provided as context to the LLM for generating grounded responses. Reduces hallucinations, enables knowledge updates without retraining, and provides attribution.
**Category:** NLP

### Q22: What are word embeddings and why are they useful?
**Answer:** Dense vector representations of words where semantic similarity is captured by vector proximity. Word2Vec (Skip-gram, CBOW), GloVe, and FastText learn these representations. They capture analogies (king - man + woman ≈ queen), reduce dimensionality compared to one-hot encoding, and serve as input features for downstream NLP tasks.
**Category:** NLP

### Q23: Explain the difference between BERT and GPT architectures.
**Answer:** BERT uses bidirectional transformer encoder trained with masked language modeling and next sentence prediction — good for understanding tasks (classification, NER, QA). GPT uses unidirectional (left-to-right) transformer decoder trained with causal language modeling — good for generation tasks. BERT sees context from both directions; GPT only sees left context during training.
**Category:** NLP

### Q24: What are the different chunking strategies in RAG systems?
**Answer:** Fixed-size chunking (split by character/token count with overlap), sentence-based (split at sentence boundaries), semantic chunking (split when embedding similarity drops), recursive character splitting (try multiple separators hierarchically), document-structure-based (use headers, paragraphs). Trade-offs: smaller chunks = more precise retrieval but less context; larger chunks = more context but noisier retrieval.
**Category:** NLP

### Q25: What is fine-tuning vs RAG? When would you use each?
**Answer:** Fine-tuning modifies model weights on task-specific data — best for adapting model behavior, style, or learning new tasks. RAG augments prompts with retrieved documents — best for grounding responses in specific, updatable knowledge. Use fine-tuning when you need behavioral changes; use RAG when you need factual grounding with frequently changing information. RAG is cheaper and doesn't risk catastrophic forgetting.
**Category:** NLP

## Computer Vision

### Q26: Why use convolutions for images rather than fully connected layers?
**Answer:** Convolutions preserve spatial information through local connectivity, achieve translation invariance through shared weights, and require far fewer parameters than FC layers. A convolution kernel acts as a feature detector that slides across the image, detecting patterns regardless of position. Parameter sharing makes CNNs practical for high-resolution images.
**Category:** Computer Vision

### Q27: What is the purpose of max-pooling in CNNs?
**Answer:** Reduces spatial dimensions (computation and memory), provides local translation invariance, selects the most prominent features from each region. Alternatives include average pooling, strided convolutions, and global average pooling (often used before final classification layer).
**Category:** Computer Vision

### Q28: Why use many small 3x3 kernels rather than fewer large ones?
**Answer:** Two 3x3 convolutions have the same receptive field as one 5x5 but with fewer parameters (18 vs 25) and more non-linear activation functions between them. This was popularized by VGGNet. More layers with small filters = deeper feature hierarchies with less computation.
**Category:** Computer Vision

### Q29: Explain non-maximum suppression (NMS) in object detection.
**Answer:** After detection, multiple overlapping bounding boxes may predict the same object. NMS resolves this: sort boxes by confidence score, select highest-scoring box, remove all boxes with IoU above threshold with selected box, repeat for remaining boxes. Variants: Soft-NMS (decays scores instead of hard removal), weighted NMS.
**Category:** Computer Vision

### Q30: What is data augmentation for images? Give examples.
**Answer:** Synthesizing new training data by applying transformations to existing images. Examples: geometric (resize, flip, rotate, crop, affine), photometric (brightness, contrast, saturation, hue jitter), noise injection (Gaussian, salt-and-pepper), advanced (Mixup, CutMix, CutOut, random erasing). Helps reduce overfitting and improves model robustness to real-world variations.
**Category:** Computer Vision

### Q31: Explain YOLO architecture and its key innovations.
**Answer:** YOLO (You Only Look Once) frames object detection as a single regression problem. Divides image into grid cells, each predicting bounding boxes and class probabilities simultaneously. Key innovations: single-pass detection (vs two-stage like R-CNN), real-time speed, global context reasoning. YOLOv8 uses anchor-free detection, decoupled head, and CSPDarknet backbone.
**Category:** Computer Vision

### Q32: What is the encoder-decoder structure in segmentation?
**Answer:** Encoder extracts hierarchical features through downsampling (like a classification CNN). Decoder upsamples features back to original resolution using transposed convolutions, bilinear interpolation, or unpooling. Skip connections between encoder and decoder preserve fine-grained spatial details lost during downsampling. Used in U-Net, SegNet, DeepLab.
**Category:** Computer Vision

## MLOps & Production

### Q33: What is model drift and how do you detect/handle it?
**Answer:** Model performance degrades over time due to changes in data distribution (data drift) or relationship between features and target (concept drift). Detection: monitor prediction distributions, feature statistics, and performance metrics over time. Handling: scheduled retraining, trigger-based retraining when drift detected, online learning, ensemble of models from different time periods.
**Category:** MLOps

### Q34: How do you serve ML models in production?
**Answer:** Options: REST API (Flask/FastAPI), gRPC for low-latency, batch inference pipelines, edge deployment (ONNX, TensorRT). Considerations: latency requirements, throughput, model size, scaling (horizontal vs vertical), A/B testing, canary deployments, model versioning, monitoring, and rollback capabilities.
**Category:** MLOps

### Q35: What are embedding models and vector databases?
**Answer:** Embedding models convert data (text, images) into dense vector representations. Vector databases (Pinecone, Weaviate, Milvus, pgvector) store and efficiently search these vectors using approximate nearest neighbor algorithms like HNSW (Hierarchical Navigable Small World graphs) or IVFFlat (Inverted File with Flat quantization). HNSW offers better recall with log search time; IVFFlat is more memory efficient for large datasets.
**Category:** MLOps

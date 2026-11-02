# Photo model update — 2026-10-25

## Measured result

The deployed composition model is a ResNet18 with a **2×2 spatial pooling head**.
This preserves coarse subject placement that global average pooling discards.
It was trained on the original fixed split: **525 training / 111 validation /
111 test images**, with four visually reviewed training-label corrections.
Validation and test membership and labels were kept fixed.

| Metric | Previous checkpoint report | Deployed checkpoint |
| --- | ---: | ---: |
| Test composition accuracy | 63.06% | **66.67%** |
| Test macro-F1 | 0.6098 | **0.6435** |
| Validation accuracy | 63.96% | **66.67%** |
| Validation macro-F1 | 0.6348 | **0.6561** |

The updated model's **66.67%** test accuracy was reproduced through the
application's serving decision path using the original full-resolution held-out
files. It was retrained on the fixed train+validation images only after the
spatial-pool-2 architecture and training schedule were selected on validation.

The final checkpoint used 636 train+validation images for 16 epochs. Training
used a 0.0003 head learning rate, batch size 32, frozen backbone BatchNorm
statistics, geometry-preserving augmentation, and seed 42. Inference averages
original and mirrored logits. The test result is **66.67% accuracy** and
**0.6435 macro-F1** on 111 untouched images.

No validation confidence threshold met the target of 80% accuracy on at least
20 selected images. The active metadata therefore marks style predictions as
tentative. This retains the predicted style and its confidence while avoiding
unsupported certainty or composition-specific corrective advice.

## Scoring and serving corrections

- The learned NIMA aesthetic score now drives the overall rating.
- Composition classification probability is kept separate from photo quality.
- NIMA's score is the expected value of its rating distribution; it is no
  longer modified by composition confidence.
- Composition training and serving share full-frame image encoding, resizing,
  normalization, EXIF handling, and flip aggregation.
- NIMA training and serving share the same PIL preprocessing.
- The singleton image service passes request-local pixels to the classifier,
  preventing one upload from taking another request's remembered file path.
- Uniform images return `Unclear` composition. Empty or sparse edge maps no
  longer receive perfect symmetry scores merely because their backgrounds
  match.
- The UI distinguishes possible style, geometric match, and learned aesthetic
  appeal. It does not infer the photographer's skill from an aesthetic rating.
- Unavailable pose detection is reported explicitly. Landmark visibility is
  identified as visibility, rather than a judgment of natural posing.
- The unsupported landing-page `99.9% accuracy` claim was replaced with the
  actual scale of the human-rated aesthetic training data.

## CPU/GPU training path

The RTX 3050 performs the forward/backward passes with CUDA mixed precision.
The CPU decodes cached JPEGs, applies geometry-preserving transforms, and
prefetches batches; pinned memory and non-blocking host-to-device copies are
enabled when CUDA is available. The small local dataset was benchmarked with
multiple worker counts, and more workers were not automatically faster because
worker startup/IPC overhead dominates this workload. Use `--workers 0` for the
fastest measured local run, or `--workers 2` when CPU prefetching is desired.

## Aesthetic training experiment

A deeper NIMA fine-tune was run against the same AVA splits, unfreezing eight
blocks and adding an expected-score loss. It regressed on validation and was
not promoted. The existing stronger aesthetic checkpoint remains active:

- Test MAE: **0.4603**
- Test Spearman: **0.5764**
- Test Pearson: **0.5852**
- Binary rating-above-5 accuracy: **77.52%**

Future resumed NIMA runs now compare against the starting checkpoint's
validation EMD, retaining the starting weights when fine-tuning regresses.

## Artifacts

- `backend/ml_models/trained/composition_model_best.pth`
- `backend/ml_models/trained/composition_metadata.json`
- `backend/ml_models/trained/composition_data_audit.json`
- `backend/ml_models/trained/photo_pipeline_evaluation.json`
- `backend/ml_models/trained/aesthetic_nima.pth`
- `backend/ml_models/trained/aesthetic_training_report.json`
- `backend/training/retrain_composition_trainval.py`
- `backend/training/benchmark_composition_embeddings.py`
- `backend/training/benchmark_composition_ensemble.py`

The serving report records predictions, methods, confidence, the checkpoint
hash, and complete-analysis smoke checks. All 111 held-out photographs use the
learned composition classifier. The uniform-red smoke image returns `Unclear`;
its overall score equals the learned aesthetic score (**4.9**).

An earlier 18% heuristic/fallback benchmark used an already-open Windows
temporary file, which prevented the CNN from reading it. That result is not a
valid benchmark of the previous production hybrid and is excluded here.

## Reproduce

Verification of this update: **43 focused backend tests**, **3 Django API
tests**, and **6 frontend tests** passed. The frontend production build succeeds
with existing dependency/lint warnings, and the modified Python modules compile.

From `backend/`, using the training virtual environment:

```bash
.venv-training/Scripts/python.exe -u training/train_model.py --data-dir training_data --save-dir ml_models/trained/runs/composition_spatial2_reviewed --split-manifest ml_models/trained/composition_data_audit.json --spatial-pool-size 2 --freeze-batchnorm --epochs 100 --batch-size 32 --learning-rate 0.0003 --workers 0 --patience 20 --seed 42 --defer-test
.venv-training/Scripts/python.exe -u training/train_model.py --data-dir training_data --save-dir ml_models/trained/runs/composition_spatial2_reviewed --batch-size 32 --workers 0 --seed 42 --evaluate-only
.venv-training/Scripts/python.exe -u training/evaluate_photo_pipeline.py --data-dir training_data
.venv-training/Scripts/python.exe -u training/retrain_composition_trainval.py --data-dir training_data --save-dir ml_models/trained/runs/composition_trainval --split-manifest ml_models/trained/composition_data_audit.json --epochs 16 --batch-size 32 --learning-rate 0.0003 --workers 0 --seed 42 --freeze-batchnorm
.venv-training/Scripts/python.exe -m pytest tests/test_photo_pipeline.py tests/test_conversation_pipeline.py -q
.venv-training/Scripts/python.exe manage.py test api
```

From `frontend/`:

```bash
npm test -- --watchAll=false --runInBand
npm run build
```

Restart a running backend after replacing weights so its process-wide model
singleton loads the updated checkpoint.

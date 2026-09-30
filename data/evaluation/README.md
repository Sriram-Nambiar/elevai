# Evaluation protocol

Run `python scripts/evaluate_benchmark.py` after adding scenes whose annotation file has `review_status: "verified"`. The script reports same-category detector box precision, recall, F1, and mean IoU at a 0.50 IoU matching threshold, plus the number of fit-rule violations on the default catalog package.

The script deliberately leaves `fit_error_mm` empty until independent measured component geometry and a valid metric camera/plane calibration are available. It does not infer a metric error from relative monocular depth. Render realism, proposal factual errors, and time saved require a human study and are reported as unmeasured rather than fabricated.

For a human evaluation, use at least two reviewers who did not create the render, rate realism and geometry preservation blind to the selected option, audit every proposal claim against its catalog/site evidence, and time the same task performed manually and with Elevai. Report participant count, scene count, task definition, raw scores, and limitations. Do not claim representative accuracy from the current single provisional scene.

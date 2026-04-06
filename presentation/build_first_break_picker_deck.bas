Attribute VB_Name = "BuildFirstBreakPickerDeck"
Option Explicit

' BuildFirstBreakPickerDeck.bas
' Import this module into PowerPoint VBA and run BuildSeismicFirstBreakPickerPresentation.
' The macro builds a 25-35 minute technical deck from local repository artifacts.
' It embeds images, adds local artifact hyperlinks, and writes speaker notes.

Private Const REPO_ROOT As String = "D:\github_repos\seismic-first-break-picker"
Private Const OUT_REL As String = "presentation\first_break_picker_vba_generated.pptx"

Private Const FONT_HEAD As String = "Aptos Display"
Private Const FONT_BODY As String = "Aptos"
Private Const FONT_MONO As String = "Consolas"

Private C_INK As Long
Private C_MUTED As Long
Private C_BG As Long
Private C_PANEL As Long
Private C_LINE As Long
Private C_BLUE As Long
Private C_GREEN As Long
Private C_ORANGE As Long
Private C_RED As Long

Public Sub BuildSeismicFirstBreakPickerPresentation()
    Dim pres As Presentation
    Dim outPath As String
    
    InitColors
    
    Set pres = Application.Presentations.Add
    pres.PageSetup.SlideSize = ppSlideSizeOnScreen16x9
    pres.PageSetup.SlideWidth = 13.333333 * 72
    pres.PageSetup.SlideHeight = 7.5 * 72
    
    Slide01_Title pres
    Slide02_Task pres
    Slide03_Scope pres
    Slide04_HDF5 pres
    Slide05_RawToImage pres
    Slide06_ExportMethod pres
    Slide07_ExportStats pres
    Slide08_LabelOverlay pres
    Slide09_Baseline pres
    Slide10_ResidualReason pres
    Slide11_Features pres
    Slide12_Model pres
    Slide13_ValidationProtocol pres
    Slide14_ValidationResults pres
    Slide15_TestResults pres
    Slide16_VisualExamples pres
    Slide17_ErrorAnalysis pres
    Slide18_Conclusion pres
    SlideA1_Commands pres
    SlideA2_RepoStructure pres
    SlideA3_Hyperparameters pres
    SlideA4_Limitations pres
    
    outPath = PathJoin(REPO_ROOT, OUT_REL)
    pres.SaveAs outPath
    MsgBox "Generated presentation:" & vbCrLf & outPath, vbInformation, "First-Break Picker"
End Sub

Private Sub InitColors()
    C_INK = RGB(28, 35, 43)
    C_MUTED = RGB(88, 99, 110)
    C_BG = RGB(255, 255, 255)
    C_PANEL = RGB(244, 247, 250)
    C_LINE = RGB(204, 212, 220)
    C_BLUE = RGB(0, 94, 148)
    C_GREEN = RGB(25, 121, 80)
    C_ORANGE = RGB(170, 92, 18)
    C_RED = RGB(178, 45, 45)
End Sub

' ---------------------------------------------------------------------------
' Main slide definitions
' ---------------------------------------------------------------------------

Private Sub Slide01_Title(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "")
    AddTitle s, "Halfmile First-Break Picking", 0.75, 1.05, 11.7, 0.72, 35
    AddText s, "CPU-only pipeline for reconstructing 2D seismic panels, learning a residual first-break correction, and validating on held-out Halfmile shots.", 0.82, 1.95, 10.8, 0.78, 18, C_MUTED, False
    AddMetric s, "Verified asset", "Halfmile", 0.82, 3.05, 2.5, 1.05, C_BLUE
    AddMetric s, "Task output", "Code + deck", 3.55, 3.05, 2.5, 1.05, C_GREEN
    AddMetric s, "Runtime stance", "CPU only", 6.28, 3.05, 2.5, 1.05, C_ORANGE
    AddMetric s, "Validation", "Shot-disjoint", 9.01, 3.05, 2.5, 1.05, C_RED
    AddLinkButton s, "Open README", "README.md", 0.82, 5.25, 2.1
    AddLinkButton s, "Open reports", "reports\evaluation", 3.15, 5.25, 2.4
    AddLinkButton s, "Open deck folder", "presentation", 5.8, 5.25, 2.55
    AddFooter s, 1, "Self-contained local deck. No external API calls required."
    AddNotes s, "Open by framing the scope clearly: Halfmile is verified end to end. Multi-asset execution is optional for this task and the pipeline is ready for the other raw HDF5 assets."
End Sub

Private Sub Slide02_Task(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "1. Problem Statement and Goal")
    AddBullets s, Array( _
        "Automatically identify seismic first breaks from labeled HDF5 trace data.", _
        "Reconstruct 2D seismic images from flat trace storage using receiver geometry.", _
        "Pair each 2D image with manual first-break labels stored in SPARE1.", _
        "Prepare code and a 25-35 minute technical presentation covering data, method, validation, and results."), _
        0.65, 1.15, 6.05, 3.5, 16, True
    AddImage s, "reports\figures\exported_segment_previews\Halfmile_shot20241112_seg003.png", 7.1, 1.05, 5.55, 3.7, "Example exported 2D panel with manual first-break picks"
    AddCallout s, "Core interpretation", "The task is not only a trace-level prediction problem. It first requires image reconstruction so neighboring traces are meaningful.", 7.1, 5.0, 5.55, 1.05, C_BLUE
    AddFooter s, 2, "Requirement mapping: reconstruct panels, attach labels, build an automated picker, validate."
    AddNotes s, "Spend little time on general seismic theory. Emphasize the two practical tasks: panel reconstruction and first-break prediction."
End Sub

Private Sub Slide03_Scope(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "2. Dataset Scope")
    AddText s, "The task lists four assets. Testing all four is optional. The local end-to-end validation in this submission was performed on Halfmile.", 0.65, 1.0, 12.0, 0.55, 16, C_MUTED, False
    AddTable s, Array( _
        Array("Asset", "Task-listed file", "Submission status"), _
        Array("Brunswick", "Brunswick_orig_1500ms_V2.hdf5", "Pipeline-ready, not locally validated"), _
        Array("Halfmile", "Halfmile3D_add_geom_sorted.hdf5", "Verified end to end"), _
        Array("Lalor", "Lalor_raw_z_1500ms_norp_geom_v3.hdf5", "Pipeline-ready, not locally validated"), _
        Array("Sudbury", "preprocessed_Sudbury3D.hdf", "Pipeline-ready, not locally validated")), _
        0.75, 1.95, 11.8, 2.6
    AddCallout s, "Precise scope statement", "This deck reports empirical results for Halfmile. The code carries asset_name metadata through export, splits, datasets, and evaluation for later multi-asset runs.", 0.75, 4.95, 11.8, 1.05, C_GREEN
    AddFooter s, 3, "Use this slide to avoid overclaiming cross-asset validation."
    AddNotes s, "Say plainly that testing all four was optional. The verified result is Halfmile, and the design is reusable."
End Sub

Private Sub Slide04_HDF5(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "3. HDF5 Data Layout")
    AddTable s, Array( _
        Array("Field", "Role"), _
        Array("data_array", "Trace samples, trace count by sample count"), _
        Array("SHOTID / SHOT_PEG", "Shot grouping key"), _
        Array("REC_PEG / REC_X", "Receiver ordering and split basis"), _
        Array("REC_Y / REC_HT", "Stored receiver geometry context"), _
        Array("SOURCE_X / SOURCE_Y", "Shot geometry context"), _
        Array("COORD_SCALE / HT_SCALE", "SEG-Y style scaling"), _
        Array("SAMP_RATE", "Convert labels from ms to sample index"), _
        Array("SPARE1", "Manual first-break label in ms")), _
        0.65, 1.1, 6.25, 4.9
    AddCode s, "with h5py.File(path, ""r"") as handle:" & vbCrLf & _
               "    group = handle[""TRACE_DATA/DEFAULT""]" & vbCrLf & _
               "    data_array = group[""data_array""]" & vbCrLf & _
               "    labels_ms = group[""SPARE1""][:]" & vbCrLf & _
               "    sample_ms = group[""SAMP_RATE""][0] / 1000.0", _
               7.2, 1.35, 5.25, 1.85, 10
    AddCallout s, "Label rule", "SPARE1 stores first-break time in milliseconds. Values 0 and -1 are treated as unlabeled and excluded from metrics.", 7.2, 3.6, 5.25, 1.05, C_ORANGE
    AddLinkButton s, "Open inspect_hdf5.py", "scripts\inspect_hdf5.py", 7.2, 5.35, 2.55
    AddLinkButton s, "Open data.py", "seismic_first_break_picker\data.py", 9.95, 5.35, 2.25
    AddFooter s, 4, "HDF5 group: TRACE_DATA/DEFAULT. Label key: SPARE1."
    AddNotes s, "This slide proves the pipeline uses the task-native HDF5 fields, not a pre-converted toy dataset."
End Sub

Private Sub Slide05_RawToImage(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "4. Raw Trace Storage Is Not the Final Image")
    AddImage s, "reports\figures\Halfmile_preview_shot.png", 0.65, 1.0, 7.2, 4.65, "Receiver-ordered raw shot preview"
    AddBullets s, Array( _
        "HDF5 stores traces as a flat table.", _
        "Receiver geometry defines useful trace neighborhoods.", _
        "Local ML patches need coherent adjacent traces.", _
        "Reconstruction is therefore a first-class pipeline stage."), _
        8.15, 1.25, 4.55, 3.1, 16, False
    AddLinkButton s, "Open preview_one_shot.py", "scripts\preview_one_shot.py", 8.15, 5.15, 2.85
    AddFooter s, 5, "Transition: from flat traces to receiver-ordered 2D panels."
    AddNotes s, "Use the image to show why first breaks behave like lines over panels rather than independent trace labels."
End Sub

Private Sub Slide06_ExportMethod(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "5. Segment Export Method")
    AddFlow s, Array("Group by SHOTID", "Order receivers", "Split large gaps", "Filter panels", "Save NPZ + manifest"), 0.65, 1.05, 12.0
    AddImage s, "reports\figures\split_preview_20021449\shot_20021449_segment_00.png", 0.75, 2.35, 5.75, 3.65, "Example split panel"
    AddBullets s, Array( _
        "Shot identity: SHOTID, with SHOT_PEG fallback.", _
        "Primary receiver order: REC_PEG.", _
        "Fallback receiver order: REC_X.", _
        "Large receiver gaps: jump_factor = 8.0.", _
        "Filtering: at least 80 traces and at least 70 valid labels."), _
        6.9, 2.35, 5.6, 3.35, 15, False
    AddLinkButton s, "Open export_segments.py", "scripts\export_segments.py", 6.9, 5.95, 2.7
    AddFooter s, 6, "Exported .npz panels are generated artifacts and ignored by .gitignore."
    AddNotes s, "Tie each export step to image coherence and supervised label quality."
End Sub

Private Sub Slide07_ExportStats(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "6. Export Statistics")
    AddMetric s, "Exported segments", "5,391", 0.75, 1.25, 2.75, 1.1, C_BLUE
    AddMetric s, "Usable shots", "689", 3.75, 1.25, 2.35, 1.1, C_GREEN
    AddMetric s, "Labeled traces", "993,189", 6.35, 1.25, 2.55, 1.1, C_ORANGE
    AddMetric s, "Label coverage", "90.33%", 9.15, 1.25, 2.55, 1.1, C_RED
    AddTable s, Array( _
        Array("Metric", "Value"), _
        Array("Raw Halfmile traces", "1,099,559"), _
        Array("Samples per trace", "751"), _
        Array("Sampling interval", "2.0 ms"), _
        Array("Unique raw shots", "690"), _
        Array("Retained usable shots", "689"), _
        Array("Final retained segments", "5,391")), _
        0.9, 3.0, 5.5, 3.05
    AddCallout s, "Interpretation", "The export retains broad Halfmile coverage while removing panels too short or too sparsely labeled for reliable supervised evaluation.", 6.95, 3.25, 5.35, 1.35, C_BLUE
    AddLinkButton s, "Open methodology summary", "reports\evaluation\methodology_results_summary.md", 6.95, 5.05, 3.25
    AddFooter s, 7, "Use these numbers to establish validated run scale."
    AddNotes s, "Make clear that the statistics are from the current local Halfmile run."
End Sub

Private Sub Slide08_LabelOverlay(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "7. Manual Label Overlay")
    AddImage s, "reports\figures\exported_segment_previews\Halfmile_shot20241112_seg003.png", 0.7, 1.0, 8.0, 4.95, "Exported segment with manual first-break picks"
    AddBullets s, Array( _
        "Time sample is on Y and receiver trace is on X.", _
        "Manual picks are converted from milliseconds to sample index.", _
        "Unlabeled traces are masked from scoring.", _
        "This is the qualitative sanity check before training."), _
        9.05, 1.25, 3.7, 3.2, 15, False
    AddLinkButton s, "Open exported previews", "reports\figures\exported_segment_previews", 9.05, 5.15, 3.05
    AddFooter s, 8, "The red pick line comes from SPARE1 labels."
    AddNotes s, "If this overlay were wrong, all later metrics would be suspect. This slide establishes label alignment."
End Sub

Private Sub Slide09_Baseline(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "8. Refined Baseline Picker")
    AddFlow s, Array("Envelope", "Noise estimate", "Threshold trigger", "Smooth prior", "Derivative refine", "Final smooth"), 0.65, 1.0, 12.1
    AddImage s, "reports\figures\baseline_refined_preview_shot20241112_seg003.png", 0.7, 2.25, 7.55, 3.85, "Refined baseline preview"
    AddBullets s, Array( _
        "Model-free fallback line.", _
        "Smoothed amplitude envelope per trace.", _
        "Early-time noise estimate and threshold trigger.", _
        "Cross-trace smoothing and local derivative refinement."), _
        8.55, 2.3, 4.1, 3.15, 15, False
    AddLinkButton s, "Open baseline.py", "seismic_first_break_picker\baseline.py", 8.55, 5.65, 2.2
    AddFooter s, 9, "The ML model predicts a correction to this baseline."
    AddNotes s, "Position the baseline as a practical and interpretable starting point, not as a discarded naive method."
End Sub

Private Sub Slide10_ResidualReason(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "9. Why Add Learned Correction")
    AddImage s, "reports\evaluation\figures\regression_Halfmile_shot20121514_seg024.png", 0.7, 1.0, 7.6, 4.9, "Regression example: manual, baseline, corrected"
    AddBullets s, Array( _
        "The refined baseline is consistent but can drift on hard panels.", _
        "Many errors are local and systematic rather than random.", _
        "Residual target true_pick - baseline_pick is easier to learn on CPU.", _
        "The baseline still acts as a fallback and anchor."), _
        8.65, 1.25, 3.95, 3.3, 15, False
    AddCallout s, "Failure case included", "The model improves most segments, but can regress when the baseline starts far from the true line.", 8.65, 4.9, 3.95, 1.2, C_ORANGE
    AddFooter s, 10, "This slide motivates the residual ML stage without overclaiming."
    AddNotes s, "Showing a failure case helps make the results slide more credible."
End Sub

Private Sub Slide11_Features(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "10. ML Correction Dataset Design")
    AddPatchDiagram s, 0.9, 1.25, 5.0, 4.55
    AddTable s, Array( _
        Array("Design choice", "Value"), _
        Array("Patch height", "81 samples"), _
        Array("Patch width", "5 traces"), _
        Array("Flattened features", "405"), _
        Array("Target", "true - baseline"), _
        Array("Trace stride", "3"), _
        Array("Correction filter", "|target| <= 60 samples")), _
        6.55, 1.35, 5.7, 3.65
    AddCallout s, "Reasoning", "The patch gives time context and neighboring trace context while staying small enough for fast CPU training.", 6.55, 5.25, 5.7, 0.85, C_BLUE
    AddLinkButton s, "Open correction.py", "seismic_first_break_picker\correction.py", 0.9, 6.02, 2.35
    AddFooter s, 11, "Correction target is measured in sample-index units and evaluated in milliseconds."
    AddNotes s, "Explain the center point, neighboring traces, and residual target. Avoid going too deep into implementation."
End Sub

Private Sub Slide12_Model(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "11. CPU-First Model Choice")
    AddBullets s, Array( _
        "Model family: HistGradientBoostingRegressor.", _
        "Good fit for dense tabular patch vectors.", _
        "No GPU or deep-learning framework required.", _
        "Four compact candidate configurations evaluated on validation examples.", _
        "Final model refit on train + validation after selection."), _
        0.75, 1.1, 5.6, 3.4, 16, False
    AddTable s, Array( _
        Array("Hyperparameter", "Value"), _
        Array("learning_rate", "0.04"), _
        Array("max_iter", "260"), _
        Array("max_depth", "8"), _
        Array("min_samples_leaf", "25"), _
        Array("l2_regularization", "0.0"), _
        Array("random_state", "42")), _
        7.0, 1.1, 5.0, 3.55
    AddLinkButton s, "Open modeling.py", "seismic_first_break_picker\modeling.py", 0.75, 5.25, 2.2
    AddLinkButton s, "Open training report", "data\processed\ml_correction_training_report.json", 3.15, 5.25, 2.95
    AddFooter s, 12, "requirements.txt pins scikit-learn to 1.7.0 for saved model compatibility."
    AddNotes s, "Frame this as a pragmatic engineering choice under CPU-only constraints."
End Sub

Private Sub Slide13_ValidationProtocol(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "12. Validation Protocol and Leakage Control")
    AddCallout s, "Main validation rule", "Split by asset_name + shot_id, not by individual segment file. This prevents same-shot leakage across training and held-out evaluation.", 0.75, 1.05, 11.8, 0.95, C_BLUE
    AddTable s, Array(Array("Split", "Shots", "Segments"), Array("Train", "482", "3,779"), Array("Validation", "68", "526"), Array("Test", "139", "1,086")), 0.9, 2.55, 5.3, 2.3
    AddTable s, Array(Array("Overlap check", "Value"), Array("Train vs validation", "0"), Array("Train vs test", "0"), Array("Validation vs test", "0"), Array("Seed", "42"), Array("Ratios", "70 / 10 / 20")), 7.0, 2.35, 5.1, 2.9
    AddLinkButton s, "Open split summary", "data\processed\splits\split_summary.json", 0.9, 5.45, 2.7
    AddLinkButton s, "Open splits.py", "seismic_first_break_picker\splits.py", 3.8, 5.45, 2.05
    AddFooter s, 13, "Shot-disjoint evaluation is more defensible than random segment splitting."
    AddNotes s, "This is one of the most important slides. Emphasize leakage prevention."
End Sub

Private Sub Slide14_ValidationResults(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "13. Validation Selection Results")
    AddMetric s, "Baseline MAE", "18.769 ms", 0.85, 1.2, 2.7, 1.05, C_MUTED
    AddMetric s, "Corrected MAE", "10.643 ms", 3.85, 1.2, 2.7, 1.05, C_GREEN
    AddMetric s, "MAE gain", "8.126 ms", 6.85, 1.2, 2.5, 1.05, C_BLUE
    AddMetric s, "Best candidate", "#3", 9.65, 1.2, 2.1, 1.05, C_ORANGE
    AddTable s, Array( _
        Array("Candidate", "Corrected MAE", "Corrected RMSE", "MAE gain"), _
        Array("0", "11.069", "22.494", "7.700"), _
        Array("1", "11.080", "22.614", "7.688"), _
        Array("2", "11.407", "22.677", "7.361"), _
        Array("3", "10.643", "22.079", "8.126")), _
        0.95, 3.0, 7.0, 2.65
    AddCallout s, "Selection rule", "Candidate 3 had the lowest corrected validation MAE and was refit on train plus validation examples.", 8.35, 3.15, 3.95, 1.15, C_GREEN
    AddLinkButton s, "Open training report", "data\processed\ml_correction_training_report.json", 8.35, 4.85, 2.95
    AddFooter s, 14, "Validation examples are correction examples centered on baseline picks."
    AddNotes s, "Keep validation results separate from final held-out test results."
End Sub

Private Sub Slide15_TestResults(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "14. Quantitative Held-Out Test Results")
    AddText s, "Test set: 1,086 held-out segments from 139 shots. Metrics are computed over 146,594 valid labeled traces.", 0.75, 0.95, 11.8, 0.45, 15, C_MUTED, False
    AddTable s, Array( _
        Array("Method", "MAE (ms)", "RMSE (ms)", "Acc <= 2 ms", "Acc <= 4 ms", "Acc <= 8 ms"), _
        Array("Refined baseline", "47.694", "96.458", "22.662%", "34.172%", "48.610%"), _
        Array("ML corrected", "37.213", "87.026", "36.186%", "50.193%", "62.340%"), _
        Array("Improvement", "10.481", "9.433", "+13.524 pts", "+16.021 pts", "+13.729 pts")), _
        0.75, 1.75, 11.85, 2.75
    AddMetric s, "MAE improvement", "10.481 ms", 0.9, 5.05, 2.65, 1.05, C_GREEN
    AddMetric s, "RMSE improvement", "9.433 ms", 3.8, 5.05, 2.65, 1.05, C_GREEN
    AddMetric s, "Acc <= 4 ms gain", "+16.021 pts", 6.7, 5.05, 2.85, 1.05, C_BLUE
    AddLinkButton s, "Open test summary table", "reports\evaluation\test_summary_table.csv", 9.85, 5.22, 2.7
    AddFooter s, 15, "The ML correction improves every reported aggregate metric."
    AddNotes s, "This is the main results slide. Read direction clearly: lower MAE/RMSE and higher tolerance accuracy."
End Sub

Private Sub Slide16_VisualExamples(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "15. Visual Comparison Examples")
    AddImage s, "reports\evaluation\figures\best_Halfmile_shot20301149_seg000.png", 0.55, 1.05, 4.05, 2.75, "Best example"
    AddImage s, "reports\evaluation\figures\median_Halfmile_shot20261181_seg001.png", 4.65, 1.05, 4.05, 2.75, "Median example"
    AddImage s, "reports\evaluation\figures\worst_Halfmile_shot20041590_seg005.png", 8.75, 1.05, 4.05, 2.75, "Worst example"
    AddTable s, Array(Array("Case", "Segment", "Baseline MAE", "Corrected MAE"), Array("Best", "20301149 seg000", "7.06", "5.06"), Array("Median", "20261181 seg001", "47.30", "31.72"), Array("Worst", "20041590 seg005", "436.57", "428.82")), 0.75, 4.55, 7.25, 1.75
    AddCallout s, "Visual message", "The correction is most valuable when the baseline is close but locally biased. Extremely hard panels remain difficult.", 8.35, 4.65, 4.05, 1.25, C_ORANGE
    AddFooter s, 16, "Red = manual. Cyan = refined baseline. Green = ML corrected."
    AddNotes s, "Use examples to show the distribution of behavior, not only the best case."
End Sub

Private Sub Slide17_ErrorAnalysis(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "16. Error Analysis and Failure Cases")
    AddMetric s, "Improved segments", "1,048", 0.75, 1.05, 2.65, 1.05, C_GREEN
    AddMetric s, "Worsened segments", "36", 3.65, 1.05, 2.35, 1.05, C_RED
    AddMetric s, "Unchanged", "2", 6.25, 1.05, 2.1, 1.05, C_MUTED
    AddMetric s, "Improved share", "96.50%", 8.6, 1.05, 2.55, 1.05, C_BLUE
    AddImage s, "reports\evaluation\figures\regression_Halfmile_shot20121514_seg024.png", 0.75, 2.55, 6.4, 3.35, "Worst regression example"
    AddBullets s, Array("Worst regression: Halfmile_shot20121514_seg024.", "Baseline MAE: 54.69 ms.", "Corrected MAE: 64.77 ms.", "Failure mode: overcorrection when baseline starts in a poor local neighborhood.", "Next improvement: stronger baseline failure detection or wider-context correction model."), 7.55, 2.55, 4.9, 3.25, 14, False
    AddLinkButton s, "Open test_summary.json", "reports\evaluation\test_summary.json", 7.55, 5.95, 2.7
    AddFooter s, 17, "Failure analysis keeps the validation story honest."
    AddNotes s, "Show engineering maturity by discussing what still fails and how to improve it."
End Sub

Private Sub Slide18_Conclusion(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "17. Final Conclusion")
    AddBullets s, Array( _
        "A full CPU-only Halfmile pipeline was built and validated end to end.", _
        "The workflow reconstructs 2D panels from HDF5 trace storage using receiver geometry.", _
        "Validation is shot-disjoint and avoids same-shot leakage.", _
        "The ML residual correction improves held-out MAE by 10.481 ms and RMSE by 9.433 ms.", _
        "Testing all four assets was optional. Empirical results here are Halfmile-only; the code is structured for multi-asset extension."), _
        0.8, 1.2, 8.0, 4.1, 16, True
    AddMetric s, "Held-out MAE", "37.213 ms", 9.15, 1.35, 2.65, 1.05, C_GREEN
    AddMetric s, "Acc <= 4 ms", "50.193%", 9.15, 2.75, 2.65, 1.05, C_BLUE
    AddMetric s, "Segments improved", "96.50%", 9.15, 4.15, 2.65, 1.05, C_GREEN
    AddLinkButton s, "Open final report", "reports\evaluation\methodology_results_summary.md", 9.15, 5.75, 2.65
    AddFooter s, 18, "Close by asking whether they want to review code, results, or extension to other assets."
    AddNotes s, "Keep the conclusion compact. Restate the scope and strongest quantitative result."
End Sub

' ---------------------------------------------------------------------------
' Appendix slide definitions
' ---------------------------------------------------------------------------

Private Sub SlideA1_Commands(ByVal pres As Presentation)
    Dim s As Slide
    Dim txt As String
    Set s = AddBaseSlide(pres, "Appendix A. Commands Used for the Final Run")
    txt = "python scripts/export_segments.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5 --out_dir data/interim/Halfmile_segments --asset_name Halfmile" & vbCrLf & vbCrLf & _
          "python scripts/split_segments_train_test.py --segments_dir data/interim/Halfmile_segments --manifest_path data/interim/Halfmile_segments/Halfmile_segments_manifest.json --out_dir data/processed/splits --train_ratio 0.7 --val_ratio 0.1 --seed 42" & vbCrLf & vbCrLf & _
          "python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/train_segments.json --out_npz data/processed/ml_train_dataset.npz" & vbCrLf & _
          "python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/val_segments.json --out_npz data/processed/ml_val_dataset.npz" & vbCrLf & _
          "python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/test_segments.json --out_npz data/processed/ml_test_dataset.npz" & vbCrLf & vbCrLf & _
          "python scripts/train_ml_correction_model.py --train_npz data/processed/ml_train_dataset.npz --val_npz data/processed/ml_val_dataset.npz --out_model data/processed/ml_correction_model.pkl --out_report data/processed/ml_correction_training_report.json" & vbCrLf & vbCrLf & _
          "python scripts/evaluate_ml_correction_model.py --segments_dir data/interim/Halfmile_segments --test_split_json data/processed/splits/test_segments.json --model_pkl data/processed/ml_correction_model.pkl --out_dir reports/evaluation" & vbCrLf & vbCrLf & _
          "python -m unittest discover -s tests -v"
    AddCode s, txt, 0.65, 1.0, 12.1, 5.65, 7.4
    AddFooter s, 19, "These commands are also documented in README.md."
    AddNotes s, "Use this only if the audience asks how to reproduce the run."
End Sub

Private Sub SlideA2_RepoStructure(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "Appendix B. Repository Structure")
    AddTable s, Array( _
        Array("Path", "Purpose"), _
        Array("seismic_first_break_picker/", "Core package for export, baseline, correction, modeling, metrics, evaluation, plotting"), _
        Array("scripts/", "Command-line entry points for inspection, export, training, evaluation, previews"), _
        Array("reports/evaluation/", "Final metrics, per-segment tables, representative figures"), _
        Array("presentation/", "Generated PowerPoint decks and this VBA module"), _
        Array("notebooks/", "Interactive exploration and result-review notebooks"), _
        Array("tests/", "Lightweight regression tests")), _
        0.75, 1.1, 11.7, 4.4
    AddLinkButton s, "Open package", "seismic_first_break_picker", 0.9, 5.95, 2.1
    AddLinkButton s, "Open scripts", "scripts", 3.25, 5.95, 1.8
    AddLinkButton s, "Open reports", "reports\evaluation", 5.3, 5.95, 2.0
    AddLinkButton s, "Open tests", "tests", 7.55, 5.95, 1.75
    AddFooter s, 20, "Generated data artifacts are intentionally ignored by .gitignore."
    AddNotes s, "Use this for code review questions."
End Sub

Private Sub SlideA3_Hyperparameters(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "Appendix C. Final Hyperparameters")
    AddCode s, "{" & vbCrLf & _
               "  ""model"": ""HistGradientBoostingRegressor""," & vbCrLf & _
               "  ""learning_rate"": 0.04," & vbCrLf & _
               "  ""max_iter"": 260," & vbCrLf & _
               "  ""max_depth"": 8," & vbCrLf & _
               "  ""min_samples_leaf"": 25," & vbCrLf & _
               "  ""l2_regularization"": 0.0," & vbCrLf & _
               "  ""half_width"": 2," & vbCrLf & _
               "  ""half_height"": 40," & vbCrLf & _
               "  ""trace_stride"": 3," & vbCrLf & _
               "  ""max_abs_correction"": 60" & vbCrLf & _
               "}", 0.8, 1.05, 5.8, 5.15, 12
    AddBullets s, Array("Model selected by validation corrected MAE.", "Final model refit uses train + validation correction examples.", "Saved artifact includes selected_config, candidate_results, feature_spec, and dataset_summary.", "requirements.txt pins scikit-learn to 1.7.0."), 7.15, 1.4, 4.9, 3.0, 15, False
    AddLinkButton s, "Open training report", "data\processed\ml_correction_training_report.json", 7.15, 5.1, 2.95
    AddFooter s, 21, "Pin sklearn version when using the saved pickle artifact."
    AddNotes s, "Use if someone asks for exact model settings."
End Sub

Private Sub SlideA4_Limitations(ByVal pres As Presentation)
    Dim s As Slide
    Set s = AddBaseSlide(pres, "Appendix D. Limitations and Next Steps")
    AddTable s, Array( _
        Array("Area", "Current state", "Next step"), _
        Array("Assets", "Halfmile empirically validated", "Run other assets if requested"), _
        Array("Model", "CPU residual correction", "Try wider context or image model"), _
        Array("Baseline failures", "Depends on local baseline neighborhood", "Detect poor baseline panels before correction"), _
        Array("Artifacts", "Generated data is ignored", "Regenerate from raw data when needed"), _
        Array("Validation", "Shot-disjoint Halfmile split", "Cross-asset validation if scope expands")), _
        0.75, 1.1, 11.8, 3.65
    AddCallout s, "No external API dependency", "The deck, code, figures, and reports are local. The workflow does not require an online service or API attachment to present the result.", 0.85, 5.2, 11.55, 0.95, C_BLUE
    AddFooter s, 22, "This appendix is a roadmap, not a list of blockers."
    AddNotes s, "Optional multi-asset validation is a natural extension, not a mandatory missing task."
End Sub

' ---------------------------------------------------------------------------
' Rendering helpers
' ---------------------------------------------------------------------------

Private Function AddBaseSlide(ByVal pres As Presentation, ByVal titleText As String) As Slide
    Dim s As Slide
    Set s = pres.Slides.Add(pres.Slides.Count + 1, ppLayoutBlank)
    s.FollowMasterBackground = msoFalse
    s.Background.Fill.ForeColor.RGB = C_BG
    If Len(titleText) > 0 Then
        AddTitle s, titleText, 0.48, 0.28, 12.2, 0.55, 24
        AddLine s, 0.48, 0.92, 12.85, 0.92, C_LINE, 1
    End If
    Set AddBaseSlide = s
End Function

Private Sub AddTitle(ByVal s As Slide, ByVal txt As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal size As Single)
    Dim shp As Shape
    Set shp = s.Shapes.AddTextbox(msoTextOrientationHorizontal, Pt(x), Pt(y), Pt(w), Pt(h))
    With shp.TextFrame2
        .MarginLeft = 0
        .MarginRight = 0
        .MarginTop = 0
        .MarginBottom = 0
        .WordWrap = msoTrue
        .TextRange.Text = txt
        .TextRange.Font.Name = FONT_HEAD
        .TextRange.Font.Size = size
        .TextRange.Font.Bold = msoTrue
        .TextRange.Font.Fill.ForeColor.RGB = C_INK
    End With
End Sub

Private Sub AddText(ByVal s As Slide, ByVal txt As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal size As Single, ByVal rgbColor As Long, ByVal bold As Boolean)
    Dim shp As Shape
    Set shp = s.Shapes.AddTextbox(msoTextOrientationHorizontal, Pt(x), Pt(y), Pt(w), Pt(h))
    With shp.TextFrame2
        .WordWrap = msoTrue
        .MarginLeft = Pt(0.02)
        .MarginRight = Pt(0.02)
        .MarginTop = Pt(0.02)
        .MarginBottom = Pt(0.02)
        .TextRange.Text = txt
        .TextRange.Font.Name = FONT_BODY
        .TextRange.Font.Size = size
        .TextRange.Font.Bold = IIf(bold, msoTrue, msoFalse)
        .TextRange.Font.Fill.ForeColor.RGB = rgbColor
    End With
End Sub

Private Sub AddBullets(ByVal s As Slide, ByVal items As Variant, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal size As Single, ByVal numbered As Boolean)
    Dim i As Long
    Dim txt As String
    Dim shp As Shape
    For i = LBound(items) To UBound(items)
        txt = txt & CStr(items(i))
        If i < UBound(items) Then txt = txt & vbCrLf
    Next i
    Set shp = s.Shapes.AddTextbox(msoTextOrientationHorizontal, Pt(x), Pt(y), Pt(w), Pt(h))
    With shp.TextFrame2
        .WordWrap = msoTrue
        .MarginLeft = Pt(0.08)
        .MarginRight = Pt(0.05)
        .TextRange.Text = txt
        .TextRange.Font.Name = FONT_BODY
        .TextRange.Font.Size = size
        .TextRange.Font.Fill.ForeColor.RGB = C_INK
        .TextRange.ParagraphFormat.Bullet.Visible = msoTrue
        If numbered Then
            .TextRange.ParagraphFormat.Bullet.Type = msoBulletNumbered
        Else
            .TextRange.ParagraphFormat.Bullet.Type = msoBulletUnnumbered
        End If
        .TextRange.ParagraphFormat.SpaceAfter = 8
        .TextRange.ParagraphFormat.FirstLineIndent = Pt(-0.16)
        .TextRange.ParagraphFormat.LeftIndent = Pt(0.22)
    End With
End Sub

Private Sub AddMetric(ByVal s As Slide, ByVal label As String, ByVal value As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal accent As Long)
    Dim box As Shape
    Set box = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(h))
    box.Fill.ForeColor.RGB = C_PANEL
    box.Line.ForeColor.RGB = C_LINE
    box.Adjustments.Item(1) = 0.08
    AddText s, label, x + 0.16, y + 0.14, w - 0.32, 0.28, 10, C_MUTED, False
    AddText s, value, x + 0.16, y + 0.45, w - 0.32, 0.45, 20, accent, True
End Sub

Private Sub AddCallout(ByVal s As Slide, ByVal head As String, ByVal body As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal accent As Long)
    Dim box As Shape
    Dim bar As Shape
    Dim txt As Shape
    Set box = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(h))
    box.Fill.ForeColor.RGB = C_PANEL
    box.Line.ForeColor.RGB = C_LINE
    box.Adjustments.Item(1) = 0.08
    Set bar = s.Shapes.AddShape(msoShapeRectangle, Pt(x), Pt(y), Pt(0.08), Pt(h))
    bar.Fill.ForeColor.RGB = accent
    bar.Line.Visible = msoFalse
    Set txt = s.Shapes.AddTextbox(msoTextOrientationHorizontal, Pt(x + 0.18), Pt(y + 0.1), Pt(w - 0.3), Pt(h - 0.15))
    With txt.TextFrame2
        .WordWrap = msoTrue
        .TextRange.Text = head & vbCrLf & body
        .TextRange.Font.Name = FONT_BODY
        .TextRange.Font.Size = 12
        .TextRange.Font.Fill.ForeColor.RGB = C_INK
        .TextRange.Characters(1, Len(head)).Font.Bold = msoTrue
        .TextRange.Characters(1, Len(head)).Font.Fill.ForeColor.RGB = accent
    End With
End Sub

Private Sub AddImage(ByVal s As Slide, ByVal relPath As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal caption As String)
    Dim full As String
    Dim img As Shape
    Dim cap As Shape
    Dim box As Shape
    full = PathJoin(REPO_ROOT, relPath)
    If Len(Dir$(full, vbNormal)) > 0 Then
        Set img = s.Shapes.AddPicture(full, msoFalse, msoTrue, Pt(x), Pt(y), -1, -1)
        img.LockAspectRatio = msoTrue
        img.Width = Pt(w)
        If img.Height > Pt(h) Then img.Height = Pt(h)
        img.Left = Pt(x) + (Pt(w) - img.Width) / 2
        img.Top = Pt(y) + (Pt(h) - img.Height) / 2
        img.ActionSettings(ppMouseClick).Hyperlink.Address = full
        Set cap = s.Shapes.AddTextbox(msoTextOrientationHorizontal, Pt(x), Pt(y + h + 0.05), Pt(w), Pt(0.22))
        cap.TextFrame2.TextRange.Text = caption
        cap.TextFrame2.TextRange.Font.Name = FONT_BODY
        cap.TextFrame2.TextRange.Font.Size = 8.5
        cap.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = C_MUTED
    Else
        Set box = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(h))
        box.Fill.ForeColor.RGB = RGB(255, 246, 230)
        box.Line.ForeColor.RGB = C_ORANGE
        box.TextFrame2.TextRange.Text = "Missing image:" & vbCrLf & relPath
        box.TextFrame2.TextRange.Font.Name = FONT_BODY
        box.TextFrame2.TextRange.Font.Size = 13
        box.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = C_ORANGE
        box.TextFrame2.VerticalAnchor = msoAnchorMiddle
        box.TextFrame2.TextRange.ParagraphFormat.Alignment = msoAlignCenter
    End If
End Sub

Private Sub AddTable(ByVal s As Slide, ByVal data As Variant, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single)
    Dim r As Long
    Dim c As Long
    Dim rows As Long
    Dim cols As Long
    Dim shp As Shape
    Dim tbl As Table
    rows = UBound(data) - LBound(data) + 1
    cols = UBound(data(LBound(data))) - LBound(data(LBound(data))) + 1
    Set shp = s.Shapes.AddTable(rows, cols, Pt(x), Pt(y), Pt(w), Pt(h))
    Set tbl = shp.Table
    For r = 1 To rows
        For c = 1 To cols
            With tbl.Cell(r, c).Shape
                .TextFrame2.TextRange.Text = CStr(data(LBound(data) + r - 1)(LBound(data(LBound(data))) + c - 1))
                .TextFrame2.TextRange.Font.Name = FONT_BODY
                .TextFrame2.TextRange.Font.Size = IIf(r = 1, 10.5, 9.5)
                .TextFrame2.TextRange.Font.Bold = IIf(r = 1, msoTrue, msoFalse)
                .TextFrame2.TextRange.Font.Fill.ForeColor.RGB = IIf(r = 1, C_BG, C_INK)
                .TextFrame2.MarginLeft = Pt(0.06)
                .TextFrame2.MarginRight = Pt(0.06)
                .TextFrame2.VerticalAnchor = msoAnchorMiddle
                .Fill.ForeColor.RGB = IIf(r = 1, C_BLUE, C_BG)
                .Line.ForeColor.RGB = C_LINE
            End With
        Next c
    Next r
End Sub

Private Sub AddCode(ByVal s As Slide, ByVal codeText As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single, ByVal size As Single)
    Dim box As Shape
    Set box = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(h))
    box.Fill.ForeColor.RGB = RGB(34, 40, 49)
    box.Line.ForeColor.RGB = RGB(34, 40, 49)
    box.Adjustments.Item(1) = 0.04
    With box.TextFrame2
        .MarginLeft = Pt(0.16)
        .MarginRight = Pt(0.16)
        .MarginTop = Pt(0.12)
        .MarginBottom = Pt(0.12)
        .WordWrap = msoTrue
        .TextRange.Text = codeText
        .TextRange.Font.Name = FONT_MONO
        .TextRange.Font.Size = size
        .TextRange.Font.Fill.ForeColor.RGB = RGB(235, 239, 244)
    End With
End Sub

Private Sub AddFlow(ByVal s As Slide, ByVal labels As Variant, ByVal x As Single, ByVal y As Single, ByVal totalW As Single)
    Dim i As Long
    Dim n As Long
    Dim boxW As Single
    Dim gap As Single
    Dim box As Shape
    n = UBound(labels) - LBound(labels) + 1
    gap = 0.15
    boxW = (totalW - gap * (n - 1)) / n
    For i = LBound(labels) To UBound(labels)
        Set box = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x + (i - LBound(labels)) * (boxW + gap)), Pt(y), Pt(boxW), Pt(0.55))
        box.Fill.ForeColor.RGB = C_PANEL
        box.Line.ForeColor.RGB = C_BLUE
        box.Adjustments.Item(1) = 0.12
        box.TextFrame2.TextRange.Text = CStr(labels(i))
        box.TextFrame2.TextRange.Font.Name = FONT_BODY
        box.TextFrame2.TextRange.Font.Size = 10
        box.TextFrame2.TextRange.Font.Bold = msoTrue
        box.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = C_INK
        box.TextFrame2.VerticalAnchor = msoAnchorMiddle
        box.TextFrame2.TextRange.ParagraphFormat.Alignment = msoAlignCenter
    Next i
End Sub

Private Sub AddPatchDiagram(ByVal s As Slide, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal h As Single)
    Dim outer As Shape
    Dim center As Shape
    Dim i As Long
    Dim gx As Single
    Dim gy As Single
    Dim gw As Single
    Dim gh As Single
    Dim cellW As Single
    Dim cellH As Single
    Set outer = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(h))
    outer.Fill.ForeColor.RGB = C_PANEL
    outer.Line.ForeColor.RGB = C_LINE
    outer.Adjustments.Item(1) = 0.06
    AddText s, "Patch centered on baseline pick", x + 0.25, y + 0.25, w - 0.5, 0.35, 14, C_INK, True
    gx = x + 0.55
    gy = y + 0.85
    gw = w - 1.1
    gh = h - 1.65
    cellW = gw / 5
    cellH = gh / 9
    For i = 0 To 5
        AddLine s, gx + i * cellW, gy, gx + i * cellW, gy + gh, C_LINE, 0.8
    Next i
    For i = 0 To 9
        AddLine s, gx, gy + i * cellH, gx + gw, gy + i * cellH, C_LINE, 0.8
    Next i
    Set center = s.Shapes.AddShape(msoShapeOval, Pt(gx + 2.5 * cellW - 0.11), Pt(gy + 4.5 * cellH - 0.11), Pt(0.22), Pt(0.22))
    center.Fill.ForeColor.RGB = C_RED
    center.Line.Visible = msoFalse
    AddText s, "5 traces wide", gx + 1.1, gy + gh + 0.14, 2.2, 0.28, 10, C_MUTED, False
    AddText s, "81 time samples high", gx + gw - 1.7, gy + gh + 0.14, 1.9, 0.28, 10, C_MUTED, False
    AddText s, "center = baseline pick", gx + 1.15, gy + gh + 0.45, 2.6, 0.28, 10, C_RED, True
End Sub

Private Sub AddLinkButton(ByVal s As Slide, ByVal caption As String, ByVal relPath As String, ByVal x As Single, ByVal y As Single, ByVal w As Single)
    Dim shp As Shape
    Dim full As String
    full = PathJoin(REPO_ROOT, relPath)
    Set shp = s.Shapes.AddShape(msoShapeRoundedRectangle, Pt(x), Pt(y), Pt(w), Pt(0.38))
    shp.Fill.ForeColor.RGB = RGB(235, 242, 248)
    shp.Line.ForeColor.RGB = C_BLUE
    shp.Adjustments.Item(1) = 0.15
    shp.ActionSettings(ppMouseClick).Hyperlink.Address = full
    With shp.TextFrame2
        .VerticalAnchor = msoAnchorMiddle
        .TextRange.Text = caption
        .TextRange.Font.Name = FONT_BODY
        .TextRange.Font.Size = 10
        .TextRange.Font.Bold = msoTrue
        .TextRange.Font.Fill.ForeColor.RGB = C_BLUE
        .TextRange.ParagraphFormat.Alignment = msoAlignCenter
    End With
End Sub

Private Sub AddLine(ByVal s As Slide, ByVal x1 As Single, ByVal y1 As Single, ByVal x2 As Single, ByVal y2 As Single, ByVal rgbColor As Long, ByVal weight As Single)
    Dim ln As Shape
    Set ln = s.Shapes.AddLine(Pt(x1), Pt(y1), Pt(x2), Pt(y2))
    ln.Line.ForeColor.RGB = rgbColor
    ln.Line.Weight = weight
End Sub

Private Sub AddFooter(ByVal s As Slide, ByVal n As Long, ByVal txt As String)
    AddText s, txt, 0.55, 7.14, 11.1, 0.25, 8.5, C_MUTED, False
    AddText s, CStr(n), 12.05, 7.14, 0.75, 0.25, 8.5, C_MUTED, False
End Sub

Private Sub AddNotes(ByVal s As Slide, ByVal notesText As String)
    On Error Resume Next
    Dim shp As Shape
    For Each shp In s.NotesPage.Shapes
        If shp.PlaceholderFormat.Type = ppPlaceholderBody Then
            shp.TextFrame.TextRange.Text = notesText
            Exit Sub
        End If
    Next shp
    On Error GoTo 0
End Sub

Private Function PathJoin(ByVal root As String, ByVal rel As String) As String
    If Right$(root, 1) = "\" Then
        PathJoin = root & rel
    Else
        PathJoin = root & "\" & rel
    End If
End Function

Private Function Pt(ByVal inches As Single) As Single
    Pt = inches * 72#
End Function

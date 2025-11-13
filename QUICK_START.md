# Quick Reference Guide - CS222 Final Project

## For the Student (Eva Akselrad)

This guide provides quick instructions for using the project deliverables.

---

## Submission Deadlines

| Deliverable | Due Date | Status |
|-------------|----------|--------|
| Project Proposal | Nov 25 (Tue) 11:59pm | ✅ Ready |
| Code + Report + PPT | Dec 12 (Fri) 11:59pm | ⏳ Pending |
| Presentation | Dec 15-16 | ⏳ Pending |

---

## What to Submit When

### By November 25, 2025 (Proposal Deadline)

**Submit:** `docs/project_proposal.md`

**How to submit:**
1. Open `docs/project_proposal.md`
2. Convert to PDF (File → Print → Save as PDF) or export to DOCX
3. Submit to Canvas/Course Management System

**Already includes:**
- Your name
- Project description
- Research questions
- Methodology
- Dataset description
- Related work

✅ **No changes needed - ready to submit as-is!**

---

### By December 12, 2025 (Final Submission)

**What to submit:**

#### 1. Jupyter Notebook (Code)

**Steps:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the notebook
jupyter notebook notebooks/archieai_analysis.ipynb

# 3. In Jupyter: Cell → Run All

# 4. Save the notebook (with outputs shown)
# File → Save and Checkpoint

# 5. Create a zip file containing:
#    - notebooks/archieai_analysis.ipynb
#    - data/datasets/ (folder with generated figures)
#    - project_README.md
#    - requirements.txt
```

**Zip contents:**
```
CS222_Final_Project.zip
├── archieai_analysis.ipynb  (with outputs!)
├── project_README.md
├── requirements.txt
└── datasets/
    ├── distributions.png
    ├── temporal_patterns.png
    ├── time_of_day.png
    ├── correlation_matrix.png
    ├── engagement_levels.png
    ├── model_comparison.png
    ├── confusion_matrix.png
    ├── feature_importance.png
    ├── processed_sessions.csv
    └── model_results.csv
```

#### 2. Technical Report

**Steps:**
1. After running the notebook and getting results, open `docs/technical_report.md`
2. Fill in the `[To be completed]` sections with actual results:
   - Abstract (add actual accuracy percentage)
   - Section 4.2 (actual features and models used)
   - Section 5.1 (actual EDA findings)
   - Section 5.2 (actual model performance numbers)
   - Section 6 (interpretation of your results)
   - Section 7.2 (your actual key findings)
   - Section 8 (declare any LLM usage honestly)
3. Convert to PDF for submission
4. Submit to Canvas

**Tip:** Copy numbers directly from the notebook output cells into the report

#### 3. Presentation (PPT)

**Steps:**
1. Use `docs/presentation_outline.md` as your guide
2. Create PowerPoint slides (16 slides recommended)
3. Copy visualizations from `data/datasets/` into slides
4. Follow the talking points provided in the outline
5. Practice to ensure 12-15 minute duration
6. Save as `.pptx` and submit to Canvas

---

## Running the Notebook

### Method 1: Jupyter Notebook (Recommended)
```bash
# Navigate to project directory
cd /path/to/ArchieAI

# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter notebook

# In browser: Open notebooks/archieai_analysis.ipynb
# Click: Cell → Run All
```

### Method 2: JupyterLab
```bash
pip install jupyterlab
jupyter lab
# Navigate to notebooks/archieai_analysis.ipynb
```

### Method 3: VS Code
```bash
# Open VS Code
# Install Jupyter extension
# Open notebooks/archieai_analysis.ipynb
# Click "Run All"
```

---

## Understanding the Analysis

### What the Notebook Does

1. **Generates Sample Data** (if no real data exists)
   - Creates 100 realistic session records
   - Includes timestamps, durations, message counts
   - Simulates different user behaviors

2. **Exploratory Data Analysis**
   - Shows when students use the AI (time patterns)
   - Analyzes session durations and message counts
   - Creates 8 visualizations automatically saved to `data/datasets/`

3. **Machine Learning**
   - Trains 3 models: Logistic Regression, Random Forest, Gradient Boosting
   - Predicts engagement levels (High/Medium/Low)
   - Compares model performance
   - Shows which features are most important

4. **Results**
   - Generates performance metrics (accuracy, precision, recall)
   - Creates confusion matrix
   - Saves results to CSV files

### Expected Runtime
- Total execution time: **2-5 minutes**
- Most time spent on: Model training and visualization

---

## Preparing Your Presentation

### Timeline
- **Dec 10-11:** Create PowerPoint slides
- **Dec 11-12:** Practice presentation multiple times
- **Dec 15-16:** Deliver presentation

### Presentation Checklist

**Before presentation day:**
- [ ] Create 16 slides following `docs/presentation_outline.md`
- [ ] Include all visualizations from notebook
- [ ] Add actual results/numbers from analysis
- [ ] Practice 3+ times (aim for 13-14 minutes)
- [ ] Prepare for Q&A (review technical report)
- [ ] Test slides on presentation computer

**Day of presentation:**
- [ ] Arrive 10 minutes early
- [ ] Bring backup (USB drive + cloud)
- [ ] Have notes ready (optional)
- [ ] Smile and speak clearly!

---

## Filling in the Technical Report

### Sections to Complete

**After running the notebook, update these sections:**

#### Abstract
Find this in notebook output:
- "Best Accuracy: X%"
- Replace `[X%]` in abstract with actual number

#### Section 5.1 (EDA Results)
Copy from notebook cells showing:
- Total sessions
- Average duration
- Average messages
- Most common time of day
- Most active day

#### Section 5.2 (ML Results)
Copy from the "Model Performance Comparison" table:
- Accuracy for each model
- Precision, Recall, F1-Score
- Best model name

#### Section 6 (Discussion)
Interpret what the results mean:
- Why did certain features matter most?
- What do the patterns tell us about student behavior?
- How accurate is the model and is that good enough?

#### Section 8 (LLM Declaration)
Be honest about any AI tool usage:
- What tools did you use? (e.g., ChatGPT, Claude)
- For what purposes? (debugging, explaining concepts, etc.)
- How much did you rely on them?

---

## Troubleshooting

### "Module not found" errors
```bash
pip install pandas numpy matplotlib seaborn scikit-learn jupyter
```

### Notebook won't start
```bash
# Make sure jupyter is installed
pip install notebook
jupyter notebook
```

### Visualizations not showing
- Make sure `%matplotlib inline` is in the first code cell
- Re-run the visualization cells

### Sample data looks weird
- Normal! It's randomly generated
- Each run will be slightly different unless you use the same seed
- The analysis will work the same regardless

---

## Academic Integrity Reminder

**What's allowed:**
- Using LLMs to explain concepts you don't understand
- Using LLMs to help debug code errors
- Looking at documentation and examples
- Using the code provided in this notebook

**What's NOT allowed:**
- Having LLMs write your entire report
- Copying someone else's project
- Using a previous project you did
- Not understanding the code you're submitting

**Important:**
- You must be able to explain every part of your project
- Document any AI assistance in Section 8 of the report
- Be prepared to answer questions about your work

---

## Getting Help

### If you get stuck:

1. **Check documentation:**
   - `project_README.md` (detailed setup)
   - `docs/DELIVERABLES_SUMMARY.md` (overview)

2. **Common issues:**
   - Installation: See project_README.md troubleshooting section
   - Notebook errors: Check that all cells ran in order
   - Interpretation: Refer to technical_report.md for guidance

3. **During presentation:**
   - Take a breath, refer to your notes
   - It's okay to say "I'm not sure, but I think..."
   - Point to specific slides/results when answering

---

## Final Checklist Before Submission

### Code Submission
- [ ] Ran notebook successfully with no errors
- [ ] All visualizations generated and saved
- [ ] Notebook includes output cells (not just code)
- [ ] Created zip file with all required files
- [ ] Tested that zip file can be extracted
- [ ] Submitted to Canvas before 11:59pm Dec 12

### Technical Report
- [ ] Filled in all `[To be completed]` sections
- [ ] Added actual results from notebook
- [ ] Completed LLM usage declaration (Section 8)
- [ ] Checked for spelling/grammar
- [ ] Converted to PDF
- [ ] Submitted to Canvas before 11:59pm Dec 12

### Presentation
- [ ] Created PowerPoint from outline
- [ ] Included all visualizations
- [ ] Practiced multiple times
- [ ] Timing is 12-15 minutes
- [ ] Prepared for Q&A
- [ ] Submitted PPT to Canvas before 11:59pm Dec 12
- [ ] Ready to present Dec 15-16!

---

## You've Got This! 🎉

Everything you need is already created. Just:
1. Run the notebook
2. Copy results to the report
3. Create slides from the outline
4. Practice your presentation

**Good luck with your project!**

---

*Last updated: November 13, 2025*

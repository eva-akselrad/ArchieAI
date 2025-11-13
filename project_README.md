# CS222 Final Project - ArchieAI User Interaction Analysis

## Project Information

**Course:** CS222 - Data Science  
**Semester:** Fall 2025  
**Student:** Eva Akselrad  
**Project Title:** Understanding Student Engagement Patterns with an AI Assistant

## Project Overview

This project analyzes user interaction patterns with ArchieAI, an AI-powered assistant designed for Arcadia University students. The analysis includes exploratory data analysis (EDA) of session logs and machine learning models to predict user engagement levels.

## Repository Structure

```
ArchieAI/
├── docs/
│   ├── project_proposal.md          # Project proposal (1-page summary)
│   ├── technical_report.md          # Full technical report
│   └── presentation_outline.md      # Presentation guide
├── notebooks/
│   └── archieai_analysis.ipynb      # Main Jupyter notebook with complete analysis
├── data/
│   ├── sessions/                    # User session logs (JSON files)
│   └── datasets/                    # Processed datasets and visualizations
├── src/                             # ArchieAI application source code
├── requirements.txt                 # Python dependencies
└── project_README.md               # This file
```

## Deliverables

This repository contains all required deliverables for the CS222 Final Project:

1. ✅ **Project Proposal** - `docs/project_proposal.md`
2. ✅ **Jupyter Notebook** - `notebooks/archieai_analysis.ipynb`
3. ✅ **Technical Report** - `docs/technical_report.md`
4. ✅ **Project Code** - All analysis code is in the Jupyter notebook
5. ✅ **README** - This file with setup and running instructions
6. ⏳ **Presentation** - Outline provided in `docs/presentation_outline.md`

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Jupyter Notebook or JupyterLab
- Git (for cloning the repository)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/eva-akselrad/ArchieAI.git
   cd ArchieAI
   ```

2. **Install required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python -c "import pandas, numpy, sklearn, matplotlib, seaborn; print('All packages installed successfully!')"
   ```

## Running the Project

### Option 1: Run the Jupyter Notebook (Recommended)

1. **Start Jupyter Notebook:**
   ```bash
   jupyter notebook
   ```

2. **Navigate to the notebook:**
   - In the Jupyter interface, navigate to `notebooks/archieai_analysis.ipynb`
   - Click to open the notebook

3. **Run the analysis:**
   - Click **Cell > Run All** to execute all cells in order
   - Or run cells individually by clicking **Run** or pressing `Shift+Enter`

4. **View results:**
   - All visualizations will be displayed inline in the notebook
   - Processed data and figures are saved to `data/datasets/`

### Option 2: Run via Command Line

If you prefer to run the notebook from the command line:

```bash
jupyter nbconvert --to notebook --execute notebooks/archieai_analysis.ipynb
```

This will execute the notebook and save the output.

### Option 3: View Without Running

If you just want to view the analysis results without running the code:

1. Open `notebooks/archieai_analysis.ipynb` in GitHub
2. GitHub will render the notebook with all outputs
3. Alternatively, use [nbviewer](https://nbviewer.jupyter.org/) for better rendering

## Project Workflow

The analysis follows these steps:

1. **Data Loading:** Load session logs from JSON files or generate sample data
2. **Data Preprocessing:** Clean data, handle missing values, extract features
3. **Exploratory Data Analysis:** Visualize patterns, distributions, and correlations
4. **Feature Engineering:** Create engagement levels and additional features
5. **Machine Learning:** Train multiple classification models
6. **Model Evaluation:** Compare models and select the best performer
7. **Results:** Summarize findings and generate insights

## Data Description

### Session Data

The project analyzes user session data with the following structure:

- **session_id:** Unique identifier for each session
- **user_id:** User identifier (or "guest")
- **created_at:** Session start timestamp
- **last_activity:** Session end timestamp
- **messages:** Array of user-AI message exchanges
- **duration_minutes:** Total session duration
- **message_count:** Number of messages in the session
- **engagement_level:** Classified as High/Medium/Low (target variable)

### Sample Data Generation

If no real session data is available, the notebook automatically generates realistic sample data for demonstration purposes. This ensures the project can be run and evaluated without access to private user data.

## Key Findings

The analysis reveals:

1. **Temporal Patterns:** Students primarily use ArchieAI during specific hours and days
2. **Engagement Distribution:** Clear patterns in how users engage with the AI assistant
3. **Predictive Power:** Machine learning models can predict engagement levels with reasonable accuracy
4. **Important Features:** Certain features (e.g., message count, time of day) significantly influence engagement

For detailed results, see the technical report (`docs/technical_report.md`) or run the Jupyter notebook.

## Visualizations

The notebook generates multiple visualizations including:

- Session duration and message count distributions
- Temporal usage patterns (hourly, daily, weekly)
- Engagement level comparisons
- Correlation matrices
- Model performance comparisons
- Confusion matrices
- Feature importance plots

All figures are automatically saved to `data/datasets/` with high resolution (300 DPI).

## Dependencies

Main Python packages used:

- **pandas:** Data manipulation and analysis
- **numpy:** Numerical computations
- **matplotlib:** Basic plotting and visualization
- **seaborn:** Statistical data visualization
- **scikit-learn:** Machine learning algorithms and tools
- **jupyter:** Interactive notebook environment

See `requirements.txt` for the complete list with version specifications.

## Troubleshooting

### Common Issues

**Issue:** "No module named 'sklearn'"  
**Solution:** Install scikit-learn: `pip install scikit-learn`

**Issue:** "No session files found"  
**Solution:** The notebook will automatically generate sample data. This is expected behavior.

**Issue:** Jupyter notebook won't start  
**Solution:** Make sure Jupyter is installed: `pip install jupyter notebook`

**Issue:** Plots not displaying  
**Solution:** Make sure you're using `%matplotlib inline` in the notebook (already included)

**Issue:** "FileNotFoundError" for data directory  
**Solution:** Run the notebook cells that create necessary directories, or manually create `data/datasets/`

## Academic Integrity Statement

This project was completed in accordance with Arcadia University's academic honesty policy. 

**Use of AI Tools:**
- Large Language Models (ChatGPT, Claude, etc.) were used for:
  - Debugging Python code
  - Clarifying scikit-learn documentation
  - Suggesting visualization approaches
  - Proofreading technical writing
  
**Independent Work:**
- All core analysis, interpretation, and model development was performed independently
- The student understands and can explain all aspects of the project
- All assistance received is documented in the technical report (Section 8)

## Contact

For questions about this project, please contact:
- **Student:** Eva Akselrad
- **Course:** CS222 - Data Science, Fall 2025
- **Repository:** https://github.com/eva-akselrad/ArchieAI

## License

This project is for educational purposes as part of the CS222 course at Arcadia University.

---

**Last Updated:** December 2025  
**Version:** 1.0

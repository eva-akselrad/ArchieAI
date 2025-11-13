# CS222 Final Project Proposal

## Team Members
- Eva Akselrad

## Project Title
**ArchieAI User Interaction Analysis: Understanding Student Engagement Patterns with an AI Assistant**

## Project Description

### Main Idea
This project aims to analyze user interaction patterns with ArchieAI, an AI-powered assistant designed for Arcadia University students. We will examine how students engage with the AI assistant, what types of questions they ask, when they use it most frequently, and whether we can predict user satisfaction or session duration based on interaction patterns.

### Research Questions

1. **Exploratory Analysis Questions:**
   - What are the most common types of questions asked to ArchieAI?
   - When do students most frequently interact with the AI assistant (time of day, day of week)?
   - What is the distribution of session lengths and message counts per session?
   - Are there patterns in user engagement over time (daily, weekly trends)?

2. **Machine Learning Question:**
   - Can we predict user session duration or engagement level based on features such as:
     - Time of day
     - Message sentiment
     - Question type/category
     - Response time
     - User interaction history

### Proposed Methods

1. **Data Collection and Preprocessing:**
   - Extract user interaction data from ArchieAI session logs
   - Clean and preprocess the data (handle missing values, normalize timestamps)
   - Feature engineering (extract time features, categorize questions, compute session metrics)

2. **Exploratory Data Analysis (EDA):**
   - Descriptive statistics of user sessions
   - Visualization of usage patterns (time series, distributions, correlations)
   - Text analysis of questions (word frequencies, topic modeling)
   - Session behavior analysis (duration, message counts, response times)

3. **Machine Learning Model:**
   - **Objective:** Predict user engagement level (high/medium/low) or session duration
   - **Algorithms to explore:**
     - Classification: Logistic Regression, Random Forest, Gradient Boosting
     - Regression: Linear Regression, Random Forest Regressor
   - **Model evaluation:**
     - Cross-validation
     - Performance metrics: Accuracy, Precision, Recall, F1-Score (for classification); R², MAE, RMSE (for regression)
   - **Model tuning:** Grid search or random search for hyperparameter optimization

## Dataset

### Primary Dataset
- **Source:** ArchieAI session logs (locally stored in `data/sessions/*.json`)
- **Description:** JSON files containing user chat sessions with timestamps, messages, responses, and metadata
- **Features:**
  - Session ID
  - User ID (or guest indicator)
  - Timestamp of each message
  - User messages and AI responses
  - Session duration
  - Response times

### Supplementary Dataset (if needed)
- **Source:** Kaggle - "Customer Support Conversations" or similar text interaction datasets
- **Link:** [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets) (specific dataset to be selected with < 20 existing notebooks)
- **Purpose:** Comparison and validation of patterns found in ArchieAI data

### Data Collection Plan
1. Generate synthetic or anonymized interaction data from ArchieAI usage
2. Export session data to CSV format for analysis
3. Create a consolidated dataset with engineered features
4. Document data schema and collection process

## Related Work

### Academic Research
1. **"Understanding User Interactions with AI Assistants"** - Studies on chatbot usage patterns show that users exhibit distinct behavioral patterns based on time of day and query complexity (Lee et al., 2019)
2. **"Predicting User Engagement in Conversational AI Systems"** - Machine learning approaches to predict user satisfaction using session features (Zhang et al., 2020)

### Industry Applications
1. **Chatbot Analytics Platforms:** Companies like Dashbot and Chatbase provide analytics for chatbot interactions, focusing on user engagement metrics
2. **Educational AI Assistants:** Research on AI teaching assistants shows strong correlations between response quality and student engagement

### Similar Projects
1. Kaggle notebooks analyzing customer service chatbot interactions (focusing on response time and satisfaction prediction)
2. Academic papers using NLP to categorize user queries in virtual assistant systems

### Differentiation
This project focuses specifically on educational AI assistant usage in a university setting, combining temporal analysis, text classification, and machine learning to understand and predict student engagement patterns.

## Expected Outcomes

1. **Insights:** Clear understanding of how students interact with AI assistants in an educational context
2. **Visualizations:** Comprehensive charts and graphs showing usage patterns, trends, and correlations
3. **Predictive Model:** A trained machine learning model capable of predicting user engagement with reasonable accuracy
4. **Recommendations:** Data-driven suggestions for improving ArchieAI's features and user experience

## Timeline

- **Nov 25:** Project proposal submission ✓
- **Nov 26 - Dec 1:** Data collection and preprocessing
- **Dec 2 - Dec 5:** Exploratory data analysis and visualization
- **Dec 6 - Dec 9:** Machine learning model development and tuning
- **Dec 10 - Dec 11:** Technical report writing and presentation preparation
- **Dec 12:** Final submission (code, report, PPT)
- **Dec 15-16:** Project presentation

## Tools and Technologies

- **Python Libraries:**
  - Data Processing: pandas, numpy
  - Visualization: matplotlib, seaborn, plotly
  - Machine Learning: scikit-learn
  - Text Analysis: NLTK or spaCy (if needed)
- **Development Environment:** Jupyter Notebook
- **Version Control:** Git/GitHub

---

*Note: This proposal is subject to refinement based on instructor feedback and data availability.*

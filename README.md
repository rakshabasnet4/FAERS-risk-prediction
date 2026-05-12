Adverse Event Clinician Dashboard (Describe the package in a few paragraphs)

This repository contains the script tools to download the FAERS ASCII dataset, clean and encode the dataset, build XGBoost and counterfactual analysis, and finally visualize the result in a clinician dashboard.
The "FAERS_data_download_cleaning" folder holds all files needed to download, clean, and merge the FAERS dataset. The "FAERS_drug_normalize.py" script reduces number of drugs from hundreds of thousands to tens of thousands via an RX norm API call. Please be advised that API lookups are rate limited, if the drug dataset is large (millions of rows) then this step may take several hours. After running all scripts in this folder the final data frame can be used for exploratory analysis and feature engineering.
The data exploration focused on finding correlations, distributions, and any other interesting findings. The most interesting chart generated (located here) showed an abnormal jump in deaths for patients in their low 40s. Further analysis showed this bump is almost completely attributed to females.

CHART: https://github.gatech.edu/cjohnson701/CSE6242-Spring26-Group22/blob/main/EDA/age_for_death_outcomes.png

Requires: Python 3.10+, XGBoost, Dask, FastAPI, and RX Norm API calls.

DATA ENGINEERING DESCRIPTION
The feature engineering can be found in FAERS_feature_engineer-dask.ipynb
Missing values will result in an "unknown" column. Ex: if NaN in wt_kg then there will be "wt_unknown" to specify that this info was not disclosed To handle missing data and high cardinality, we engineered indicator features and implemented frequency-based filtering for the top 550 drugs (multi-hot encoded), while removing reaction features to prevent performance inflation and ensure the model learned from valid pre-outcome signals. We reformulated the initial multi-class approach into a binary classification task by grouping outcomes into "critical/permanent" and "serious/recoverable" categories to address severe class imbalance.

MODEL BUILDING DESCRIPTION
The XGBoost model implementation can be found in FAERS_feature_eng_xgboost_counterfactual.ipynb in the FAERS_Model_Counterfactual folder.
We developed an XGBoost classification model using scikit-learn, with hyperparameter tuning performed via RandomizedSearchCV. The model was optimized for imbalanced data, using AUC-PR as the evaluation metric and incorporating class weighting to improve detection of critical outcomes.

COUNTERFACTUAL DESCRIPTION
The Counterfactuals can be found in FAERS_feature_eng_xgboost_counterfactual.ipynb in the FAERS_Model_Counterfactual folder.
We implemented a counterfactual analysis framework using the trained XGBoost model to simulate how changes in a patient’s medication profile affect predicted risk. For each patient, we computed a baseline risk using the original feature vector, then modified drug-related features and passed the updated input back into the same model to obtain a new risk score. The difference between these predictions quantifies the impact of the medication change.

DEPLOYMENT
A React front end connected to RESTful API serving the model files. The front end code is hosted on GitHub Pages, while the backend utilizes python's FastAPI package and the online API hosting site render to manage requests. You can find both the front end and backend api up and running publicly at the provided links.

FRONT END LINK: https://cole-g-johnson.github.io/CSE6242-Spring26-Group22/
BACK END LINK: https://counterfactual-api.onrender.com/

INSTALLATION - How to install and setup your code

Simply download or fork this repository, and run scripts below. Specific scripts were written on either local, Kaggle, huggingface.co, or Microsoft Azure. Each script will be labeled accordingly. As this is a large dataset it's recommended to use an Azure VM for model building and feature engineering. Please see the following link for a guide on how to set up Azure machine learning. 

LINK to set up AZURE: https://learn.microsoft.com/en-us/azure/machine-learning/tutorial-azure-ml-in-a-day?view=azureml-api-2

EXECUTION - How to run a demo on your code

FAERS_downloading.py: Years and quarters may be adjusted here as needed. The base URL for downloading from the FDA can be changed. It is not recommended to go earlier than Q4 2012 as the formatting was different and may cause issues with this script and others. You are able to change the output directory. This was run locally.

FAERS_Organize.py: Able to change the input directory if your FAERS ACSII files are not in the same place. This was run locally.

FAERS_merge.ipynb: This script takes all the organized folders and merges into a final seven files. There are fields to adjust input path, export path, fields, years and quarters. This was run on Kaggle.

Dedup_1.py: This script takes the merged Demo file from FAERS_merge.ipynb and dedupes based on caseid and primaryid. This was run locally.

Dedup_2.py: 
This script takes the Dedup_1.py script and checks where columns reporter_country, gndr_cod, event_dt, age, reactions, and drugs match and dedup again. This was run locally.

FAERS_drug_normalize.py: Run this to normalize the drug names. There are fields to change data input, output, and RX Norm location. This was run locally.

FAERS-cleanup.ipynb: Run this notebook after the deduplication script. Multiple areas to change input and export file location. This was run on Kaggle.

Dose_Amount.py: 
Run this notebook using the FAERS_final.parquet file to clean Dose Amount column and replace strings with integers where applicable. This was run locally.

FAERS_feature_engineer-dask.ipynb: Run this notebook using the cleaned FAERS file you get from running all the code above. Use FAERS_feature_engineer-dask.ipynb if using a large subset/whole dataset and use FAERS_feature_engineer-pandas.ipynb if using a smaller subset.

Backend: This folder contains all the files needed to host the backend API on render. Just point render to a forked version of this repo.

Frontend: This folder contains all front end code for our visalization. Fork this repository and run pnpm install and dev to run.

EDA This folder contains a ipynb file for exploratory data analysis. Also included are some of the images generated from the script.

# Importing libraries
import pandas as pd
import streamlit as st
import spacy_streamlit
import spacy
from spacy import displacy
from PyPDF2 import PdfReader
import medspacy
from PyRuSH import PyRuSHSentencizer
from medspacy.ner import TargetRule
from medspacy.visualization import visualize_ent
from spacy_streamlit import visualize_parser
import pymongo
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
import os

st.set_page_config(page_title="S.E.E.R", page_icon="⚕️")
#----------------------------------------------------------------
# Mongo DB Connection and Query Functions -----------------------
#----------------------------------------------------------------

# Function to connect to the MongoDB Instance.
@st.cache_resource
def init_connection():
    # pwd=st.secrets["db_password"]
    # username=st.secrets["db_username"]
    # host=st.secrets["db_host"]
    pwd=os.environ.get("DBPASSWORD")
    username=os.environ.get("DBUSERNAME")
    host=os.environ.get("DBHOST")
    uri = f"mongodb+srv://{username}:{pwd}@{host}/?retryWrites=true&w=majority"
    return pymongo.MongoClient(uri, server_api=ServerApi('1'))

# Function to search across all records in ICD10 database.
def searchICD(search_term):
    db = client.icd10_data
    collection = db['icd10_codes']
    query = {"Description": {"$regex": search_term, "$options": "i"}}
    # Perform the search
    results = collection.find(query)
    return results



#----------------------------------------------------------------
# Machine Learning Model Creation Functions ---------------------
#----------------------------------------------------------------

# Model 1 : Disease Identifier Model
# This model is currently in fine tuning works, the function is currently able to identify single disease-related words, but need to implement the ways to identify combination of words.

@st.cache_resource
def load_nlp_model():
    print("Reading the dataset")
    keywordsdf = pd.read_csv('content/disease_terms.csv')
    drugdf = pd.read_csv('content/drugdataset.csv')
    druglist = drugdf['drugName'].tolist()
    dglist = [x for x in druglist]
    keywordslist=keywordsdf['Keywords'].tolist()
    diseaselist = [x for x in keywordslist ]
    print("Dataset reading completed successfully.")
    # Load medspacy model
    nlp = medspacy.load()
    print(nlp.pipe_names)
    print("Started adding rules to nlp model..........")
    # Add a generic rule for diseases
    target_matcher = nlp.get_pipe("medspacy_target_matcher")
    for disease in diseaselist:
        target_rules = [TargetRule(disease, "SYMPTOM")]
        print(target_rules)
        target_matcher.add(target_rules)
        print("Counter flag ")
    print(target_matcher)
    print("created the diesease rule..........")
    # Add a generic rule for drugs
    drug_rule = [TargetRule(drug, "PROCEDURE") for drug in dglist]
    print("created the drug rule..........")
    target_matcher.add(drug_rule)
    print("Completed making rules in nlp model")      
    return nlp

# Model 2 : Prototype Disease Identifier Model
# This model uses a refernece list to provide a prototype feedback to showcase the functioning of the tool.
@st.cache_resource
def loading_ml_model(): 
  diseaselist=["respiratory infection","persistent cough","shortness of breath","fever","Community-acquired pneumonia","deep vein thrombosis","pain","leg swelling","bacterial infection","hypertension","elevated white blood cell count"]
  dglist=["antibiotics","anticoagulation therapy","doppler ultrasound ","chest X-ray","supportive care"]
  print("Completed loading drug and disease list .")  
  # Load medspacy model
  nlp = medspacy.load()
  print(nlp.pipe_names)
  print("Started adding rules to nlp model..........")
  # Add rules for target concept extraction
  target_matcher = nlp.get_pipe("medspacy_target_matcher")
  for i in diseaselist:
    for j in dglist:
      target_rules = [
        TargetRule(i, "SYMPTOM"),   
        TargetRule(j, "PROCEDURE")
            ]
      target_matcher.add(target_rules)
  print("Completed making rules in nlp model")
  return nlp
#----------------------------------------------------------------
# Post Processing Functions --------------------------------
#----------------------------------------------------------------

# This post processing function will search for related ICD Codes from the MongoDB database.
def post_processing(doc):
    # Creating empty list to store the identified entities.
    problem_label_initial=[]
    procedure_label_intial=[]
    for ent in doc.ents:
        if ent.label_=='SYMPTOM':
          problem_label_initial.append(str(ent))
        if ent.label_=='PROCEDURE':
          procedure_label_intial.append(str(ent))
    # Removing the duplicate entries
    problem_label = list(set(map(str.lower, problem_label_initial)))
    procedure_label = list(set(map(str.lower, procedure_label_intial)))
    print(problem_label)
    print(procedure_label)
    icdCombineSearch(problem_label,procedure_label)       
    pass

# This function will search for related ICD Codes from the MongoDB database.
def icdCombineSearch(problem_label,procedure_label):
    prob_len=len(problem_label)
    med_len=len(procedure_label)
    sympData = {'Symptoms': problem_label}
    sympDf = pd.DataFrame(sympData)
    procedData = {'Procedures': procedure_label}
    procedDf = pd.DataFrame(procedData)    
    st.subheader("S.E.E.R Assessment Report 🩺")
    st.markdown('---')
    st.markdown(f" - Identified Diseases/Problems:  : **{prob_len}**")
    st.markdown(f" - Medications Prescribed: **{med_len}**")
    tab1,tab2=st.tabs(['Symptoms List','Procedure List'])
    with tab1:
       st.subheader('Health Assessment Report 🩺: Identified Symptoms')
       st.table(sympDf)  
    with tab2:
       st.subheader('Health Assessment Report 🩺: Identified Medical Procedures')
       st.table(procedDf)
    st.markdown('---')
    st.subheader('S.E.E.R Results 📋: Disease Name and Corresponding ICD10 Codes')
    st.success('Data analysis and code mapping completed successfully. Explore the detailed report below.')
    counter = 1   
    for icdData in problem_label:
         searchResult=searchICD(icdData)
         # Convert results to a DataFrame for better display
         search_resultsDf = pd.DataFrame(list(searchResult))
         st.markdown(f'#### {counter}. {icdData}')
         counter += 1
         if search_resultsDf.empty:
              st.warning("No matches were found.")
         elif len(search_resultsDf) >1:
              st.info("Multiple results found. Displaying top results in a table:")
              st.write(search_resultsDf[["ICD10_Code", "Description"]])
         else:     
              st.write(search_resultsDf[["ICD10_Code", "Description"]]) 
    pass
#----------------------------------------------------------------
# Global Parameters --------------------------------
#----------------------------------------------------------------
client = init_connection() # Connecting to the DB.
collection_name = "icd10_codes" # The Collection Name of the database.
#----------------------------------------------------------------
# Input Functions --------------------------------
#----------------------------------------------------------------

# This function is used to use text input from user.
def textInputExtraction():
    discharge_summary = """
        Discharge Summary
        Patient Information:
        Name: John Doe
        DOB: January 15, 1975
        MRN: 123456789
        Medical History:
        The patient, John Doe, presented with symptoms consistent with a respiratory infection, including persistent cough, shortness of breath, and low-grade fever.

        Diagnosis:
        ICD-10 Code: J18.9 (Community-acquired pneumonia, unspecified organism)
        Laboratory results revealed an elevated white blood cell count, and chest X-ray showed infiltrates.
        Treatment:
        The patient was diagnosed with community-acquired pneumonia (ICD-10 Code: J18.9) and was treated with the following medications:

        Antibiotics: Prescribed a course of antibiotics for bacterial infection.
        Supportive Care: Received supportive care to manage symptoms.
        Complications and Additional Diagnosis:
        During the hospital stay, there was concern for possible deep vein thrombosis (DVT) due to leg swelling and pain.

        ICD-10 Code: I82.409 (Deep vein thrombosis of unspecified lower extremity)
        Doppler ultrasound confirmed the diagnosis, and anticoagulation therapy was initiated.

        Other Medical Considerations:
        Additionally, the patient had a history of hypertension and was monitored closely for any cardiac complications.

        Discharge Information:
        The patient is discharged with the following medications:

        Antibiotics : Complete the prescribed course.
        Anticoagulation Therapy : Continue as prescribed.
        Follow-up appointments are scheduled for continued care and monitoring.
        """   
    medical_data=st.text_area('Text to analyze',f'{discharge_summary}',height=400)
    return medical_data
    pass

# This function is used to use document input from user.
# Currently , it only supports PDF documents.
def docInputExtraction():
      uploaded_file = st.file_uploader("Choose a pdf file")
      if(uploaded_file is not None):
        reader = PdfReader(uploaded_file)
        number_of_pages = len(reader.pages)
        page = reader.pages[0]
        text_data = page.extract_text()
        st.toast('PDF processing completed!')
        st.info('Note: For prototype purposes, the application currently processes only the first page of the PDF or document. Full document processing will be available in future updates. ')
        return text_data
      else:
          st.warning("Upload a file to get started.")
      pass

#----------------------------------------------------------------
# Main Function --------------------------------
#----------------------------------------------------------------
def main():
  st.title('⚕️ S.E.E.R: System for Efficient Encoding and Reference')
  st.write('📕 Identify the Diseases and corresponding ICD10 codes in a document with ease 🔍 .')
  on = st.toggle('Switch to Document Mode ➡️')
  if on:
       input_data=docInputExtraction()
  else:
        input_data= textInputExtraction()
  prototype_mode = st.toggle('Prototype Mode ➡️',value=True)
  if prototype_mode:
    nlp=loading_ml_model()
  else:
    nlp=load_nlp_model()
  st.toast('Model loaded and ready for use.',icon='😍')
  print("Completed loading the NLP model.")
  if st.button('Extract'):
    st.toast('Data Extraction is started',icon='😍')
    st.subheader('Data Extraction Summary  📋:')
    # Processing Data with nlp model
    doc=nlp(input_data)
    print("Extracted the data.")
    st.success('✅ Symptoms and procedures successfully identified and highlighted for your review. ')
    # Adding colors to the rules
    colors = {"SYMPTOM": "orange", "PROCEDURE": "green"}
    options = {"colors": colors}
    visualize_ent(doc)
    print("Starting visualization of the data....")
    # Visualization of extracted data
    highlighted_text = displacy.render(doc, style="ent", options=options, page=True)
    st.components.v1.html(highlighted_text, width=1000, height=1000, scrolling=True)
    print("Visualization Completed.")
    print("Calling post processing function.")
    st.success('✅ S.E.E.R Assessment Report generation is now completed.')
    post_processing(doc)
    st.write('Made with ❤️  by team Inevitables.')

if __name__ == "__main__":
    main()
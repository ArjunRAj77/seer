import streamlit as st
import pymongo
import pandas as pd
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
import os


st.set_page_config(page_title="S.E.E.R", page_icon="⚕️")
@st.cache_resource
def init_connection():
    # pwd = st.secrets["db_password"]
    # username = st.secrets["db_username"]
    # host = st.secrets["db_host"]
    pwd = os.environ.get("DBPASSWORD") or st.secrets["db_password"]
    username = os.environ.get("DBUSERNAME") or st.secrets["db_username"]
    host = os.environ.get("DBHOST") or st.secrets["db_host"]
    uri = f"mongodb+srv://{username}:{pwd}@{host}/?retryWrites=true&w=majority"
    return pymongo.MongoClient(uri, server_api=ServerApi('1'))


def get_collection(collection_name):
    db = client.icd10_data
    return db[collection_name]

client = init_connection()
collection_name = "icd10_codes"

class SessionState:
    def __init__(self):
        self.icd_search_query = ""

session_state = SessionState()


def main():
    st.title('⚕️ S.E.E.R: System for Efficient Encoding and Reference')
    on = st.toggle('Switch to ICD Code Search Mode ➡️') # Added toggle support instead of buttons.
    if on:
        icd10CodeSearchMode()
    else:
        symptomSearchMode()


def icd10CodeSearchMode():
    st.header("ICD Code Search 📑")
    st.write("You can use the option to search for ICD Codes and identify the diseases")

    session_state = st.session_state
    if not hasattr(session_state, 'icd_search_query'):
        session_state.icd_search_query = ""

    icd_search_query = st.text_input("Enter your search query 🔎", value=session_state.icd_search_query)

    search_col, clear_col = st.columns(2)

        
    if search_col.button("Search ICD10 code ", key="icd10_search_button") and icd_search_query:  # Unique key for tile A
        results = icd10_search(icd_search_query)
        # Convert results to a DataFrame for better display
        df_results = pd.DataFrame(list(results))
        if not df_results.empty:
            st.subheader("Search Results:")
            st.table(df_results[["ICD10_Code", "Description"]])

            if st.button("Download Results as CSV 💾", key="icd_download_button"):
                download_symptom_results(df_results)

          #   csv_data = df_results.to_csv(index=False).encode('utf-8')
          #     st.download_button(
          #       label="Download Results as CSV 💾",
           #        data=csv_data,
           #        file_name="icd_search_results.csv",
           #        key="download_button"
           #   ) 
           

        else:
           st.warning("No results were found!") 

        if clear_col.button("Clear results🔄", key="icd10_clear_button"):
         session_state.icd_search_query = ""
         icd_search_query = " "




def symptomSearchMode():
    st.header("Symptoms search 🦠")
    st.write("You can use the option to search for symptoms and identify the ICD Codes for it.")

    session_state = st.session_state
    if not hasattr(session_state, 'icd_search_query'):
        session_state.icd_search_query = ""

    search_query = st.text_input("Enter your search query 🔎", value=session_state.icd_search_query)  # Provide a label here

    search_col, clear_col = st.columns(2)

    # Add functionality here
    if search_col.button("Search Symptoms", key="symptom_button"
                 ) and search_query:  # Unique key for tile B
        results = symptomSearch(search_query)
        # Convert results to a DataFrame for better display
        df_results = pd.DataFrame(list(results))
        if not df_results.empty:
            st.subheader("Search Results:")
            st.table(df_results[["ICD10_Code", "Description"]])

            csv_data = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV 💾",
                data=csv_data,
                file_name="symptom_search.csv",
                key="download_button"
            )
        else:
            st.warning("No results were found!")

        session_state.icd_search_query = search_query
   


        if clear_col.button("Clear results🔄", key="icd10_clear_button"):
         session_state.icd_search_query = ""
        # icd_search_query = " "
        
        

def icd10_search(icd_search_query):
    collection = get_collection(collection_name)
    query = {"ICD10_Code": {"$regex": icd_search_query, "$options": "i"}}
    # Perform the search for ICD 10 codes
    results = collection.find(query)
    return results

def symptomSearch(search_query):
    collection = get_collection(collection_name)
    query = {"Description": {"$regex": search_query, "$options": "i"}}
    # Perform the search for matching with the symptoms.
    results = collection.find(query)
    return results

def download_symptom_results(df_results):
    csv_data = df_results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Results as CSV 💾",
        data=csv_data,
        file_name="icd_code_search.csv",
        key="icd_download_button"  # Use a different key for the download button
    )

if __name__ == "__main__":
    main()

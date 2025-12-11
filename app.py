import streamlit as st
import pandas as pd
import parser
import exporter

st.set_page_config(page_title="Research Paper Extractor", layout="wide")

st.title("Research Paper to Excel Extractor")
st.markdown("Upload a research paper (PDF) to extract sections into an Excel file.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("Process Paper"):
        with st.spinner("Processing..."):
            try:
                # Parse the PDF
                data = parser.parse_pdf(uploaded_file)
                
                # Show preview
                st.subheader("Extracted Data Preview")
                df = pd.DataFrame([data])
                st.dataframe(df)
                
                # Export to Excel
                excel_data = exporter.to_excel(data)
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name="extracted_paper.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")

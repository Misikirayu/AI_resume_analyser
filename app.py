import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
import PyPDF2
import docx
from pdfminer.high_level import extract_text
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

def extract_text_from_pdf(file):
    return extract_text(file)

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def analyze_resume(resume_text):
    prompt = """
    You are an expert resume analyzer. Please analyze the following resume and provide feedback in the following JSON format exactly:
    {
        "Overall Score": <number between 0-100>,
        "Key Strengths": [<list of strengths>],
        "Areas for Improvement": [<list of areas>],
        "Skills Assessment": "<detailed analysis>",
        "Experience Analysis": "<detailed analysis>",
        "Education Analysis": "<detailed analysis>",
        "Format and Presentation": "<detailed analysis>",
        "Specific Recommendations": [<list of recommendations>]
    }

    Ensure the response is valid JSON. Do not include any text before or after the JSON object.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": f"Here is the resume to analyze:\n\n{resume_text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        
        # Get the response content
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse the JSON response
        try:
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = [
                "Overall Score", "Key Strengths", "Areas for Improvement",
                "Skills Assessment", "Experience Analysis", "Education Analysis",
                "Format and Presentation", "Specific Recommendations"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    return {
                        "error": f"Missing required field: {field}",
                        "raw_response": response_text
                    }
            
            return analysis
            
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse AI response as JSON. Please try again.",
                "raw_response": response_text
            }
            
    except Exception as e:
        return {
            "error": f"API Error: {str(e)}",
            "raw_response": "No response received"
        }

def main():
    st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
    
    st.title("🤖 AI Resume Analyzer")
    st.markdown("""
    ### Upload your resume and get detailed AI-powered analysis and feedback!
    This tool uses advanced AI to analyze your resume and provide actionable insights.
    """)
    
    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=['pdf', 'docx'])
    
    if uploaded_file:
        with st.spinner('Analyzing your resume... Please wait...'):
            # Extract text based on file type
            if uploaded_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            else:
                resume_text = extract_text_from_docx(uploaded_file)
            
            # Get analysis
            analysis = analyze_resume(resume_text)
            
            if "error" in analysis:
                st.error(f"An error occurred: {analysis['error']}")
                if "raw_response" in analysis:
                    with st.expander("Show raw AI response"):
                        st.code(analysis["raw_response"])
            else:
                # Display overall score with a progress bar
                st.subheader("Overall Score")
                st.progress(analysis["Overall Score"] / 100)
                st.write(f"{analysis['Overall Score']}/100")
                
                # Display key strengths
                st.subheader("💪 Key Strengths")
                for strength in analysis["Key Strengths"]:
                    st.write(f"- {strength}")
                
                # Display areas for improvement
                st.subheader("🎯 Areas for Improvement")
                for area in analysis["Areas for Improvement"]:
                    st.write(f"- {area}")
                
                # Create three columns for detailed analysis
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("🔧 Skills Assessment")
                    st.write(analysis["Skills Assessment"])
                
                with col2:
                    st.subheader("💼 Experience Analysis")
                    st.write(analysis["Experience Analysis"])
                
                with col3:
                    st.subheader("🎓 Education Analysis")
                    st.write(analysis["Education Analysis"])
                
                # Format and Presentation
                st.subheader("📝 Format and Presentation")
                st.write(analysis["Format and Presentation"])
                
                # Specific Recommendations
                st.subheader("🚀 Specific Recommendations")
                for rec in analysis["Specific Recommendations"]:
                    st.write(f"- {rec}")
                
                # Add download button for the analysis
                st.download_button(
                    label="Download Analysis Report",
                    data=json.dumps(analysis, indent=2),
                    file_name="resume_analysis.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main() 
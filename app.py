import streamlit as st
import requests
from bs4 import BeautifulSoup
import PyPDF2
from openai import OpenAI

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

# Streamlit App Title
st.set_page_config(page_title="GenAI Chatbot", layout="centered")
st.title("🧠 GenAI Chatbot with Custom Data")

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload PDF", "Scrape Website", "Ask Questions"])

# Section 1: Upload PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + " "
    return text[:4000]  # Limit text to fit OpenAI context size

if page == "Upload PDF":
    st.header("📂 Upload a PDF Document")
    uploaded_pdf = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_pdf:
        pdf_text = extract_text_from_pdf(uploaded_pdf)
        st.session_state["context"] = {"pdf": pdf_text}
        st.success("✅ PDF content extracted successfully!")

# Section 2: Scrape Website
def scrape_website(url):
    headers = {"User-Agent": "Mozilla/5.0"}  # Avoid getting blocked
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Failed to fetch page, Status Code: {response.status_code}"}
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string if soup.title else "No Title"
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return {"title": title, "headings": headings, "content": " ".join(paragraphs)[:4000]}

if page == "Scrape Website":
    st.header("🌐 Scrape Website Content")
    website_url = st.text_input("Enter website URL:")
    if st.button("Scrape Website"):
        if website_url:
            website_content = scrape_website(website_url)
            if "error" in website_content:
                st.error(website_content["error"])
            else:
                st.session_state["context"] = {"website": website_content}
                st.success("✅ Website content extracted successfully!")

# Section 3: Ask Questions
def handle_question(question):
    if "context" not in st.session_state:
        return "No data available in session."
    context = st.session_state["context"]
    if isinstance(context, dict):
        if "website" in context:
            return ask_question_about_website(question, context["website"])
        elif "pdf" in context:
            return ask_question_about_pdf(question, context["pdf"])
    return "Invalid data format in session."

def ask_question_about_website(question, scraped_data, model="openai/gpt-3.5-turbo-0613"):
    title = scraped_data.get("title", "")
    headings = "\n".join(scraped_data.get("headings", []))
    content = scraped_data.get("content", "")[:2000]
    prompt = f"""You are an expert AI assistant. Answer the question based on the provided website data.\n\nWebsite Title: {title}\nHeadings: {headings}\nMain Content: {content}\n\nQuestion: {question}\n\nProvide a concise and relevant answer."""
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    )
    return completion.choices[0].message.content

def ask_question_about_pdf(question, pdf_data, model="openai/gpt-3.5-turbo-0613"):
    prompt = f"""You are an expert AI assistant. Answer the question based on the provided PDF document.\n\nPDF Content: {pdf_data}\n\nQuestion: {question}\n\nProvide a concise and relevant answer."""
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    )
    return completion.choices[0].message.content

if page == "Ask Questions":
    st.header("❓ Ask a Question About Your Data")
    question = st.text_input("Enter your question:")
    if st.button("Get Answer"):
        if "context" in st.session_state:
            answer = handle_question(question)
            st.write("**Chatbot Response:**", answer)
        else:
            st.warning("Please provide a website URL or upload a PDF first.")

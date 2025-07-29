import streamlit as st
import os

# --- Page Setup ---
st.set_page_config(
    page_title="Customer Service Knowledge Base", 
    layout="wide",
    initial_sidebar_state="collapsed"
)


PDF_DIR = "/Users/danielwanganga/Documents/Airtel_AI/SEs/knowledge_base/pdfs"

def inject_custom_css():
    st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

        /* CSS Variables for theming */
        :root {
            --primary-color: #E4002B;
            --primary-hover: #C00021;
            --primary-light: rgba(228, 0, 43, 0.1);
            --secondary-color: #2563EB;
            --secondary-hover: #1D4ED8;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --danger-color: #EF4444;
            --border-radius: 12px;
            --border-radius-lg: 16px;
            --transition: all 0.3s ease;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        /* Reset Streamlit defaults */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Hide Streamlit elements */
        #MainMenu { visibility: hidden; }
        .stDeployButton { display: none; }
        footer { visibility: hidden; }
        
        /* Main container improvements */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            color: white;
            padding: 2rem;
            border-radius: var(--border-radius-lg);
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: var(--shadow-lg);
        }

        .main-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Search section */
        .search-section {
            margin-bottom: 2rem;
        }

        .search-container {
            position: relative;
            max-width: 600px;
            margin: 0 auto;
        }

        .search-input {
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            border: 2px solid #e2e8f0;
            border-radius: 50px;
            font-size: 1rem;
            outline: none;
            transition: var(--transition);
            background: white;
            box-shadow: var(--shadow-sm);
        }

        .search-input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
            font-size: 1.1rem;
        }

        /* Grid layouts */
        .campaign-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .briefing-grid {
            display: grid;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        /* Card styles */
        .card {
            background: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            border: 1px solid #e2e8f0;
            transition: var(--transition);
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .campaign-card {
            border-left: 4px solid var(--primary-color);
        }

        .campaign-card h3 {
            color: var(--primary-color);
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }

        .campaign-date {
            color: #64748b;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .briefing-card {
            border-left: 4px solid var(--warning-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .briefing-content h4 {
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
            font-weight: 600;
            color: #1e293b;
        }

        .briefing-due {
            color: var(--warning-color);
            font-weight: 600;
            font-size: 0.875rem;
        }

        /* Section headers */
        .section-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }

        .section-icon {
            font-size: 1.5rem;
            color: var(--primary-color);
        }

        .section-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        }

        /* Post list */
        .post-list {
            background: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            border: 1px solid #e2e8f0;
        }

        .post-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f1f5f9;
            transition: var(--transition);
        }

        .post-item:last-child {
            border-bottom: none;
        }

        .post-item:hover {
            background: #f8fafc;
            margin: 0 -1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            border-radius: 8px;
        }

        .post-icon {
            color: var(--secondary-color);
            font-size: 1.1rem;
        }

        .post-title {
            color: #334155;
            font-weight: 500;
            text-decoration: none;
        }

        .post-title:hover {
            color: var(--primary-color);
        }

        /* Tools section */
        .tools-section {
            background: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            border: 1px solid #e2e8f0;
            margin-bottom: 2rem;
        }

        .tool-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--secondary-color);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: var(--border-radius);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
        }

        .tool-link:hover {
            background: var(--secondary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        /* Feedback section */
        .feedback-section {
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-radius: var(--border-radius-lg);
            padding: 2rem;
            margin-top: 2rem;
            border: 1px solid #e2e8f0;
        }

        .feedback-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .feedback-input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e2e8f0;
            border-radius: var(--border-radius);
            font-size: 1rem;
            outline: none;
            transition: var(--transition);
            margin-bottom: 1rem;
        }

        .feedback-input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .feedback-btn {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: var(--border-radius);
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }

        .feedback-btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .feedback-btn:disabled {
            background: #94a3b8;
            cursor: not-allowed;
            transform: none;
        }

        /* Alert styles */
        .alert {
            padding: 1rem;
            border-radius: var(--border-radius);
            border: 1px solid;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .alert-success {
            background: #f0fdf4;
            border-color: #bbf7d0;
            color: #166534;
        }

        .alert-warning {
            background: #fffbeb;
            border-color: #fed7aa;
            color: #92400e;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 2rem;
            }
            
            .campaign-grid {
                grid-template-columns: 1fr;
            }
            
            .briefing-card {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
            
            .section-title {
                font-size: 1.5rem;
            }
        }

        /* Streamlit widget styling */
        .stTextInput > div > div > input {
            border-radius: 50px !important;
            border: 2px solid #e2e8f0 !important;
            padding: 1rem 1rem 1rem 3rem !important;
            font-size: 1rem !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px var(--primary-light) !important;
        }

        .stButton > button {
            background: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--border-radius) !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            transition: var(--transition) !important;
        }

        .stButton > button:hover {
            background: var(--primary-hover) !important;
            transform: translateY(-1px) !important;
        }
    </style>
    """)

# Inject CSS
inject_custom_css()

# Header
st.html("""
<div class="main-header">
    <h1><i class="fas fa-chart-line"></i> Customer Service Knowledge Base</h1>
</div>
""")

# Search Section
st.html("""
<div class="search-section">
    <div class="search-container">
        <i class="fas fa-search search-icon"></i>
    </div>
</div>
""")

search_query = st.text_input("", placeholder="Search for offers, guides, or SOPs", label_visibility="collapsed")

# Campaigns Section
st.html("""
<div class="section-header">
    <i class="fas fa-rocket section-icon"></i>
    <h2 class="section-title">Important Annoucements</h2>
</div>
""")

campaigns = [
    {"title": "NEW SMARTA Bundles", "date": "14 Jul 2025"},
    {"title": 'Rudishiwa 100% Extended', "date": "27 Jun 2025"},
    {"title": "Airtel AI Spam Feature Awareness", "date": "25 Jun 2025"},
]

st.html('<div class="campaign-grid">')
for campaign in campaigns:
    st.html(f"""
    <div class="card campaign-card">
        <h3><i class="fas fa-bullhorn"></i> {campaign['title']}</h3>
        <p class="campaign-date"><i class="fas fa-calendar"></i> Published on {campaign['date']}</p>
    </div>
    """)
st.html('</div>')

# Mandatory Briefings Section
st.html("""
<div class="section-header">
    <i class="fas fa-graduation-cap section-icon"></i>
    <h2 class="section-title">Mandatory Briefings</h2>
</div>
""")

briefings = [
    {"title": "July Airtime & Bundle Commission Structure", "due": "31 Jul 2025"},
    {"title": "TSE Training,Parkside Tower M Floor", "due": "10 Jul 2025"},
    {"title": "Customer Objection Handling Scripts", "due": "31 Jul 2025"},
]

st.html('<div class="briefing-grid">')
for briefing in briefings:
    st.html(f"""
    <div class="card briefing-card">
        <div class="briefing-content">
            <h4><i class="fas fa-clock"></i> {briefing['title']}</h4>
        </div>
        <div class="briefing-due">
            Due: {briefing['due']}
        </div>
    </div>
    """)
st.html('</div>')

# Top Posts Section
st.html("""
<div class="section-header">
    <i class="fas fa-star section-icon"></i>
    <h2 class="section-title">Top Posts</h2>
</div>
""")

top_posts = [
    "New SMARTA Bundle Ranges",
    "New Home Broadband Prices", 
    "New Commission Band"
]

st.html('<div class="post-list">')
for post in top_posts:
    st.html(f"""
    <div class="post-item">
        <i class="fas fa-file-alt post-icon"></i>
        <a href="#" class="post-title">{post}</a>
    </div>
    """)
st.html('</div>')

# Tools & Quick Links Section
st.html("""
<div class="section-header">
    <i class="fas fa-tools section-icon"></i>
    <h2 class="section-title">Tools & Quick Links</h2>
</div>
""")

st.html("""
<div class="tools-section">
    <a href="#" class="tool-link">
        <i class="fas fa-mobile-alt"></i>
        Sales App
    </a>
</div>
""")

# Feedback Section
st.html("""
<div class="feedback-section">
    <h3 class="feedback-title">
        <i class="fas fa-comments"></i>
        Quick Feedback
    </h3>
</div>
""")

# Create columns for better layout
col1, col2 = st.columns([3, 1])

with col1:
    feedback = st.text_input(
        "",
        placeholder="What's missing or unclear? (Max 165 Characters)",
        max_chars=165,
        label_visibility="collapsed"
    )

with col2:
    submit_clicked = st.button("Submit Feedback", type="primary")

if submit_clicked:
    if feedback:
        st.html("""
        <div class="alert alert-success">
            <i class="fas fa-check-circle"></i>
            Thank you! Your feedback will help us improve this KB.
        </div>
        """)
    else:
        st.html("""
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            Please enter your feedback before submitting.
        </div>
        """)

# Add some spacing at the bottom
st.html('<div style="height: 2rem;"></div>')
# Add function to manually rebuild index
def manual_rebuild_index():
    """Function to manually trigger index rebuild"""
    if st.button("🔄 Force Rebuild Knowledge Base", help="This will delete the current index and rebuild from PDFs"):
        st.cache_resource.clear()
        st.rerun()
  # Add manual rebuild option in sidebar
with st.sidebar:
        st.subheader("🔧 Knowledge Base Controls")
        manual_rebuild_index()
        
        # Show current PDF files
if os.path.exists(PDF_DIR):
            pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
            st.write(f"📁 Current PDFs ({len(pdf_files)}):")
            for pdf_file in pdf_files:
                st.write(f"• {pdf_file}")
else:
            st.write("📁 PDF directory not found")
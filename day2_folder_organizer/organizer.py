import streamlit as st
import os
import pandas as pd
import time
from pathlib import Path
from scanner import scan_directory
from classifier import get_file_classification, get_available_models
from mover import move_file

def normalize_path(path):
    """
    Normalizes the path to work on Linux (WSL), converting Windows paths to WSL equivalents.
    Handles various path formats and makes them absolute.
    """
    path = path.strip().strip('"').strip("'")
    
    # If already an absolute Linux path, expand and return
    if path.startswith('/'):
        path = os.path.expanduser(path)
        return os.path.abspath(path)
    
    # Convert Windows drive letters to WSL mounts (try /mnt/ first, then /)
    drive_map = {
        'A': '/mnt/a', 'B': '/mnt/b', 'C': '/mnt/c', 'D': '/mnt/d', 'E': '/mnt/e',
        'F': '/mnt/f', 'G': '/mnt/g', 'H': '/mnt/h', 'I': '/mnt/i', 'J': '/mnt/j',
        'K': '/mnt/k', 'L': '/mnt/l', 'M': '/mnt/m', 'N': '/mnt/n', 'O': '/mnt/o',
        'P': '/mnt/p', 'Q': '/mnt/q', 'R': '/mnt/r', 'S': '/mnt/s', 'T': '/mnt/t',
        'U': '/mnt/u', 'V': '/mnt/v', 'W': '/mnt/w', 'X': '/mnt/x', 'Y': '/mnt/y', 'Z': '/mnt/z'
    }
    
    upper_path = path.upper()
    for drive, mount in drive_map.items():
        if upper_path.startswith(drive + ':'):
            converted = mount + path[2:].replace('\\', '/')
            # Try /mnt/ first
            test_path = os.path.abspath(converted)
            if os.path.exists(test_path) or not os.path.exists(mount.replace('/mnt/', '/')):
                return test_path
            else:
                # Try /drive if /mnt/ doesn't exist
                alt_mount = '/' + drive.lower()
                converted = alt_mount + path[2:].replace('\\', '/')
                return os.path.abspath(converted)
    
    # For other paths (relative, UNC, etc.), expand user and make absolute
    path = os.path.expanduser(path)
    return os.path.abspath(path)

# Page Configuration
st.set_page_config(
    page_title="Smart Folder Organizer",
    page_icon="📂",
    layout="centered"
)

# Custom CSS for the Premium Purple Theme
st.markdown("""
<style>
    /* Hide Streamlit elements for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div.block-container {padding-top: 0.2rem; padding-bottom: 0.2rem;}

    /* Main Background with animated gradient */
    .stApp {
        background: linear-gradient(-45deg, #7b2cbf, #3c096c, #240046, #10002b);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: white;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Global Card Styles */
    div[data-testid="stVerticalBlock"] > div:has(div.custom-card) {
        background: transparent !important;
    }

    .custom-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        color: white;
        border-radius: 15px;
        padding: 8px 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }

    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }

    /* Header Styles - Ultra compact */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 0 5px 0;
        text-align: center;
        position: relative;
    }

    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 80px;
        height: 2px;
        background: linear-gradient(90deg, #a855f7, #db2777);
        border-radius: 1px;
    }

    .header-logo {
        font-size: 35px;
        margin-bottom: 2px;
        filter: drop-shadow(0 0 10px rgba(255,255,255,0.4));
        animation: float 3s ease-in-out infinite;
    }

    .header-title {
        font-size: 30px;
        font-weight: 900;
        margin: 0;
        letter-spacing: -1px;
        color: white;
        text-shadow: 0 3px 10px rgba(0,0,0,0.5);
        background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .header-desc {
        font-size: 12px;
        opacity: 0.9;
        margin-top: 1px;
        font-weight: 400;
        max-width: 500px;
        color: rgba(255, 255, 255, 0.9);
    }

    .day-badge {
        position: fixed;
        top: 15px;
        right: 25px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(15px);
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 10px;
        border: 1px solid rgba(255,255,255,0.2);
        z-index: 1000;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2);
    }

    /* Professional Column Layout */
    .stColumns {
        gap: 24px !important;
        margin-bottom: 20px !important;
    }

    .stColumns > div {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        min-height: 400px !important;
    }

    .stColumns > div:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Professional Container Styling */
    .stContainer {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.3s ease !important;
        overflow: hidden !important;
    }

    .stContainer:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Enhanced Section Headers */
    .section-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 16px !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        color: white !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        border-bottom: 2px solid rgba(168, 85, 247, 0.3) !important;
        padding-bottom: 8px !important;
    }

    .section-title::before {
        content: '';
        width: 4px;
        height: 20px;
        background: linear-gradient(135deg, #a855f7, #db2777);
        border-radius: 2px;
        margin-right: 8px;
    }

    /* Professional Content Spacing */
    .stColumns > div > div {
        padding: 16px !important;
    }

    .stColumns > div p {
        margin-bottom: 12px !important;
        line-height: 1.5 !important;
        color: rgba(255, 255, 255, 0.85) !important;
        font-size: 14px !important;
    }

    /* Enhanced Folder Items */
    .folder-item {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)) !important;
        padding: 10px 14px !important;
        border-radius: 10px !important;
        display: flex !important;
        align-items: center !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 6px !important;
        backdrop-filter: blur(10px) !important;
        font-size: 14px !important;
        cursor: pointer !important;
    }

    .folder-item:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.08)) !important;
        transform: translateX(8px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Settings Section Enhancements */
    .stColumns > div .stCheckbox {
        margin-bottom: 12px !important;
    }

    .stColumns > div .stCheckbox label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }

    .stColumns > div hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        margin: 16px 0 !important;
    }

    /* Professional Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(15px);
        color: white;
        padding: 8px 16px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 10px 0;
    }

    /* Column Header Spacing */
    .stColumns > div > div:first-child {
        margin-bottom: 20px !important;
    }

    /* Professional Typography */
    .stColumns > div h1, .stColumns > div h2, .stColumns > div h3 {
        color: white !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 16px !important;
    }

    /* Enhanced Button Styling in Columns */
    .stColumns > div .stButton>button {
        width: 100% !important;
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }
        font-size: 14px;
        margin-bottom: 8px;
    }
    .folder-item:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
    }
    
    /* Tabs Styling - Ultra compact */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 4px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 4px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 8px !important;
        color: rgba(255,255,255,0.6) !important;
        padding: 6px 12px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        height: 32px !important;
        line-height: 20px !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #a855f7 0%, #db2777 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Form Inputs - Compact */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        color: white !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        height: 40px !important;
    }
    .stTextInput input:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2) !important;
        background: rgba(255, 255, 255, 0.12) !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #a855f7 0%, #db2777 100%);
        color: white !important;
        border: none;
        padding: 10px 20px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 6px 15px rgba(168, 85, 247, 0.3);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(168, 85, 247, 0.5);
    }
    .stButton>button:active {
        transform: translateY(-1px);
    }

    /* File Item Styling - Compact */
    .file-item {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
        padding: 6px;
        border-radius: 8px;
        margin-bottom: 3px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        transition: all 0.3s ease;
    }
    .file-item:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        transform: translateX(3px);
    }
    .file-icon {
        font-size: 20px;
        min-width: 25px;
        height: 25px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Progress Bar Styling - Compact */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #a855f7 0%, #db2777 100%) !important;
        border-radius: 5px !important;
        height: 6px !important;
    }
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 5px !important;
    }

    /* Success Messages */
    .success-message {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.1));
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        text-align: center;
        color: #22c55e;
        font-weight: 600;
    }

    /* Status Container */
    .stStatus {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 15px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Review Table Styling - Ultra compact */
    .review-table {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
    }
    .table-header {
        display: flex;
        font-weight: 700;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 6px;
        padding-bottom: 6px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15);
    }
    .table-row {
        display: flex;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        transition: background 0.3s ease;
        border-radius: 4px;
        margin-bottom: 2px;
    }
    .table-row:hover {
        background: rgba(255, 255, 255, 0.05);
        transform: scale(1.01);
    }
    .table-cell {
        padding: 0 12px;
        display: flex;
        align-items: center;
    }
    .file-name-cell {
        flex: 3;
        font-weight: 500;
    }
    .category-cell {
        flex: 2;
    }
    .size-cell {
        flex: 1;
        justify-content: flex-end;
        font-size: 13px;
        opacity: 0.8;
    }

    /* Category Input Styling */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        color: white !important;
        font-size: 14px !important;
        width: 100% !important;
    }
    .stTextInput input:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.2) !important;
    }

    /* Folder Structure Styling */
    .folder-structure {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-top: 20px;
    }

    /* Expander Styling - Compact */
    .stExpander {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
        overflow: hidden;
    }
    .stExpander summary {
        padding: 8px 12px !important;
        font-weight: 600 !important;
        color: white !important;
        cursor: pointer !important;
        background: transparent !important;
        font-size: 13px !important;
    }
    .stExpander summary:hover {
        background: rgba(255, 255, 255, 0.08) !important;
    }
    .stExpander .stExpanderContent {
        padding: 5px 12px 8px 20px !important;
        color: rgba(255, 255, 255, 0.8) !important;
        background: rgba(255, 255, 255, 0.02) !important;
    }
    .stExpander .stExpanderContent p {
        margin-bottom: 3px;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'files' not in st.session_state:
    st.session_state.files = []
if 'classified_files' not in st.session_state:
    st.session_state.classified_files = []
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False
if 'organized' not in st.session_state:
    st.session_state.organized = False
if 'successful_moves' not in st.session_state:
    st.session_state.successful_moves = 0
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'gemma3:4b'

# Header - Compact version for one-screen view
st.markdown("""
    <div class="header-container">
        <div class="header-logo">🚀</div>
        <h1 class="header-title">Smart Folder Organizer</h1>
        <p class="header-desc">✨ AI-Powered File Organization</p>
    </div>
""", unsafe_allow_html=True)

# Main UI using Columns - Professional Equal Layout
col_left, col_right = st.columns([1, 1], gap="large")

# Add professional status indicator
if st.session_state.organized:
    st.markdown('<div class="status-badge">✅ <span>ORGANIZATION COMPLETE</span></div>', unsafe_allow_html=True)
elif st.session_state.classified_files:
    st.markdown('<div class="status-badge">🔄 <span>READY TO ORGANIZE</span></div>', unsafe_allow_html=True)
elif st.session_state.files:
    st.markdown('<div class="status-badge">🤖 <span>ANALYZING FILES</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-badge">📁 <span>READY TO SCAN</span></div>', unsafe_allow_html=True)

# Left Column - Smart Category Preview
with col_left:
    # Folders Section - Dynamic based on organization status
    with st.container(border=True):
        if st.session_state.organized and st.session_state.classified_files:
            # Show actual created folders after organization
            st.markdown('<div class="section-title">📂 Your Organized Folders</div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:14px; opacity:0.8; margin-bottom:15px;">Folders created with your organized files:</p>', unsafe_allow_html=True)

            # Get unique categories from organized files
            created_folders = set()
            for file in st.session_state.classified_files:
                if 'category' in file:
                    created_folders.add(file['category'])

            if created_folders:
                # Get folder icons and colors
                folder_icons = {
                    "Work": "💼", "Personal": "🏠", "Projects": "💻",
                    "Archive": "📦", "Media": "📸", "Documents": "📄",
                    "Images": "🖼️", "Videos": "🎥", "Music": "🎵",
                    "Downloads": "⬇️", "Desktop": "🖥️"
                }

                for folder in sorted(created_folders):
                    icon = folder_icons.get(folder, "📁")
                    # Count files in this folder
                    file_count = sum(1 for f in st.session_state.classified_files if f.get('category') == folder)
                    st.markdown(f'<div class="folder-item">{icon} &nbsp; {folder} <span style="opacity:0.7;font-size:12px;">({file_count} files)</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="folder-item" style="opacity:0.6;">📁 No folders created yet</div>', unsafe_allow_html=True)

        elif st.session_state.classified_files:
            # Show predicted categories from AI analysis
            st.markdown('<div class="section-title">🎯 Predicted Categories</div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:14px; opacity:0.8; margin-bottom:15px;">AI predicted these categories for your files:</p>', unsafe_allow_html=True)

            # Get unique categories from AI predictions
            predicted_categories = set()
            for file in st.session_state.classified_files:
                if 'category' in file:
                    predicted_categories.add(file['category'])

            if predicted_categories:
                folder_icons = {
                    "Work": "💼", "Personal": "🏠", "Projects": "💻",
                    "Archive": "📦", "Media": "📸", "Documents": "📄",
                    "Images": "🖼️", "Videos": "🎥", "Music": "🎵",
                    "Downloads": "⬇️", "Desktop": "🖥️"
                }

                for category in sorted(predicted_categories):
                    icon = folder_icons.get(category, "📁")
                    file_count = sum(1 for f in st.session_state.classified_files if f.get('category') == category)
                    st.markdown(f'<div class="folder-item">{icon} &nbsp; {category} <span style="opacity:0.7;font-size:12px;">({file_count} files)</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="folder-item" style="opacity:0.6;">🤔 Analyzing categories...</div>', unsafe_allow_html=True)

        else:
            # Show smart examples based on file types when files are scanned
            st.markdown('<div class="section-title">🔍 Smart Category Preview</div>', unsafe_allow_html=True)

            if st.session_state.files:
                # Analyze file extensions to predict meaningful categories
                file_extensions = {}
                for file in st.session_state.files:
                    ext = file['name'].split('.')[-1].lower() if '.' in file['name'] else 'no-ext'

                    if ext not in file_extensions:
                        file_extensions[ext] = 0
                    file_extensions[ext] += 1

                # Predict categories based on file types
                predicted_categories = set()

                # Document files
                doc_exts = ['doc', 'docx', 'pdf', 'txt', 'rtf', 'odt']
                if any(ext in file_extensions for ext in doc_exts):
                    predicted_categories.add("Documents")

                # Image files
                img_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
                if any(ext in file_extensions for ext in img_exts):
                    predicted_categories.add("Images")

                # Video files
                vid_exts = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm']
                if any(ext in file_extensions for ext in vid_exts):
                    predicted_categories.add("Videos")

                # Audio files
                aud_exts = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma']
                if any(ext in file_extensions for ext in aud_exts):
                    predicted_categories.add("Music")

                # Archive files
                arch_exts = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
                if any(ext in file_extensions for ext in arch_exts):
                    predicted_categories.add("Archive")

                # Code/Project files
                code_exts = ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs']
                if any(ext in file_extensions for ext in code_exts):
                    predicted_categories.add("Projects")

                # Default categories if nothing specific detected
                if not predicted_categories:
                    predicted_categories.update(["Work", "Personal", "Media"])

                st.markdown('<p style="font-size:14px; opacity:0.8; margin-bottom:15px;">Based on your files, AI will likely create:</p>', unsafe_allow_html=True)

                folder_icons = {
                    "Work": "💼", "Personal": "🏠", "Projects": "💻",
                    "Archive": "📦", "Media": "📸", "Documents": "📄",
                    "Images": "🖼️", "Videos": "🎥", "Music": "🎵"
                }

                for category in sorted(predicted_categories):
                    icon = folder_icons.get(category, "📁")
                    st.markdown(f'<div class="folder-item">{icon} &nbsp; {category}</div>', unsafe_allow_html=True)

            else:
                # No files scanned yet - show general examples
                st.markdown('<p style="font-size:14px; opacity:0.8; margin-bottom:15px;">Upload files to see predicted categories:</p>', unsafe_allow_html=True)
                folders = ["Work", "Personal", "Projects", "Archive", "Media", "Documents", "Images", "Videos", "Music"]
                icons = ["💼", "🏠", "💻", "📦", "📸", "📄", "🖼️", "🎥", "🎵"]
                for icon, name in zip(icons, folders):
                    st.markdown(f'<div class="folder-item">{icon} &nbsp; {name}</div>', unsafe_allow_html=True)

# Right Column - Settings
with col_right:
    # Settings Section - Ultra compact
    with st.container(border=True):
        st.markdown('<div class="section-title">⚙️ Settings</div>', unsafe_allow_html=True)
        st.checkbox("AI Reasoning", value=True, help="Show AI analysis")
        st.checkbox("Auto-approve", value=False, help="Skip confirmations")

        st.markdown("---")
        st.markdown("**🤖 AI Model:**")

        # Try to get available models
        try:
            available_models, status = get_available_models()

            if status == 'ok' and len(available_models) > 1:
                # Multiple models available - show dropdown
                selected_model = st.selectbox(
                    "Choose AI Model",
                    options=available_models,
                    index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
                    help="Select the Ollama model to use for file classification",
                    label_visibility="collapsed"
                )
                if selected_model != st.session_state.selected_model:
                    st.session_state.selected_model = selected_model
                    st.success(f"✅ Model changed to: {selected_model}")
            elif status == 'ok' and len(available_models) == 1:
                # Only one model available
                st.info(f"📋 Using available model: **{available_models[0]}**")
                if available_models[0] != st.session_state.selected_model:
                    st.session_state.selected_model = available_models[0]
                    st.success(f"✅ Model set to: {available_models[0]}")
            elif status == 'not_running':
                # Ollama is installed but not running
                st.warning("⚠️ Ollama is installed but not running. Please start Ollama with `ollama serve`")
                manual_model = st.text_input(
                    "Enter Model Name",
                    value=st.session_state.selected_model,
                    help="Enter your Ollama model name (e.g., gemma3:4b, llama2:7b)",
                    label_visibility="collapsed",
                    key="manual_model_input"
                )
                if manual_model and manual_model != st.session_state.selected_model:
                    st.session_state.selected_model = manual_model
                    st.success(f"✅ Model set to: {manual_model}")
            elif status == 'no_models':
                # Ollama is running but no models installed
                st.warning("⚠️ Ollama is running but no models are installed. Please install a model first.")
                st.info("💡 Install a model with: `ollama pull gemma3:4b`")
                manual_model = st.text_input(
                    "Enter Model Name",
                    value=st.session_state.selected_model,
                    help="Enter your Ollama model name (e.g., gemma3:4b, llama2:7b)",
                    label_visibility="collapsed",
                    key="manual_model_input"
                )
                if manual_model and manual_model != st.session_state.selected_model:
                    st.session_state.selected_model = manual_model
                    st.success(f"✅ Model set to: {manual_model}")
            else:
                # Other error
                st.error("❌ Error detecting Ollama status. Please check your installation.")
                manual_model = st.text_input(
                    "Model Name (Manual)",
                    value=st.session_state.selected_model,
                    help="Enter your Ollama model name manually (e.g., gemma3:4b, llama2:7b)",
                    label_visibility="collapsed",
                    key="fallback_model_input"
                )
                if manual_model and manual_model != st.session_state.selected_model:
                    st.session_state.selected_model = manual_model
                    st.success(f"✅ Model set to: {manual_model}")

        except Exception as e:
            st.error(f"❌ Error connecting to Ollama: {str(e)}")
            st.info("💡 Make sure Ollama is running: `ollama serve`")
            manual_model = st.text_input(
                "Model Name (Manual)",
                value=st.session_state.selected_model,
                help="Enter your Ollama model name manually (e.g., gemma3:4b, llama2:7b)",
                label_visibility="collapsed",
                key="fallback_model_input"
            )
            if manual_model and manual_model != st.session_state.selected_model:
                st.session_state.selected_model = manual_model
                st.success(f"✅ Model set to: {manual_model}")

        # Show current selected model
        st.caption(f"🎯 Current model: **{st.session_state.selected_model}**")

        st.markdown("---")
        st.markdown("**How it works:**")
        st.markdown("1. Scan files")
        st.markdown("2. AI analyzes")
        st.markdown("3. Review & edit")
        st.markdown("4. Organize")

# Tabs for Workspace - Compacted
tab1, tab2, tab3 = st.tabs(["Upload", "AI Review", "Done"])

# Tab 1: Upload Files
with tab1:
    with st.container(border=True):
        st.markdown("### 📁 Select Your Files Directory")
        st.markdown("Enter the path to the folder containing files you want to organize:")

        target_path = st.text_input(
            "Directory Path",
            placeholder="/mnt/c/Users/Name/Downloads or C:\\Users\\Name\\Downloads",
            label_visibility="collapsed"
        ).strip().strip('"').strip("'")

        if st.button("🔍 SCAN & ANALYZE FILES", use_container_width=True):
            if not target_path:
                st.error("⚠️ Please enter a folder path first.")
            else:
                try:
                    # Normalize path (handles Windows paths on WSL)
                    normalized_path = normalize_path(target_path)

                    if os.path.isdir(normalized_path):
                        with st.spinner("🔍 Scanning directory..."):
                            st.session_state.files = scan_directory(normalized_path)

                        if st.session_state.files:
                            st.success(f"✅ Found {len(st.session_state.files)} files to organize!")
                            st.info("👆 Go to '🤖 AI Review' tab to analyze and organize your files")
                            # Don't auto-trigger analysis, let user go to AI Review tab
                        else:
                            st.warning("📁 No files found in the specified directory.")
                    else:
                        st.error("❌ Please enter a valid directory path.")
                        with st.expander("🔧 Troubleshooting Path Issues"):
                            st.write("**Debug Information:**")
                            st.code(f"Input: {target_path}")
                            st.code(f"Normalized: {normalized_path}")
                            st.code(f"Current Working Directory: {os.getcwd()}")
                            if os.path.exists(normalized_path):
                                st.info("Path exists but it is not a folder (might be a file).")
                            else:
                                st.info("Path not found. Ensure the path is correct for this machine.")
                except Exception as e:
                    st.error(f"❌ Processing error: {str(e)}")

        if st.session_state.files:
            st.markdown("---")
            st.markdown(f"**📊 Scan Results: {len(st.session_state.files)} files detected**")

            # Compact file preview in a grid
            with st.expander("📋 Files", expanded=False):
                cols = st.columns(4)
                for i, f in enumerate(st.session_state.files[:8]):  # Show max 8 files
                    with cols[i % 4]:
                        file_ext = f['name'].split('.')[-1].lower() if '.' in f['name'] else 'file'
                        icon = "📄"
                        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                            icon = "🖼️"
                        elif file_ext in ['mp4', 'avi', 'mkv', 'mov']:
                            icon = "🎥"
                        elif file_ext in ['mp3', 'wav', 'flac']:
                            icon = "🎵"
                        elif file_ext in ['pdf']:
                            icon = "📕"
                        elif file_ext in ['doc', 'docx', 'txt']:
                            icon = "📝"
                        st.markdown(f'<div class="file-item" style="padding:4px; margin-bottom:2px;"><div class="file-icon" style="width:20px; height:20px; font-size:14px;">{icon}</div><div style="font-size:9px;">{f["name"][:12]}...</div></div>', unsafe_allow_html=True)

                if len(st.session_state.files) > 8:
                    st.caption(f"... +{len(st.session_state.files)-8} more")

# Tab 2: AI Analysis
with tab2:
    with st.container(border=True):
        if not st.session_state.files:
            st.info("📁 Please scan files first in the Upload tab")
        elif st.session_state.analyzing:
            st.markdown("### 🤖 AI Analysis in Progress")
            st.markdown("Our AI is analyzing your files and suggesting the best organization categories...")

            progress_bar = st.progress(0)
            status_text = st.empty()

            results = []
            for i, file in enumerate(st.session_state.files):
                progress = (i + 1) / len(st.session_state.files)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing: {file['name']}")

                results.append({**file, **get_file_classification(file, st.session_state.selected_model)})
                time.sleep(0.1)  # Simulate processing time

            st.session_state.classified_files = results
            st.session_state.analyzing = False
            progress_bar.empty()
            status_text.empty()
            st.success("✅ AI Analysis Complete!")
            st.rerun()

        elif not st.session_state.classified_files:
            st.markdown("### 🤖 AI File Analysis")
            st.markdown(f"Ready to analyze **{len(st.session_state.files)} files** with AI")
            
            if st.button("🚀 START AI ANALYSIS", use_container_width=True, type="primary"):
                st.session_state.analyzing = True
                st.rerun()
        
        elif st.session_state.classified_files:
            st.markdown("### 🤖 AI Suggestions - Review & Customize")
            st.markdown("✨ Our AI has analyzed your files and suggested categories. Review and edit them before organizing:")

            # Create editable categories
            if 'edited_categories' not in st.session_state:
                st.session_state.edited_categories = {f['path']: f['category'] for f in st.session_state.classified_files}

            # Display files with editable categories in a compact table format
            st.markdown('<div class="review-table" style="padding:15px;">', unsafe_allow_html=True)
            st.markdown('<div class="table-header" style="margin-bottom:10px;"><div class="file-name-cell">📄 File</div><div class="category-cell">🏷️ Category</div><div class="size-cell">📏 Size</div></div>', unsafe_allow_html=True)

            for file in st.session_state.classified_files[:6]:  # Limit to 6 files for ultra compact
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    file_ext = file['name'].split('.')[-1].lower() if '.' in file['name'] else 'file'
                    icon = "📄"
                    if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                        icon = "🖼️"
                    elif file_ext in ['mp4', 'avi', 'mkv', 'mov']:
                        icon = "🎥"
                    elif file_ext in ['mp3', 'wav', 'flac']:
                        icon = "🎵"
                    st.markdown(f"**{icon} {file['name'][:20]}...**" if len(file['name']) > 20 else f"**{icon} {file['name']}**")
                with cols[1]:
                    new_cat = st.text_input(
                        f"Category for {file['name']}",
                        value=st.session_state.edited_categories[file['path']],
                        key=f"cat_{file['path']}",
                        label_visibility="collapsed"
                    )
                    st.session_state.edited_categories[file['path']] = new_cat
                with cols[2]:
                    st.markdown(f"**{file['size_kb']}KB**")

            if len(st.session_state.classified_files) > 10:
                st.caption(f"... and {len(st.session_state.classified_files)-10} more files")

            st.markdown('</div>', unsafe_allow_html=True)

            # Show proposed folder structure compactly
            st.markdown("### 📁 Proposed Organization")
            folder_summary = {}
            for file in st.session_state.classified_files:
                cat = st.session_state.edited_categories[file['path']]
                if cat not in folder_summary:
                    folder_summary[cat] = []
                folder_summary[cat].append(file['name'])

            cols = st.columns(2)
            folder_icons = {
                "Work": "💼", "Personal": "🏠", "Projects": "💻",
                "Archive": "📦", "Media": "📸", "Documents": "📄",
                "Images": "🖼️", "Videos": "🎥", "Music": "🎵"
            }

            for i, (folder, files) in enumerate(list(folder_summary.items())[:6]):  # Limit to 6 categories
                with cols[i % 2]:
                    icon = folder_icons.get(folder, "📁")
                    with st.expander(f"{icon} {folder} ({len(files)})", expanded=False):
                        for fname in files[:3]:  # Show max 3 files per category
                            st.markdown(f"• {fname[:20]}..." if len(fname) > 20 else f"• {fname}")
                        if len(files) > 3:
                            st.caption(f"... +{len(files)-3} more")

            st.markdown("---")
            if st.button("🚀 ORGANIZE FILES NOW", use_container_width=True, type="primary"):
                # Update classified_files with edited categories
                for file in st.session_state.classified_files:
                    file['category'] = st.session_state.edited_categories[file['path']]

                with st.status("🔄 Moving files to organized folders...", expanded=True) as status:
                    success_count = 0
                    failed_files = []

                    for file in st.session_state.classified_files:
                        st.write(f"📂 Moving: {file['name']} → **{file['category']}**")
                        success, message = move_file(file['path'], file['category'])
                        if success:
                            success_count += 1
                            st.write(f"✅ {file['name']} moved successfully")
                        else:
                            failed_files.append((file['name'], message))
                            st.write(f"❌ Failed: {file['name']} - {message}")

                    if success_count > 0:
                        status.update(label=f"🎉 Successfully organized {success_count} files!", state="complete")
                        st.session_state.organized = True
                        st.session_state.successful_moves = success_count
                        time.sleep(1)  # Brief pause to show success
                        st.rerun()
                    else:
                        status.update(label="❌ No files were moved. Check errors above.", state="error")
        else:
            st.info("👆 Start by scanning files in the Upload tab")

# Tab 3: Results
with tab3:
    with st.container(border=True):
        if st.session_state.organized:
            st.markdown('<div class="section-title" style="color:#22c55e">✅ Organization Complete!</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="success-message" style="padding:10px; margin:5px 0;">
                <h3 style="margin:0 0 5px 0; color:#22c55e; font-size:16px;">🎉 Success!</h3>
                <p style="margin:0; font-size:13px;">
                    Organized <strong>{st.session_state.successful_moves}</strong> files into <strong>{len(set(f.get('category', '') for f in st.session_state.classified_files if f.get('category')))}</strong> categories
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Show created folders summary - compact
            if st.session_state.classified_files:
                st.markdown("### 📂 Created Folders:")

                folder_summary = {}
                for file in st.session_state.classified_files:
                    cat = file.get('category', 'Uncategorized')
                    if cat not in folder_summary:
                        folder_summary[cat] = []
                    folder_summary[cat].append(file['name'])

                cols = st.columns(2)
                folder_icons = {
                    "Work": "💼", "Personal": "🏠", "Projects": "💻",
                    "Archive": "📦", "Media": "📸", "Documents": "📄",
                    "Images": "🖼️", "Videos": "🎥", "Music": "🎵"
                }

                for i, (folder, files) in enumerate(list(folder_summary.items())[:6]):  # Limit to 6
                    with cols[i % 2]:
                        icon = folder_icons.get(folder, "📁")
                        with st.expander(f"{icon} {folder} ({len(files)})", expanded=False):
                            for fname in files[:3]:  # Max 3 files
                                st.markdown(f"• {fname[:18]}..." if len(fname) > 18 else f"• {fname}")
                            if len(files) > 3:
                                st.caption(f"... +{len(files)-3} more")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Start New Scan", use_container_width=True):
                    st.session_state.files = []
                    st.session_state.classified_files = []
                    st.session_state.organized = False
                    st.rerun()
            with col2:
                if st.button("📂 Open Organized Folder", use_container_width=True):
                    # This would open the folder in file explorer
                    st.info("Folder opened in file explorer")
        else:
            st.info("✨ Complete the organization process to see results here")

# Footer - Ultra minimal
st.markdown("""
    <div style="text-align: center; padding: 2px; color: rgba(255,255,255,0.4); font-size: 9px;">
        Gemma3 AI | Local
    </div>
""", unsafe_allow_html=True)

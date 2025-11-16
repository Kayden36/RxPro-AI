# RXPro  
**An AI-Powered Patient ADE Safety PoS System**  

## 🚀 Overview

**RXPro** is a **Streamlit-based MVP** that combines:

- A **Point-of-Sale (POS) system** for pharmacy orders  
- **Inventory management**  
- **Customer & admin dashboards**  
- **AI-powered RX safety checks** using Google Gemini 2.5 Pro API  
- **TXT-based receipts** with optional browser PDF printing  

The system is designed to ensure **patient safety**, highlight **drug interactions**, and provide **counseling notes** while supporting standard POS operations.

## 💻 Features

### Customer Dashboard

- View **order history**  
- Create **new orders (POS)**  
- Use **latest POS order as RX input** for AI inference  
- Upload **RX files (.txt)** for inference  
- Dynamic **cart management** with subtotal and total calculation  
- Download **order receipts** (TXT)  

### Admin Dashboard

- **Manage drug inventory**  
- **View customer records**  
- **View all orders**  
- Add new drugs with expiry, usage, and quantity  

### AI RX Inference (Gemini 2.5 Pro)

- Dosage verification  
- Drug interaction checks  
- Allergy checks  
- Counseling notes for patients  
- Prescription compliance verification  
## 🛠 Tech Stack
- **Python 3.11+**  
- **Streamlit** for front-end & dashboard  
- **SQLite** for local database storage  
- **Pandas** for data handling  
- **Requests** & **Base64** for API integration  
## 📦 Installation
1. Clone the repository:
```bash
git clone https://github.com/<YOUR_USERNAME>/rxpro.git
cd rxpro
##Set Environment 
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
##install dependencies
pip install streamlit pandas requests
##run system
streamlit run app.py

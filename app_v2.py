import streamlit as st
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Vote Bot", layout="wide")
st.title("🤖 Automated Vote Sender")

# Sidebar configuration
st.sidebar.header("Configuration")

# Default request body
default_body = {
    "data": {
        "influencer_id": 1564,
        "category_id": 26
    },
    "recaptcha": "0cAFcWeA7TbuDpLiYMy0A8M5fIdTK7QBtnq97bHkr86LKwSBqSGlNGqjfgNcuQWHvRyxWdZ_dOEVoPTSNL3kRV4l66j-8hb8hDOtBEiWzYRDPDCea94-_9enbCQAoF3_d6rOinDIHdpaKNiNdhELCHHC3VAeUF-x24M5QwO0EEwbTLAMZp1msJM-ua2ZmdW_bkBq0qitRbyNi16SK8dIQ_HaukL7xoDcqAJrTbHKQ7PXnIcY3vHqkJY9szLJwFAop34eopNwDIELv56MLhUPgm7Mlmn0peyyEXRzvLnrRSwOjLhXi6zW1SIBbFtUYG71jSb-vo6u_dbY-xV5cTM3cpBGUkeYpM8ghvu2WlGan3lDUI2dVekV64Vn1Xog4cHbA_XAYrTfyMWQc3M2cH4TI39YDGsTXyfAUtEliQPqiMk5Eyjt-COhz2EW5Wsk6rGI_fDp3KIskj2boNZUpdFU0dFWeNp__jxtLm9k-mu0EY0mrqpULx1GxxPH32Zpdd_lVmkVV0CaQypRITtMsmaLQvCBAhkgbLiSwqZxFPJsywByRV5MNWvPdSK9Bh8JGNG3pxTWhucaGSo5JD4nehVZ_KVAlveDhzVJIOzgJ0B5DCSXB-theyf4jpeEldDcPtIu6yoG2jyzlXaEe7tuXm6T6ytch2hvBHiuSGBF81WDAw2ZO_JSlAVIg25Iobgrh8EMK9rMgWd_4ELIU64uqFTRIdZi3mBNK7de4u2LYR4thdJ0Ke_5pRoZpG0TLvSTxiK-HnfPkHCP2hffuwO1vjUu4GTRs1T_QeyT1LKeTstGgkElhAiI89TZsU77I3wkQrjqgBf6AbipNpc6PdXulfoAz7gvfW0h0_hMjHr02gQNmp3hMlHcce5F2U_XBSS3pl4G9Z2XUgsIOB9Jp13eKjSYBIBSxcqDJp4kEW6Bj6bSw6uzwnPw8TzxmZWqDLsXNuLnrFb5ApsTnhpAMiiGBoVycwb6CSQid0jmQP9VJF3Ot0sBM5b-kL45F3XCKJaJdBVze3APMSB47wPrQSdnHSjjlAedsCPif9pYpThmxBxutQNf68oPHn8OTZQDsmSc9EX0_K8w3XlRH-iEIfC5zRW-DadZUgzKMVkLDkeTEnP98eBKmk7-hE6vJRrZe0rBgH71d13CNiTIjRSbtTcxq6rHPNQp_6SJDsKp4qCdnMcuZ7_huO7Ri2YLul2Gv8cXO3tN5oaKTfSWL5xna42HuPFVHqioh-h6hUbDFI_9egKxlZ668gdjJytQuDQkiufZILr_aSQKUW6LSqmrqVAIqXkKE3fZZXbLqQK6Vptv3Q7aAJDOqPevfNM-bkEdt1wEUlz2K5QjFx8alTtT1rf7jL94cH2iuqFzsZyASUTP0-kvkiJLHHnVaV2nzZ5yQNkk4-4cbZZYyeEi3RX5Lc6-GEPr4TVuiPdGfMTkOGOnjU5K4GkGD9qGPLqVcJx5D2sShi7cO42r0c9Ds2fO7_k2XnIuCmcBooLZDe9ZJitrMCA4yY--FsSkOu4n5wO3l8uzdU8FQyNUvvAoe1dty0TE0tMkQ7QinxqRi1edLJHtvocKtJ830MY616eXIFbwHFhSy3KPJky2y92GRasDv0J8kHSllEhQJxk87qm5N7-Pm7nkpJAfWtGwggz_WwuCvZ4dlANd6wj3-bvWa9dtjm8Qdw-OHe923nugA3c3kjf1lUg7iEhbCPwIzxYZfo5X7062sw-Rn8psv7xvcDAs8x5Whm8OM45dkgBrSvOqeirmN5b14_SWk3wRiR5dqoEL84VwFvPjMbhbM6LGu9rg_W"
}

# Configuration parameters
MAX_WORKERS = st.sidebar.slider("Max Workers", 1, 100, 50, help="Nombre de threads simultanés")
BATCH_SIZE = st.sidebar.slider("Batch Size", 1, 5000, 1000, help="Nombre de requêtes par batch")
REQUEST_DELAY = st.sidebar.slider("Request Delay (ms)", 1, 100, 20, help="Délai entre les requêtes en millisecondes") / 1000
BATCH_DELAY = st.sidebar.slider("Batch Delay (s)", 1, 10, 2, help="Délai entre les batches en secondes")

# Editable JSON input
st.sidebar.subheader("Request Body")
body_text = st.sidebar.text_area("Edit JSON body:", json.dumps(default_body, indent=2), height=200)

try:
    body = json.loads(body_text)
except Exception as e:
    st.sidebar.error(f"Invalid JSON: {e}")
    st.stop()

# API URL input
api_url = st.sidebar.text_input("API URL", "https://api.digitalcreatorawards.com/api/influencer/vote")

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'global_success_count' not in st.session_state:
    st.session_state.global_success_count = 0
if 'global_failure_count' not in st.session_state:
    st.session_state.global_failure_count = 0
if 'batch_count' not in st.session_state:
    st.session_state.batch_count = 0
if 'status' not in st.session_state:
    st.session_state.status = "Ready"
if 'last_response' not in st.session_state:
    st.session_state.last_response = ""

def send_request(i):
    """Send a request with a small delay."""
    try:
        time.sleep(i * REQUEST_DELAY)
        response = requests.post(api_url, json=body, timeout=10)
        if response.status_code == 200:
            return True, response.text
        else:
            return False, f"{response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def run_batch():
    """Run a batch of requests"""
    success_count = 0
    failure_count = 0
    last_response = ""
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_request, i) for i in range(BATCH_SIZE)]
        
        for future in as_completed(futures):
            ok, result = future.result()
            if ok:
                success_count += 1
                last_response = result
            else:
                failure_count += 1
                last_response = result
    
    # Update session state
    st.session_state.global_success_count += success_count
    st.session_state.global_failure_count += failure_count
    st.session_state.batch_count += 1
    st.session_state.last_response = last_response
    
    return success_count, failure_count

# Control buttons
col1, col2, col3 = st.columns(3)

if col1.button("▶️ Start", type="primary", use_container_width=True):
    st.session_state.running = True
    st.session_state.status = "Running"

if col2.button("⏹️ Stop", type="secondary", use_container_width=True):
    st.session_state.running = False
    st.session_state.status = "Stopped"

if col3.button("🔄 Reset Counters", use_container_width=True):
    st.session_state.global_success_count = 0
    st.session_state.global_failure_count = 0
    st.session_state.batch_count = 0
    st.session_state.last_response = ""

# Status display
st.subheader("📊 Status")
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

status_col1.metric("Status", st.session_state.status)
status_col2.metric("Total Batches", st.session_state.batch_count)
status_col3.metric("✅ Success", st.session_state.global_success_count)
status_col4.metric("❌ Failures", st.session_state.global_failure_count)

# Progress bar
if st.session_state.running:
    progress_bar = st.progress(0)
else:
    progress_bar = st.progress(0)

# Last response
st.subheader("📋 Last Response")
response_placeholder = st.empty()

# Main execution loop
if st.session_state.running:
    while st.session_state.running:
        try:
            # Run batch
            success_count, failure_count = run_batch()
            
            # Update UI
            progress_bar.progress((st.session_state.batch_count % 10) / 10)
            
            # Display batch results
            st.info(f"**Batch {st.session_state.batch_count}:** ✅ {success_count} | ❌ {failure_count}")
            
            # Display last response
            try:
                response_placeholder.json(json.loads(st.session_state.last_response))
            except:
                response_placeholder.text(st.session_state.last_response)
            
            # Check for stop condition
            if not st.session_state.running:
                break
                
            # Delay between batches
            time.sleep(BATCH_DELAY)
            
        except Exception as e:
            st.error(f"Error in batch execution: {e}")
            st.session_state.running = False
            break

# Display configuration summary
st.sidebar.subheader("Current Configuration")
st.sidebar.write(f"**Workers:** {MAX_WORKERS}")
st.sidebar.write(f"**Batch Size:** {BATCH_SIZE}")
st.sidebar.write(f"**Request Delay:** {REQUEST_DELAY*1000}ms")
st.sidebar.write(f"**Batch Delay:** {BATCH_DELAY}s")

# Instructions
st.sidebar.info("""
**Instructions:**
1. Configurez les paramètres
2. Cliquez sur ▶️ Start
3. Surveillez les statistiques en temps réel
4. Cliquez sur ⏹️ Stop pour arrêter
""")

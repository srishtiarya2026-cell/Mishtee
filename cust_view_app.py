import gradio as gr
import pandas as pd
import requests
from supabase import create_client, Client

# --- 1. CONFIGURATION & ASSETS ---
SUPABASE_URL = "https://xynauxlynoxxdrbttlxm.supabase.co"
SUPABASE_KEY = "sb_publishable_nCoIYeX4nTpdy4D46P-dJA_DCSJdE_O"
LOGO_URL = "https://github.com/srishtiarya2026-cell/Mishtee/blob/main/Gemini_Generated_Image_oxqxy7oxqxy7oxqx.png?raw=true"
CSS_URL = "https://raw.githubusercontent.com/srishtiarya2026-cell/Mishtee/refs/heads/main/style.css"

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch Custom CSS from GitHub
try:
    response = requests.get(CSS_URL)
    mishtee_css = response.text if response.status_code == 200 else ""
except Exception:
    mishtee_css = ""

# --- 2. BACKEND FUNCTIONS ---

def get_trending_data():
    """Fetches top 4 products by order volume."""
    try:
        resp = supabase.table("orders").select("product_id, products(sweet_name)").execute()
        if not resp.data:
            return pd.DataFrame(columns=["Product", "Total Orders"])
        
        df_raw = pd.DataFrame(resp.data)
        df_raw['Product'] = df_raw['products'].apply(lambda x: x['sweet_name'] if x else "Unknown")
        trending_df = df_raw['Product'].value_counts().reset_index()
        trending_df.columns = ['Product', 'Total Orders']
        return trending_df.head(4)
    except Exception:
        return pd.DataFrame({"Product": ["Saffron Silk", "A2 Ancestry"], "Total Orders": [12, 8]})

def handle_login(phone_number):
    """Processes login, returns greeting and order history."""
    if not phone_number:
        return "Please enter a valid phone number.", pd.DataFrame(), get_trending_data()

    # Fetch Customer Name
    cust_resp = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
    
    if not cust_resp.data:
        greeting = "Namaste! Welcome to MishTee-Magic. It looks like you're new here!"
    else:
        name = cust_resp.data[0]['full_name']
        greeting = f"### Namaste, {name} ji! \n*Great to see you again.*"

    # Fetch Order History
    order_resp = supabase.table("orders").select(
        "order_id, order_date, products(sweet_name, price_per_kg), status"
    ).eq("cust_phone", phone_number).execute()

    if not order_resp.data:
        history_df = pd.DataFrame(columns=["Order ID", "Date", "Item", "Status"])
    else:
        orders_flat = []
        for o in order_resp.data:
            orders_flat.append({
                "Order ID": o.get('order_id'),
                "Date": o.get('order_date'),
                "Item": o['products']['sweet_name'] if o.get('products') else "Artisanal Sweet",
                "Status": o.get('status', 'Processing')
            })
        history_df = pd.DataFrame(orders_flat)

    return greeting, history_df, get_trending_data()

# --- 3. GRADIO UI LAYOUT ---

with gr.Blocks(css=mishtee_css, title="MishTee-Magic | Premium Indian Sweets") as app:
    
    # Header Section
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML(f"""
                <div style='text-align: center; padding: 20px;'>
                    <img src='{LOGO_URL}' width='200px' style='margin: 0 auto; display: block;'>
                    <p style='letter-spacing: 3px; font-weight: 300; margin-top: 15px;'>PURITY & HEALTH</p>
                </div>
            """)

    # Personalized Greeting Area
    with gr.Row():
        greeting_output = gr.Markdown("Welcome to the digital boutique of MishTee-Magic.", elem_id="greeting")

    # Content Section
    with gr.Row(equal_height=True):
        
        # Left: Login Sidebar
        with gr.Column(scale=1):
            gr.Markdown("### Personal Access")
            phone_input = gr.Textbox(label="Phone Number", placeholder="Enter registered mobile...")
            login_btn = gr.Button("REVEAL THE MAGIC", variant="primary")
            gr.HTML("<br><p style='font-size: 0.8em; opacity: 0.6;'>Experience A2 Purity & Organic Ingredients</p>")

        # Right: Tabbed Data
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("My Order History"):
                    history_table = gr.DataFrame(
                        headers=["Order ID", "Date", "Item", "Status"],
                        interactive=False,
                        wrap=True
                    )
                
                with gr.TabItem("Trending Today"):
                    trending_table = gr.DataFrame(
                        headers=["Product", "Total Orders"],
                        value=get_trending_data(), # Pre-populate
                        interactive=False
                    )

    # Event Trigger
    login_btn.click(
        fn=handle_login,
        inputs=[phone_input],
        outputs=[greeting_output, history_table, trending_table]
    )

    # Footer
    gr.HTML("""
        <div style='text-align: center; margin-top: 50px; padding: 20px; border-top: 1px solid #333333; opacity: 0.5;'>
            <p>MishTee-Magic Artisanal Mithai &copy; 2025 | Low-Sugar | A2 Milk | Organic</p>
        </div>
    """)

if __name__ == "__main__":
    app.launch()

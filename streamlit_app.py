import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
import os
warnings.filterwarnings('ignore')

st.set_page_config(page_title="CFO-in-a-Box", page_icon="📊", layout="wide")
st.title("📊 CFO-in-a-Box Financial Model")
st.markdown("---")

st.sidebar.header("⚙️ Company Settings")
COMPANY_NAME = st.sidebar.text_input("Company Name", "FDL Ltd")
CURRENCY = st.sidebar.text_input("Currency Symbol", "DZD")
PROJECTION_MONTHS = st.sidebar.slider("Projection Months", 12, 60, 36)
CASH_ON_HAND = st.sidebar.number_input("Cash on Hand", value=150000, step=1000)
CURRENT_MRR = st.sidebar.number_input("Current MRR", value=3000, step=100)
MRR_GROWTH_RATE = st.sidebar.slider("MRR Growth Rate %", 0, 30, 8) / 100
ONE_OFF_REVENUE = st.sidebar.number_input("One-off Revenue", value=0, step=500)

st.sidebar.markdown("---")
st.sidebar.header("📌 Fixed Costs")
sal = st.sidebar.number_input("Salaries", value=8000, step=100)
rent = st.sidebar.number_input("Rent", value=1200, step=100)
soft = st.sidebar.number_input("Software", value=400, step=50)
ins = st.sidebar.number_input("Insurance", value=150, step=50)
legal = st.sidebar.number_input("Legal", value=300, step=50)

fixed_costs = {
    "Salaries": sal,
    "Rent": rent,
    "Software": soft,
    "Insurance": ins,
    "Legal": legal,
}

st.sidebar.markdown("---")
st.sidebar.header("📌 Variable Costs")
mkt = st.sidebar.number_input("Marketing", value=1500, step=100)
trv = st.sidebar.number_input("Travel", value=300, step=50)
con = st.sidebar.number_input("Contractors", value=800, step=100)
cld = st.sidebar.number_input("Cloud", value=250, step=50)
evt = st.sidebar.number_input("Events", value=200, step=50)

variable_costs = {
    "Marketing": mkt,
    "Travel": trv,
    "Contractors": con,
    "Cloud": cld,
    "Events": evt,
}
one_time_costs = {
    3: {"Equipment": 5000},
    8: {"Legal Filing": 2500},
    12: {"Conference": 1800},
}

planned_hires = {
    4: 3500,
    9: 4000,
    14: 3000,
}

frugal_cuts = {
    "Marketing": 0.70,
    "Travel": 1.00,
    "Contractors": 0.50,
    "Events": 1.00,
}

GROWTH_AD_MULTIPLIER = 2.5
GROWTH_MRR_BOOST = 0.04

def run_scenario(scenario):
    records = []
    cash = CASH_ON_HAND
    mrr = CURRENT_MRR
    cumulative_hires_cost = 0
    for month in range(1, PROJECTION_MONTHS + 1):
        growth = MRR_GROWTH_RATE + (GROWTH_MRR_BOOST if scenario == 'growth' else 0)
        if month > 1:
            mrr = mrr * (1 + growth)
        one_off = ONE_OFF_REVENUE if month == 1 else 0
        total_revenue = mrr + one_off
        total_fixed = sum(fixed_costs.values())
        total_variable = 0
        for name, amount in variable_costs.items():
            if scenario == 'frugal' and name in frugal_cuts:
                amount = amount * (1 - frugal_cuts[name])
            elif scenario == 'growth' and name == 'Marketing':
                amount = amount * GROWTH_AD_MULTIPLIER
            total_variable += amount
        ot_costs = 0
        ot_label = ""
        if month in one_time_costs:
            for label, amt in one_time_costs[month].items():
                ot_costs += amt
                ot_label += label + " "
        hire_cost = 0
        if scenario == 'growth':
            if month in planned_hires:
                cumulative_hires_cost += planned_hires[month]
            hire_cost = cumulative_hires_cost
        total_costs = total_fixed + total_variable + ot_costs + hire_cost
        net_cash_flow = total_revenue - total_costs
        cash = cash + net_cash_flow
        burn_rate = total_costs - total_revenue if total_costs > total_revenue else 0
        records.append({
            'Month': month,
            'MRR': round(mrr, 2),
            'Total Revenue': round(total_revenue, 2),
            'Fixed Costs': round(total_fixed, 2),
            'Variable Costs': round(total_variable, 2),
            'One-Time Costs': round(ot_costs, 2),
            'Hire Costs': round(hire_cost, 2),
            'Total Costs': round(total_costs, 2),
            'Net Cash Flow': round(net_cash_flow, 2),
            'Cash Balance': round(cash, 2),
            'Burn Rate': round(burn_rate, 2),
            'One-Time Label': ot_label.strip(),
        })
    return pd.DataFrame(records)

def calc_runway(df):
    depleted = df[df['Cash Balance'] <= 0]
    if depleted.empty:
        return "Beyond " + str(PROJECTION_MONTHS) + " months"
    return str(depleted.iloc[0]['Month']) + " months"

df_sq = run_scenario('status_quo')
df_fr = run_scenario('frugal')
df_gr = run_scenario('growth')
st.markdown("## 🏁 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cash on Hand", CURRENCY + str(int(CASH_ON_HAND)))
col2.metric("Current MRR", CURRENCY + str(int(CURRENT_MRR)))
col3.metric("Fixed Costs/mo", CURRENCY + str(sum(fixed_costs.values())))
col4.metric("Variable Costs/mo", CURRENCY + str(sum(variable_costs.values())))

col5, col6, col7 = st.columns(3)
col5.metric("Runway - Status Quo", calc_runway(df_sq))
col6.metric("Runway - Frugal", calc_runway(df_fr))
col7.metric("Runway - Growth", calc_runway(df_gr))

break_sq = df_sq[df_sq['Net Cash Flow'] >= 0]
break_mo = int(break_sq.iloc[0]['Month']) if not break_sq.empty else 0
sq_burn = df_sq[df_sq['Burn Rate'] > 0]['Burn Rate'].mean()
sq_burn = sq_burn if not np.isnan(sq_burn) else 0

col8, col9 = st.columns(2)
col8.metric("Breakeven Month", "Month " + str(break_mo))
col9.metric("Avg Monthly Burn", CURRENCY + str(int(sq_burn)))

st.markdown("---")
st.markdown("## 📈 Cash Balance Over Time")
fig1, ax1 = plt.subplots(figsize=(12, 4))
months = df_sq['Month']
ax1.plot(months, df_sq['Cash Balance'], color='#2c3e50', lw=2.5, label='Status Quo', marker='o', markersize=3)
ax1.plot(months, df_fr['Cash Balance'], color='#27ae60', lw=2.5, label='Frugal', marker='s', markersize=3)
ax1.plot(months, df_gr['Cash Balance'], color='#2980b9', lw=2.5, label='Growth', marker='^', markersize=3)
ax1.axhline(y=0, color='#e74c3c', linestyle='--', lw=1.5, alpha=0.7, label='Zero Cash')
ax1.set_xlabel('Month')
ax1.set_ylabel('Cash Balance')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_facecolor('#f8f9fa')
st.pyplot(fig1)
plt.close()

st.markdown("## 📊 MRR Growth")
fig2, ax2 = plt.subplots(figsize=(12, 3))
ax2.plot(months, df_sq['MRR'], color='#2c3e50', lw=2, label='Status Quo')
ax2.plot(months, df_gr['MRR'], color='#2980b9', lw=2, label='Growth')
ax2.plot(months, df_fr['MRR'], color='#27ae60', lw=2, label='Frugal')
ax2.set_xlabel('Month')
ax2.set_ylabel('MRR')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_facecolor('#f8f9fa')
st.pyplot(fig2)
plt.close()

st.markdown("## 🔥 Monthly Burn Rate")
fig3, ax3 = plt.subplots(figsize=(12, 3))
bar_colors = ['#e74c3c' if b > 0 else '#27ae60' for b in df_sq['Burn Rate']]
ax3.bar(months, df_sq['Burn Rate'], color=bar_colors, alpha=0.8)
ax3.set_xlabel('Month')
ax3.set_ylabel('Burn Rate')
ax3.grid(True, alpha=0.3, axis='y')
ax3.set_facecolor('#f8f9fa')
st.pyplot(fig3)
plt.close()
st.markdown("## 💰 Net Cash Flow Comparison")
fig4, ax4 = plt.subplots(figsize=(12, 3))
ax4.bar(months - 0.25, df_sq['Net Cash Flow'], 0.25, label='Status Quo', color='#2c3e50', alpha=0.8)
ax4.bar(months, df_fr['Net Cash Flow'], 0.25, label='Frugal', color='#27ae60', alpha=0.8)
ax4.bar(months + 0.25, df_gr['Net Cash Flow'], 0.25, label='Growth', color='#2980b9', alpha=0.8)
ax4.axhline(y=0, color='black', lw=0.8, alpha=0.5)
ax4.set_xlabel('Month')
ax4.set_ylabel('Net Cash Flow')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')
ax4.set_facecolor('#f8f9fa')
st.pyplot(fig4)
plt.close()

st.markdown("## 🍕 Cost Breakdown")
fig5, ax5 = plt.subplots(figsize=(6, 6))
cost_labels = list(fixed_costs.keys()) + list(variable_costs.keys())
cost_vals = list(fixed_costs.values()) + list(variable_costs.values())
wedge_colors = plt.cm.Set3(np.linspace(0, 1, len(cost_labels)))
ax5.pie(cost_vals, labels=None, explode=[0.03]*len(cost_labels), colors=wedge_colors, autopct='%1.0f%%', pctdistance=0.8, startangle=90, textprops={'fontsize': 8})
ax5.legend(cost_labels, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=8)
st.pyplot(fig5)
plt.close()

st.markdown("---")
st.markdown("## 📋 Month-by-Month Data")
tab1, tab2, tab3 = st.tabs(["Status Quo", "Frugal", "Growth"])
cols = ['Month', 'MRR', 'Total Revenue', 'Total Costs', 'Net Cash Flow', 'Cash Balance', 'Burn Rate']
with tab1:
    st.dataframe(df_sq[cols], use_container_width=True)
with tab2:
    st.dataframe(df_fr[cols], use_container_width=True)
with tab3:
    st.dataframe(df_gr[cols], use_container_width=True)
st.markdown("---")
st.markdown("## 📥 Download Your Files")

excel_path = os.path.expanduser('~/CFO_Data.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_sq.drop(columns=['One-Time Label']).to_excel(writer, sheet_name='Status Quo', index=False)
    df_fr.drop(columns=['One-Time Label']).to_excel(writer, sheet_name='Frugal', index=False)
    df_gr.drop(columns=['One-Time Label']).to_excel(writer, sheet_name='Growth', index=False)
    summary = pd.DataFrame({
        'Metric': ['Company', 'Cash', 'MRR', 'Fixed/mo', 'Variable/mo', 'Runway SQ', 'Runway Frugal', 'Runway Growth'],
        'Value': [COMPANY_NAME, CURRENCY+str(CASH_ON_HAND), CURRENCY+str(CURRENT_MRR), CURRENCY+str(sum(fixed_costs.values())), CURRENCY+str(sum(variable_costs.values())), calc_runway(df_sq), calc_runway(df_fr), calc_runway(df_gr)]
    })
    summary.to_excel(writer, sheet_name='Summary', index=False)

with open(excel_path, 'rb') as f:
    st.download_button(
        label="📥 Download Excel File",
        data=f,
        file_name="CFO_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.caption("CFO-in-a-Box — For planning purposes only. Not financial advice.")

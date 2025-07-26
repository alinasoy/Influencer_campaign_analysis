# HealthKart Influencer Campaign Dashboard with ROI, ROAS, Payout Tracking, and Persona Insights

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import streamlit as st
import plotly.express as px
import zipfile
import io

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# 1. Generate Influencer Data
platforms = ['Instagram', 'YouTube', 'Twitter']
categories = ['Fitness', 'Lifestyle', 'Nutrition', 'Bodybuilding']
genders = ['Male', 'Female', 'Other']
influencers = pd.DataFrame({
    'ID': range(1, 21),
    'name': [f'Influencer_{i}' for i in range(1, 21)],
    'category': np.random.choice(categories, 20),
    'gender': np.random.choice(genders, 20),
    'follower_count': np.random.randint(10000, 500000, 20),
    'platform': np.random.choice(platforms, 20)
})

# 2. Generate Post Data
posts = []
for i in range(100):
    inf_id = np.random.choice(influencers['ID'])
    posts.append({
        'influencer_id': inf_id,
        'platform': influencers[influencers['ID'] == inf_id]['platform'].values[0],
        'date': datetime.today() - timedelta(days=np.random.randint(1, 60)),
        'URL': f'https://post.url/{i}',
        'caption': f'Check out our new product! #{i}',
        'reach': np.random.randint(1000, 100000),
        'likes': np.random.randint(100, 10000),
        'comments': np.random.randint(10, 1000),
    })
posts = pd.DataFrame(posts)

# 3. Generate Tracking Data
tracking_data = pd.DataFrame({
    'source': ['influencer'] * 200,
    'campaign': np.random.choice(['Campaign_A', 'Campaign_B', 'Campaign_C'], 200),
    'influencer_id': np.random.choice(influencers['ID'], 200),
    'user_id': np.random.randint(1000, 2000, 200),
    'product': np.random.choice(['MuscleBlaze', 'HKVitals', 'Gritzo'], 200),
    'date': [datetime.today() - timedelta(days=np.random.randint(1, 60)) for _ in range(200)],
    'orders': np.random.randint(1, 5, 200),
    'revenue': np.round(np.random.uniform(100, 2000, 200), 2)
})

# 4. Payout Calculation
payouts = pd.DataFrame({
    'influencer_id': influencers['ID'],
    'basis': np.random.choice(['post', 'order'], 20),
    'rate': np.random.randint(100, 5000, 20),
})
payouts['orders'] = tracking_data.groupby('influencer_id')['orders'].sum().reindex(payouts['influencer_id']).fillna(0).astype(int).values
payouts['total_payout'] = np.where(
    payouts['basis'] == 'order',
    payouts['orders'] * payouts['rate'],
    posts.groupby('influencer_id').size().reindex(payouts['influencer_id']).fillna(1).astype(int).values * payouts['rate']
)
#Save datafram to CSV file
influencers.to_csv('influencers.csv', index=False)
posts.to_csv('posts.csv', index=False)
tracking_data.to_csv('tracking_data.csv', index=False)
payouts.to_csv('payouts.csv', index=False)

#Load CSV File
influencers = pd.read_csv("influencers.csv")
posts = pd.read_csv("posts.csv")
tracking_data = pd.read_csv("tracking_data.csv")
payouts = pd.read_csv("payouts.csv")

# Streamlit Setup
st.set_page_config(layout="wide")
st.title("📣 HealthKart Influencer Campaign Dashboard")

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
platforms = st.sidebar.multiselect("Select Platform", influencers["platform"].unique(), default=influencers["platform"].unique())
categories = st.sidebar.multiselect("Select Category", influencers["category"].unique(), default=influencers["category"].unique())
products = st.sidebar.multiselect("Select Product", tracking_data["product"].unique(), default=tracking_data["product"].unique())
genders = st.sidebar.multiselect("Select Gender", influencers["gender"].unique(), default=influencers["gender"].unique())

# Apply Filters
filtered_influencers = influencers[
    influencers["platform"].isin(platforms) &
    influencers["category"].isin(categories) &
    influencers["gender"].isin(genders)
]
filtered_tracking = tracking_data[
    tracking_data["product"].isin(products) &
    tracking_data["influencer_id"].isin(filtered_influencers["ID"])
]

# Merge Data
merged = pd.merge(filtered_tracking, payouts, on="influencer_id", how="left")
merged = pd.merge(merged, influencers[['ID', 'name', 'category', 'gender']], left_on='influencer_id', right_on='ID', how='left')

# KPIs
total_revenue = merged["revenue"].sum()
total_orders = merged["orders_x"].sum()
total_payout = merged["total_payout"].sum()
roas = total_revenue / total_payout if total_payout else 0
roi = ((total_revenue - total_payout) / total_payout) * 100 if total_payout else 0

# Show KPIs
st.subheader("📊 Campaign Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
col2.metric("Total Orders", f"{total_orders}")
col3.metric("ROAS", f"{roas:.2f}")
col4.metric("ROI (%)", f"{roi:.2f}%")

# Campaign Performance
st.subheader("📌 Campaign Performance")
campaign_summary = filtered_tracking.groupby("campaign").agg({"orders": "sum", "revenue": "sum"}).reset_index()
campaign_summary["ROAS"] = campaign_summary["revenue"] / total_payout
campaign_summary["ROI (%)"] = ((campaign_summary["revenue"] - (total_payout / len(campaign_summary))) / (total_payout / len(campaign_summary))) * 100
st.dataframe(campaign_summary)
# Sort by revenue descending
campaign_summary = campaign_summary.sort_values(by="revenue", ascending=True)

# Format revenue for labels
campaign_summary["Actual_revenue"] = campaign_summary["revenue"].apply(lambda x: f"₹{x:,.2f}")

# Plot the bar chart
fig1 = px.bar(
    campaign_summary,
    x="campaign",
    y="revenue",
    title="Revenue by Campaign",
    text="Actual_revenue"
)

# Position labels on top
fig1.update_traces(textposition="outside")

# Display chart
st.plotly_chart(fig1, use_container_width=True)



# Top Influencers by ROAS
st.subheader("🏆 Top 10 Influencers by ROAS")
influencer_perf = merged.groupby(["name", "influencer_id"]).agg({"revenue": "sum", "total_payout": "mean"}).reset_index()
influencer_perf = influencer_perf[influencer_perf["total_payout"] != 0]
influencer_perf["ROAS"] = influencer_perf["revenue"] / influencer_perf["total_payout"]
top_influencers = influencer_perf.sort_values("ROAS", ascending=False).head(10)
top_influencers["ROAS_Display"] = top_influencers["ROAS"].apply(lambda x: f"{x:,.2f}")
st.dataframe(top_influencers)
# Plot bar chart
fig2 = px.bar(
    top_influencers,
    x="name",
    y="ROAS",
    text="ROAS_Display",
    title="Top 10 Influencers by ROAS",
    category_orders={"name": top_influencers["name"].tolist()}
)

# Show values above bars
fig2.update_traces(textposition="outside")

# Improve layout
fig2.update_layout(
    xaxis_title="Influencer Name",
    yaxis_title="ROAS",
    yaxis=dict(tickformat=".2f"),
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

# Display chart
st.plotly_chart(fig2, use_container_width=True)


# Bottom Influencers by ROAS (Lowest to Highest)
st.subheader("📉 Bottom 10 Influencers by ROAS")

# Group and calculate ROAS
influencer_perf = merged.groupby(["name", "influencer_id"]).agg({"revenue": "sum","total_payout": "mean"}).reset_index()

# Avoid division by zero
influencer_perf = influencer_perf[influencer_perf["total_payout"] != 0]

# Calculate ROAS
influencer_perf["ROAS"] = influencer_perf["revenue"] / influencer_perf["total_payout"]

# Sort ROAS ascending and get bottom 10
bottom_influencers = influencer_perf.sort_values("ROAS", ascending=True).head(10)

# Format ROAS for display
bottom_influencers["ROAS_Display"] = bottom_influencers["ROAS"].apply(lambda x: f"{x:,.2f}")

# Show DataFrame
st.dataframe(bottom_influencers)

# Plot bar chart
fig = px.bar(
    bottom_influencers,
    x="name",
    y="ROAS",
    text="ROAS_Display",
    title="Bottom 10 Influencers by ROAS",
)

# Show values above bars
fig.update_traces(textposition="outside")

# Improve layout
fig.update_layout(
    xaxis_title="Influencer Name",
    yaxis_title="ROAS",
    yaxis=dict(tickformat=".2f"),
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

# Display chart
st.plotly_chart(fig, use_container_width=True)


# Persona Insights
st.subheader("🧬 Best Performing Personas")

# Grouping the data
persona = merged.groupby(["category", "gender"]).agg({"revenue": "sum"}).reset_index()

# Calculate percentage of total revenue
total_rev = persona["revenue"].sum()
persona["percent"] = (persona["revenue"] / total_rev * 100).round(2)

# Add customdata for revenue and percent
fig3 = px.sunburst(
    persona,
    path=["category", "gender"],
    values="revenue",
    custom_data=["revenue", "percent"],
    title="Revenue by Persona"
)

# Custom hovertemplate
fig3.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>" +
        "Revenue: ₹%{customdata[0]:,.0f}<br>" +
        "Share: %{customdata[1]}%"
    )
)

st.plotly_chart(fig3, use_container_width=True)




# Post Engagement
st.subheader("📸 Post Engagement Overview")
post_engagement = posts.groupby("influencer_id").agg({"reach": "sum", "likes": "sum", "comments": "sum"}).reset_index()
post_engagement = pd.merge(post_engagement, influencers[["ID", "name"]], left_on="influencer_id", right_on="ID", how="left")
top_engaged = post_engagement.sort_values("reach", ascending=False).head(10)
st.dataframe(top_engaged[["name", "reach", "likes", "comments"]])

# 💸 Payout Tracking
st.subheader("💸 Payout Tracking")
payout_summary = payouts.merge(influencers[['ID', 'name']], left_on='influencer_id', right_on='ID', how='left')
payout_summary = payout_summary[['name', 'basis', 'rate', 'orders', 'total_payout']]
st.dataframe(payout_summary.sort_values("total_payout", ascending=False))


# Optional Download: All Insight Tables
with st.expander("⬇️ Download All Insights (CSV ZIP)"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("Campaign_Performance.csv", campaign_summary.to_csv(index=False))
        zip_file.writestr("Top_Influencers.csv", top_influencers.to_csv(index=False))
        zip_file.writestr("Best_Personas.csv", persona.to_csv(index=False))
        zip_file.writestr("Post_Engagement_Overview.csv", top_engaged[["name", "reach", "likes", "comments"]].to_csv(index=False))
        zip_file.writestr("Payout_Tracking.csv", payout_summary.to_csv(index=False))


    st.download_button(
        label="📥 Download All Insights as ZIP",
        data=buffer.getvalue(),
        file_name="HealthKart_Influencer_Insights.zip",
        mime="application/zip"
    )


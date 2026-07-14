import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

st.set_page_config(page_title="Statistical Analysis Engine", layout="wide")

# ==========================================
# 1. DATA GENERATOR
# ==========================================
@st.cache_data
def generate_mock_data(seed=None):
    if seed:
        np.random.seed(seed)
    
    n_samples = 200
    
    # Feature A: Base metric (e.g., Usage)
    feature_a = np.random.normal(50, 15, n_samples)
    
    # Feature B: Strongly positively correlated with A (e.g., Revenue)
    feature_b = feature_a * 1.5 + np.random.normal(0, 10, n_samples)
    
    # Feature C: Complete random noise
    feature_c = np.random.uniform(0, 100, n_samples)
    
    # Feature D: Base metric 2
    feature_d = np.random.normal(100, 25, n_samples)
    
    # Feature E: Negatively correlated with D (e.g., Latency vs Throughput)
    feature_e = 500 - (feature_d * 2) + np.random.normal(0, 20, n_samples)
    
    return pd.DataFrame({
        "Feature A (Base)": feature_a,
        "Feature B (Pos Correlated to A)": feature_b,
        "Feature C (Random Noise)": feature_c,
        "Feature D (Base 2)": feature_d,
        "Feature E (Neg Correlated to D)": feature_e
    })

# Initialize Session State for Data Regeneration
if 'data_seed' not in st.session_state:
    st.session_state.data_seed = 42

df = generate_mock_data(st.session_state.data_seed)

# ==========================================
# 2. DASHBOARD UI
# ==========================================
st.title("📊 Generic Statistical Analysis Engine")
st.markdown("Explore Data Distributions, Correlations, and Dimensionality Reduction.")

# Control Panel
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    analysis_type = st.selectbox(
        "Select Analysis Type", 
        ["Data Distribution (Histogram)", "Scatter Plot (2D)", "Correlation Heatmap", "Principal Component Analysis (PCA)"]
    )

with col2:
    if analysis_type in ["Data Distribution (Histogram)", "Scatter Plot (2D)"]:
        x_axis = st.selectbox("X-Axis Variable", df.columns, index=0)
    else:
        st.empty() # Placeholder to keep layout clean

with col3:
    if analysis_type == "Scatter Plot (2D)":
        y_axis = st.selectbox("Y-Axis Variable", df.columns, index=1)
    else:
        st.empty()

if st.button("🔄 Regenerate Random Dataset"):
    st.session_state.data_seed += 1
    st.rerun()

st.divider()

# ==========================================
# 3. DYNAMIC CHART RENDERING
# ==========================================
fig, ax = plt.subplots(figsize=(10, 6))

if analysis_type == "Data Distribution (Histogram)":
    st.subheader(f"Distribution of {x_axis}")
    sns.histplot(df[x_axis], kde=True, ax=ax, color='#4C72B0')
    ax.set_title(f"Histogram & Density of {x_axis}")
    st.pyplot(fig)

elif analysis_type == "Scatter Plot (2D)":
    st.subheader(f"{y_axis} vs {x_axis}")
    sns.regplot(data=df, x=x_axis, y=y_axis, ax=ax, scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
    ax.set_title(f"Scatter Plot with Linear Regression Trendline")
    st.pyplot(fig)

elif analysis_type == "Correlation Heatmap":
    st.subheader("Pearson Correlation Matrix")
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0, ax=ax, fmt=".2f")
    ax.set_title("Feature-to-Feature Correlation Strength")
    st.pyplot(fig)

elif analysis_type == "Principal Component Analysis (PCA)":
    st.subheader("PCA: 2D Dimensionality Reduction")
    # Standardize and compute PCA
    from sklearn.preprocessing import StandardScaler
    scaled_data = StandardScaler().fit_transform(df)
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    
    # Plot PC1 vs PC2
    sns.scatterplot(x=pca_result[:,0], y=pca_result[:,1], ax=ax, alpha=0.7)
    ax.set_xlabel(f"Principal Component 1 ({pca.explained_variance_ratio_[0]*100:.1f}% Variance)")
    ax.set_ylabel(f"Principal Component 2 ({pca.explained_variance_ratio_[1]*100:.1f}% Variance)")
    ax.set_title("PCA: Compressing 5 Variables into 2 Dimensions")
    st.pyplot(fig)
    
    st.info("💡 **What is this?** PCA takes all 5 features and squashes them down into 2 new mathematical axes (Principal Components) while trying to preserve as much variance/spread as possible. The percentages show how much of the original data's story is captured by each axis.")

st.divider()

# ==========================================
# 4. STATIC BASIC STATISTICS
# ==========================================
st.subheader("📈 Basic Statistics (Raw Data)")
# Transpose the describe() output so features are rows, matching your terminal screenshot style
st.dataframe(df.describe().T, use_container_width=True)




def main():
    print("Hello from sa4dst!")


if __name__ == "__main__":
    main()

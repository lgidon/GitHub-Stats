import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="GitHub DORA Metrics & Engineering Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling Fixes
st.markdown("""
    <style>
        .block-container { 
            padding-top: 2rem; 
        }
        
        /* Metric Box Container */
        div[data-testid="stMetric"] {
            background-color: #f0f4f9 !important;
            padding: 18px !important;
            border-radius: 12px !important;
            border-left: 5px solid #0969da !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        /* Metric Label (e.g. Total PRs) */
        div[data-testid="stMarkdownContainer"] p {
            color: #475467 !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }

        /* Metric Value (the big numbers) */
        div[data-testid="stMetricValue"] div {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING (DuckDB Engine)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    conn = duckdb.connect(database=':memory:')
    
    # Query Parquet exports directly
    prs_df = conn.execute("SELECT * FROM read_parquet('data/exports/fct_pull_requests.parquet')").df()
    authors_df = conn.execute("SELECT * FROM read_parquet('data/exports/dim_authors.parquet')").df()
    
    # Pre-process dates if present
    if 'created_at' in prs_df.columns:
        prs_df['created_at'] = pd.to_datetime(prs_df['created_at'])
        prs_df['created_date'] = prs_df['created_at'].dt.date
        
    return prs_df, authors_df

try:
    prs_df, authors_df = load_data()
except Exception as e:
    st.error(f"Error loading Parquet files: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Analytics Dashboard")
st.sidebar.markdown("---")

# Find the repository column name (handles common variations)
repo_col = next((col for col in ['repository_name', 'repo_name', 'repository', 'repo'] if col in prs_df.columns), None)

if repo_col:
    # Extract unique repositories sorted alphabetically
    available_repos = sorted(prs_df[repo_col].dropna().unique().tolist())
    
    # Multiselect filter (defaults to all repos selected)
    selected_repos = st.sidebar.multiselect(
        "Select Repository",
        options=available_repos,
        default=available_repos,
        help="Select one or more repositories to analyze."
    )
    
    # Filter dataset based on selection 
    if selected_repos:
        prs_filtered = prs_df[prs_df[repo_col].isin(selected_repos)]
    else:
        prs_filtered = prs_df.iloc[0:0] # Return empty dataframe if nothing is selected
else:
    st.sidebar.warning("Repository column not found in dataset.")
    prs_filtered = prs_df

st.sidebar.markdown("---")
# -----------------------------------------------------------------------------
# EMPTY STATE GUARD
# -----------------------------------------------------------------------------
if prs_filtered.empty:
    st.warning("⚠️ No repositories selected or no data matches the current filter criteria.")
    st.info("💡 Please select at least one repository from the sidebar to view metrics and charts.")
    st.stop()  # Prevents downstream code from running and throwing zero-division / null errors

if 'created_date' in prs_df.columns and not prs_df.empty:
    min_date = prs_filtered['created_date'].min()
    max_date = prs_filtered['created_date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filter dataset based on selected range
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        prs_filtered = prs_filtered[(prs_filtered['created_date'] >= start_d) & (prs_filtered['created_date'] <= end_d)]
    else:
        prs_filtered = prs_filtered
else:
    prs_filtered = prs_filtered


# -----------------------------------------------------------------------------
# HEADER & TOP METRICS
# -----------------------------------------------------------------------------


st.title("🚀 GitHub DORA Metrics & Engineering Analytics")
st.caption("Real-time pipeline metrics derived via Python API extraction, dbt transformations, and DuckDB Parquet storage.")

st.divider()

# st.dataframe(prs_filtered)

col1, col2, col3, col4 = st.columns(4)

total_prs = len(prs_filtered)
merged_prs = prs_filtered['is_merged'].sum() if 'is_merged' in prs_filtered.columns else 0
merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0
avg_time = prs_filtered['time_to_merge_hours'].mean() if 'time_to_merge_hours' in prs_filtered.columns else 0

with col1:
    st.metric("Total PRs Analyzed", f"{total_prs:,}")
with col2:
    st.metric("Merged PRs", f"{merged_prs:,}")
with col3:
    st.metric("Merge Rate", f"{merge_rate:.1f}%")
with col4:
    st.metric("Avg Time to Merge", f"{avg_time:.1f} hrs")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INTERACTIVE CHARTS
# -----------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.subheader("📈 PR Velocity Over Time")
    
    if 'created_date' in prs_filtered.columns:
        # Group by date for line chart
        daily_prs = prs_filtered.groupby('created_date').size().reset_index(name='pr_count')
        
        fig_timeline = px.line(
            daily_prs,
            x='created_date',
            y='pr_count',
            labels={'created_date': 'Date', 'pr_count': 'Pull Requests'},
            color_discrete_sequence=['#0366d6'],
            markers=True
        )
        fig_timeline.update_layout(
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title=None,
            yaxis_title="Count"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No date attribute available for timeline chart.")

with chart_col2:
    st.subheader("🎯 PR Status Breakdown")
    
    if 'pr_state' in prs_filtered.columns:
        status_counts = prs_filtered['pr_state'].value_counts().reset_index()
        status_counts.columns = ['pr_state', 'count']
        
        fig_pie = px.pie(
            status_counts,
            names='pr_state',
            values='count',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No state column present in dataset.")

st.divider()

# -----------------------------------------------------------------------------
# TOP CONTRIBUTORS & DATA DRILLDOWN
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["🏆 Top Contributors", "🔍 Raw Analytical Marts"])
with tab1:
    st.subheader("Engineering Team Performance")
    
    if not authors_df.empty:
        # Top Authors Bar Chart
        author_column = 'author_login' if 'author_login' in authors_df.columns else authors_df.columns[0]
        pr_count_column = 'total_prs_submitted' if 'total_prs_submitted' in authors_df.columns else authors_df.columns[1]
        
        fig_authors = px.bar(
            authors_df.sort_values(by=pr_count_column, ascending=True).tail(10),
            x=pr_count_column,
            y=author_column,
            orientation='h',
            title="Top 10 Contributors by PR Volume",
            color=pr_count_column,
            color_continuous_scale="Blues",
            text=pr_count_column
        )
        fig_authors.update_layout(margin=dict(l=20, r=20, t=40, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_authors, use_container_width=True)
        
        # Data table view
        st.dataframe(authors_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Fact Pull Requests Mart")
    st.dataframe(prs_filtered, use_container_width=True)


# Optional: Add to your charts section when analyzing multiple repos
if repo_col and len(prs_filtered[repo_col].unique()) > 1:
    st.subheader("📦 PR Distribution by Repository")
    repo_counts = prs_filtered[repo_col].value_counts().reset_index()
    repo_counts.columns = [repo_col, 'count']
    
    fig_repos = px.bar(
        repo_counts,
        x=repo_col,
        y='count',
        color=repo_col,
        title="Pull Requests per Repository",
        labels={'count': 'Total PRs', repo_col: 'Repository'}
    )
    st.plotly_chart(fig_repos, use_container_width=True)
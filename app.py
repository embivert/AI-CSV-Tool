import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import openai
from utils import ask_gpt

st.set_page_config(page_title="📊 Smart CSV Dashboard", layout="wide")

st.markdown("""
    <style>
        /* Remove default top padding */
        .block-container {
            padding-top: 1rem;
        }

        /* Optional: Make title bold, large, and nice */
        .main-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Smart CSV Analyst – AI-Powered CSV Insights Tool")

st.markdown("""
Welcome to **Smart CSV Analyst** – your intelligent assistant for exploring, filtering, charting, and analyzing CSV data using GPT.

#### ✨ Key Features:
- 🔍 Upload your CSV file
- 🧠 Ask questions in plain English – AI will respond using your dataset
- 📅 Smart filters auto-generated for columns with manageable unique values
- 📈 Auto chart generator for visual analysis
- 🤖 GPT-based analysis using sample data for fast & low-cost results
- 📥 Download filtered dataset easily

---
""")

uploaded_file = st.file_uploader("📤 Upload a CSV file", type=["csv"])

@st.cache_data
def load_csv(file):
    return pd.read_csv(file, encoding='latin-1')

if uploaded_file:
    df = load_csv(uploaded_file,)
    st.success(f"✅ Loaded `{uploaded_file.name}` ({df.shape[0]} rows, {df.shape[1]} columns)")

    # Show column stats
    st.sidebar.header("🔍 Column Filters")

    # Split UI into 2 columns
    left, right = st.columns([1, 2])
    # with left:
    st.subheader("📄 Data Preview")

    with st.sidebar:

        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        filters = {}

        with st.sidebar:

            for col in categorical_cols:
                unique_vals = df[col].nunique()

                if unique_vals <= 20 and unique_vals > 1:  # only filter if unique count is small
                    options = df[col].unique().tolist()
                    # select_all = "Select All"

                    selected = st.multiselect(f"Filter by {col}",  options, default=options[0])

                    # if select_all in selected:
                    #     selected = options
                    # else:
                    filters[col] = selected

            # Optional: check if there’s a datetime-like column
            for col in df.columns:
                if 'date' in col.lower():  # crude check: column name has 'date'
                    try:
                        date_format = st.selectbox("Select your date format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
                        dayfirst = True if date_format == "DD/MM/YYYY" else False

                        # Apply only to columns that look like dates
                        for col in df.columns:
                            if 'date' in col.lower():
                                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=dayfirst)
                                min_date, max_date = df[col].min(), df[col].max()
                                start_date = st.date_input(f"Start {col}", min_date)
                                end_date = st.date_input(f"End {col}", max_date)
                                filters[col] = (start_date, end_date)
                    except:
                        pass  # skip if conversion fails
    
    filtered_df = df.copy()
    
    for col, condition in filters.items():
        if isinstance(condition, list):  # for category filters
            filtered_df = filtered_df[filtered_df[col].isin(condition)]
        elif isinstance(condition, tuple):  # for date range filter
            start, end = condition
            filtered_df = filtered_df[(df[col] >= pd.to_datetime(start)) & (df[col] <= pd.to_datetime(end))]
    
    st.dataframe(filtered_df.head(10), hide_index=True, use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Filtered CSV", csv, "filtered_data.csv", "text/csv")


    st.subheader("📊 Charting Section")
    
    with st.expander("🤖 KPI Analysis", expanded=False):
        # Detect column types
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()
        x_options = category_cols + date_cols

        # Chart Type
        chart_type = st.selectbox("Select Chart Type", ["Bar", "Line", "Area", "Pie"])

        # X-axis
        x_axis = st.selectbox("Select X-axis", x_options, )

        # Y-axis (not needed for Pie)
        if chart_type != "Pie":
            y_axis = st.selectbox("Select Y-axis", numeric_cols)

        # Generate chart data
        if chart_type == "Pie":
            pie_data = df[x_axis].value_counts().reset_index()
            pie_data.columns = [x_axis, "Count"]
            fig, ax = plt.subplots()
            ax.pie(pie_data["Count"], labels=pie_data[x_axis], autopct="%1.1f%%")
            ax.axis("equal")
            st.pyplot(fig)

        else:
            grouped = df.groupby(x_axis)[y_axis].sum().reset_index()

            chart = alt.Chart(grouped).mark_line()  # default mark
            if chart_type == "Bar":
                chart = alt.Chart(grouped).mark_bar()
            elif chart_type == "Line":
                chart = alt.Chart(grouped).mark_line()
            elif chart_type == "Area":
                chart = alt.Chart(grouped).mark_area()

            chart = chart.encode(
                x=alt.X(x_axis, title=x_axis),
                y=alt.Y(y_axis, title=y_axis),
                tooltip=[x_axis, y_axis]
            ).properties(width=700, height=400)

            st.altair_chart(chart.interactive(), use_container_width=True)
    
    with st.expander("🤖 Ask questions about your data", expanded=True):
        user_question = st.text_input("Enter your question for the AI (Results will be based on for top 15 rows only as a demo)")

        if user_question and not df.empty:
            with st.spinner("Getting answer from GPT..."):
                ai_response = ask_gpt(df, user_question)
                st.markdown("### 💡 AI Insight")
                st.write(ai_response)


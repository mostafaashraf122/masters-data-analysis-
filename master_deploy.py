"""Streamlit dashboard for exploring the Masters suicide dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide", page_title="Masters Data Analysis")

DATA_PATH = Path(__file__).with_name("cleaned_df.csv")

COLUMN_RENAMES = {
    "age range": "age_range",
    "suicides/100k pop": "suicides_per_100k",
    "country-year": "country_year",
    "gdp_for_year ($)": "gdp_for_year_usd",
    "gdp_per_capita ($)": "gdp_per_capita_usd",
    "ag_group": "age_group",
}

COLUMN_DESCRIPTIONS = {
    "country": "Name of the country where the data was recorded.",
    "year": "Year associated with the observation.",
    "sex": "Gender of the demographic group.",
    "age_range": "Age bucket for the demographic group.",
    "suicides_no": "Number of reported suicides in the group.",
    "population": "Population size of the demographic group.",
    "suicides_per_100k": "Reported suicides per 100,000 people in the group.",
    "country_year": "Convenience field combining country and year.",
    "gdp_for_year_usd": "Country GDP for the year (current USD).",
    "gdp_per_capita_usd": "GDP per capita for the year (current USD).",
    "generation": "Generation label associated with the age bucket.",
    "age_group": "Plain-language label for the age bucket.",
}

NUMERIC_COLUMNS = [
    "suicides_no",
    "population",
    "suicides_per_100k",
    "gdp_for_year_usd",
    "gdp_per_capita_usd",
]


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load and tidy the dataset."""
    df = pd.read_csv(DATA_PATH, index_col=0)
    df = df.rename(columns=lambda col: col.strip())
    df = df.rename(columns=COLUMN_RENAMES)
    df["year"] = df["year"].astype(int)
    # Ensure consistent categorical ordering for nicer charts.
    df["age_range"] = pd.Categorical(
        df["age_range"],
        categories=[
            "5-14 years",
            "15-24 years",
            "25-34 years",
            "35-54 years",
            "55-74 years",
            "75+ years",
        ],
        ordered=True,
    )
    df.sort_values(["country", "year"], inplace=True)
    return df


def format_number(value: float) -> str:
    """Pretty-print large numbers for KPIs."""
    if pd.isna(value):
        return "-"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def apply_filters(
    df: pd.DataFrame,
    *,
    countries: list[str],
    year_range: tuple[int, int],
    sexes: list[str],
    age_groups: list[str],
) -> pd.DataFrame:
    """Return the dataframe filtered by sidebar selections."""
    mask = (
        df["country"].isin(countries)
        & df["year"].between(year_range[0], year_range[1])
        & df["sex"].isin(sexes)
        & df["age_group"].isin(age_groups)
    )
    return df.loc[mask]


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return the filtered dataframe."""
    st.sidebar.title("Filters")

    all_countries = sorted(df["country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Country",
        options=all_countries,
        default=all_countries,
        help="Select one or more countries to focus the analysis.",
    )
    if not selected_countries:
        selected_countries = all_countries

    min_year, max_year = int(df["year"].min()), int(df["year"].max())
    selected_years = st.sidebar.slider(
        "Year range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        help="Limit the dataset to a specific time window.",
    )

    all_sexes = sorted(df["sex"].unique())
    selected_sexes = st.sidebar.multiselect(
        "Sex",
        options=all_sexes,
        default=all_sexes,
    )
    if not selected_sexes:
        selected_sexes = all_sexes

    all_age_groups = sorted(df["age_group"].unique())
    selected_age_groups = st.sidebar.multiselect(
        "Age group",
        options=all_age_groups,
        default=all_age_groups,
    )
    if not selected_age_groups:
        selected_age_groups = all_age_groups

    filtered_df = apply_filters(
        df,
        countries=selected_countries,
        year_range=selected_years,
        sexes=selected_sexes,
        age_groups=selected_age_groups,
    )
    return filtered_df


def render_home(df: pd.DataFrame) -> None:
    st.title("Masters Data Analysis Dashboard")
    st.write(
        "Interactively explore suicide statistics across countries, time periods, "
        "and demographic groups. Use the sidebar to limit the scope of the analysis, "
        "then dive into the visualisation and insight pages for deeper exploration."
    )

    total_suicides = df["suicides_no"].sum()
    average_rate = df["suicides_per_100k"].mean()
    total_population = df["population"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total suicides", format_number(total_suicides))
    col2.metric("Average rate per 100k", f"{average_rate:.1f}")
    col3.metric("Population represented", format_number(total_population))
    col4.metric("Countries", f"{df['country'].nunique():,}")

    with st.expander("📋 Data dictionary", expanded=False):
        desc_df = pd.DataFrame(
            {"Column": list(COLUMN_DESCRIPTIONS.keys()), "Description": list(COLUMN_DESCRIPTIONS.values())}
        )
        st.dataframe(desc_df, use_container_width=True, hide_index=True)

    with st.expander("🔎 Filtered data preview", expanded=True):
        st.dataframe(df, use_container_width=True)

    st.caption(
        "KPIs and data preview respect the filters selected in the sidebar. "
        "The analysis and visualisations tabs provide more focused insights."
    )


def render_visualisations(df: pd.DataFrame) -> None:
    st.header("Visual exploration")

    if df.empty:
        st.info("No data available with the current filters. Adjust the sidebar selections to continue.")
        return

    st.subheader("Distribution explorer")
    selected_numeric = st.selectbox(
        "Numeric column",
        options=NUMERIC_COLUMNS,
        format_func=lambda col: col.replace("_", " ").title(),
    )

    bins = st.slider("Histogram bins", min_value=10, max_value=80, value=30, step=5)
    hist_fig = px.histogram(
        df,
        x=selected_numeric,
        color="sex",
        nbins=bins,
        marginal="box",
        labels={selected_numeric: selected_numeric.replace("_", " ").title()},
    )
    hist_fig.update_layout(legend_title_text="Sex")
    st.plotly_chart(hist_fig, use_container_width=True)

    st.subheader("Scatter comparison")
    scatter_cols = st.columns(3)
    x_axis = scatter_cols[0].selectbox("X axis", options=NUMERIC_COLUMNS, index=NUMERIC_COLUMNS.index("population"))
    y_axis = scatter_cols[1].selectbox("Y axis", options=NUMERIC_COLUMNS, index=NUMERIC_COLUMNS.index("suicides_no"))
    color_by = scatter_cols[2].selectbox(
        "Color by",
        options=["None", "country", "sex", "age_group"],
        index=1,
    )
    color = None if color_by == "None" else color_by

    scatter_fig = px.scatter(
        df,
        x=x_axis,
        y=y_axis,
        color=color,
        hover_data=["country", "year", "sex", "age_group"],
        labels={
            x_axis: x_axis.replace("_", " ").title(),
            y_axis: y_axis.replace("_", " ").title(),
        },
    )
    scatter_fig.update_traces(marker=dict(size=10, opacity=0.7))
    st.plotly_chart(scatter_fig, use_container_width=True)

    st.subheader("Top countries by suicides")
    top_countries = (
        df.groupby("country", as_index=False)["suicides_no"].sum().sort_values("suicides_no", ascending=False).head(10)
    )
    top_fig = px.bar(
        top_countries,
        x="suicides_no",
        y="country",
        orientation="h",
        labels={"suicides_no": "Suicides", "country": "Country"},
    )
    top_fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(top_fig, use_container_width=True)


def render_analysis(df: pd.DataFrame) -> None:
    st.header("Insights & breakdowns")

    if df.empty:
        st.info("No data available with the current filters. Adjust the sidebar selections to continue.")
        return

    country_options = sorted(df["country"].unique())
    focus_country = st.selectbox(
        "Focus country",
        options=country_options,
        help="Select a single country for a detailed time-series view.",
    )

    country_df = df[df["country"] == focus_country]
    yearly_country = (
        country_df.groupby("year", as_index=False)
        .agg(
            suicides_no=("suicides_no", "sum"),
            population=("population", "sum"),
            suicides_per_100k=("suicides_per_100k", "mean"),
            gdp_per_capita_usd=("gdp_per_capita_usd", "mean"),
        )
        .sort_values("year")
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total suicides", format_number(country_df["suicides_no"].sum()))
    col2.metric("Peak rate per 100k", f"{country_df['suicides_per_100k'].max():.1f}")
    col3.metric("Average GDP per capita", f"${country_df['gdp_per_capita_usd'].mean():,.0f}")

    trend_cols = st.columns(2)
    suicides_trend = px.line(
        yearly_country,
        x="year",
        y="suicides_no",
        markers=True,
        labels={"suicides_no": "Suicides", "year": "Year"},
        title=f"Yearly suicides – {focus_country}",
    )
    trend_cols[0].plotly_chart(suicides_trend, use_container_width=True)

    rate_trend = px.line(
        yearly_country,
        x="year",
        y="suicides_per_100k",
        markers=True,
        labels={"suicides_per_100k": "Rate per 100k", "year": "Year"},
        title=f"Suicide rate per 100k – {focus_country}",
    )
    trend_cols[1].plotly_chart(rate_trend, use_container_width=True)

    st.subheader("Demographic breakdown")
    demography_cols = st.columns(2)

    age_breakdown = (
        country_df.groupby("age_group", as_index=False)["suicides_no"].sum().sort_values("suicides_no", ascending=False)
    )
    age_fig = px.bar(
        age_breakdown,
        x="suicides_no",
        y="age_group",
        orientation="h",
        labels={"suicides_no": "Suicides", "age_group": "Age group"},
    )
    demography_cols[0].plotly_chart(age_fig, use_container_width=True)

    sex_breakdown = (
        country_df.groupby("sex", as_index=False)["suicides_no"].sum().sort_values("suicides_no", ascending=False)
    )
    sex_fig = px.pie(
        sex_breakdown,
        values="suicides_no",
        names="sex",
        title="Share of suicides by sex",
    )
    demography_cols[1].plotly_chart(sex_fig, use_container_width=True)

    st.subheader("Highest suicide years in the filtered dataset")
    top_years = (
        df.groupby(["country", "year"], as_index=False)["suicides_no"].sum().sort_values("suicides_no", ascending=False).head(10)
    )
    st.dataframe(top_years, use_container_width=True, hide_index=True)


def main() -> None:
    df = load_data()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Pages", ["Home", "Visualisations", "Analysis"], index=0)

    filtered_df = render_filters(df)

    if page == "Home":
        render_home(filtered_df)
    elif page == "Visualisations":
        render_visualisations(filtered_df)
    else:
        render_analysis(filtered_df)


if __name__ == "__main__":
    main()


import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(layout= 'wide', page_title= 'master analysis')
df = pd.read_csv('cleaned_df.csv', index_col= 0)
html_title = """<h1 style="color:white;text-align:center;"> masters Data Analysis </h1>"""
st.markdown(html_title, unsafe_allow_html=True)


page = st.sidebar.radio('Pages', ['Home', "visualization", "analysis"])


if page == 'Home':
    st.title('this is the data')
    data_display = st.empty()  
    data_display.dataframe(df.head(10))

    if st.button('show all'):
        data_display.dataframe(df)  

    column_descriptions = {
        "country": "Name of the country where the data is recorded.",
        "year": "Year in which the suicide data was collected.",
        "sex": "Gender category (male or female).",
        "age": "Age group of the population category.",
        "suicides_no": "Total number of suicide cases reported in that demographic group.",
        "population": "Total population count in that age and gender group.",
        "suicides/100k pop": "Suicide rate per 100,000 people in that demographic group.",
        "country-year": "Combined identifier for country and year.",
        "HDI for year": "Human Development Index for the country in that particular year.",
        " gdp_for_year ($) ": "Gross Domestic Product of the country for that year (in USD).",
        "gdp_per_capita ($)": "GDP per person for the country in that year.",
        "generation": "Generational category for the age group (e.g., Generation X, Boomers)."}

    desc_df = pd.DataFrame(list(column_descriptions.items()), columns=["Column Name", "Description"])

    st.subheader("📝 Column Descriptions")
    st.table(desc_df)

elif page == 'visualization':
    st.markdown("<h1 style='text-align: center; color: red;'> 📈this is the histogram for every  numerical column</h1>", unsafe_allow_html=True)

    numerical = df.select_dtypes(include='number').columns

    for cols in numerical:
        st.plotly_chart(px.histogram(data_frame= df , x = cols))
     

elif page == 'analysis':
    st.markdown("""
    <style>
        .css-1wa3eu0 {  
            width: 60%;
            margin-left: auto;
            margin-right: auto;
            font-size: 22px;  /* تكبير الخط */
        }
        .css-1v3fvcr {  
            text-align: center;
        }
        .css-2trqyj {  
            font-size: 20px;
        }
        h1 {
            font-size: 40px !important;  /* تكبير حجم العنوان */
        }
    </style>
    """, unsafe_allow_html=True)
    

    st.header('here you will see some analysis for the data')


    col1, col2 , col3 = st.columns(3)
    
    countries = df['country'].unique()
    

    option1 = col1.selectbox('select the country to see the no of sucides',countries)
    df1 = df[df['country'] == option1 ]
    selected_Country = df1[['year','suicides_no']]
    col2.dataframe(selected_Country)
    col3.plotly_chart(px.line(data_frame = selected_Country ,x= 'year' , y = 'suicides_no'))
     














import streamlit as st
from copilot import Copilot
import os
import pandas as pd
import plotly.express as px
import requests
import pycountry  # For country code mappings



# Helper functions for data fetching and processing
def get_indicator_code(variable):
    indicator_codes = {
        "GDP": "NY.GDP.MKTP.CD",
        "Inflation": "FP.CPI.TOTL.ZG",
        "Unemployment Rate": "SL.UEM.TOTL.ZS",
        "Population": "SP.POP.TOTL",
        "GDP per Capita": "NY.GDP.PCAP.CD",
    }
    return indicator_codes.get(variable, "")

def get_country_code(country):
    country_data = pycountry.countries.search_fuzzy(country)
    if country_data:
        return country_data[0].alpha_3  # World Bank uses ISO-3 codes
    else:
        return None

@st.cache
def fetch_wb_data(variable, country, start_year, end_year):
    indicator_code = get_indicator_code(variable)
    country_code = get_country_code(country)
    if not country_code:
        st.error(f"Country code for {country} not found.")
        return pd.DataFrame()

    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
    params = {
        'date': f'{start_year}:{end_year}',
        'format': 'json',
        'per_page': 1000
    }

    response = requests.get(url, params=params)
    data = response.json()

    if len(data) == 2:
        df = pd.DataFrame(data[1])
        df = df[['date', 'value']]
        df.rename(columns={'date': 'Date', 'value': 'Value'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna()
        df = df.sort_values('Date')
        return df
    else:
        st.error(f"No data found for {variable} in {country}.")
        return pd.DataFrame()

@st.cache
def fetch_wb_data_geo(variable, year):
    indicator_code = get_indicator_code(variable)
    url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
    params = {
        'date': f'{year}',
        'format': 'json',
        'per_page': 300
    }

    response = requests.get(url, params=params)
    data = response.json()

    if len(data) == 2:
        df = pd.DataFrame(data[1])
        df = df[['countryiso3code', 'country', 'value']]
        df.rename(columns={'countryiso3code': 'Country Code', 'country': 'Country', 'value': 'Value'}, inplace=True)
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna()
        return df
    else:
        st.error(f"No data found for {variable} in {year}.")
        return pd.DataFrame()


@st.cache
def get_country_list():
    url = "http://api.worldbank.org/v2/country?format=json&per_page=300"
    response = requests.get(url)
    data = response.json()
    if len(data) == 2:
        countries = [country['name'] for country in data[1]]
        return countries
    else:
        st.error("Failed to fetch country list.")
        return []


@st.cache
def fetch_exchange_rates(base_currency='USD'):
    url = f"https://api.exchangerate.host/latest?base={base_currency}"
    
    response = requests.get(url)
    data = response.json()
    
    if 'rates' in data:
        rates = data['rates']
        df = pd.DataFrame(list(rates.items()), columns=['Currency', 'Exchange Rate'])
        return df
    else:
        st.error("Failed to fetch exchange rates.")
        return pd.DataFrame()







### set openai key, first check if it is in environment variable, if not, check if it is in streamlit secrets, if not, raise error

st.title("Ask Me Anything about Macroeconomics & Regional Economic Outlook!")
st.write(
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key: ### get openai key from user input
    openai_api_key = st.text_input("Please enter your OpenAI API Key", type="password")

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create tabs for Chatbot and Economic Data Visualization
    tab1, tab2 = st.tabs(["Chatbot", "Economic Data Visualization"])

    ### Chatbot Feature (Tab 1)
    with tab1:
        if "messages" not in st.session_state.keys():  # Initialize the chat messages history
            st.session_state.messages = [
                {"role": "assistant", "content": "I am Macroeconomics Copilot, your personal assistant. You can ask me everything about regional macroeconomic outlook around the world."}
            ]

        @st.cache_resource
        def load_copilot():
            return Copilot(key = openai_api_key)

        if "chat_copilot" not in st.session_state.keys():  # Initialize the chat engine
            st.session_state.chat_copilot = load_copilot()

        if prompt := st.chat_input(
            "Ask a question"
        ):  # Prompt for user input and save to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        for message in st.session_state.messages:  # Write message history to UI
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # If last message is not from assistant, generate a new response
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):

                retrived_info, answer = st.session_state.chat_copilot.ask(prompt, messages=st.session_state.messages[:-1])
                ### answer can be a generator or a string

                #print(retrived_info)
                if isinstance(answer, str):
                    st.write(answer)
                else:
                    ### write stream answer to UI
                    def generate():
                        for chunk in answer:
                            content = chunk.choices[0].delta.content
                            if content:
                                yield content
                    answer = st.write_stream(generate())

                st.session_state.messages.append({"role": "assistant", "content": answer})
    
    ### Economic Data Visualization Feature (Tab 2)
    with tab2:
        st.header("Economic Data Visualization")

        # Step 1: User Inputs
        economic_variables = ["GDP", "Inflation", "Unemployment Rate", "Population", "GDP per Capita", "Exchange Rates"]
        variable = st.selectbox("Select Economic Variable", economic_variables)

        if variable != "Exchange Rates":
            viz_type = st.radio("Select Visualization Type", ("Time Series Plot", "Geographical Visualization"))

            if viz_type == "Time Series Plot":
                # Select Country
                countries = get_country_list()
                country = st.selectbox("Select Country", countries)

                # Select Time Period
                start_year, end_year = st.slider("Select Time Period", 1960, 2023, (2010, 2023))

                # Fetch and Display Data
                df = fetch_wb_data(variable, country, start_year, end_year)

                if not df.empty:
                    st.write(f"Displaying {variable} data for {country} from {start_year} to {end_year}")
                    fig = px.line(df, x='Date', y='Value', title=f"{variable} in {country}")
                    st.plotly_chart(fig)
                else:
                    st.warning("No data available for the selected options.")

            else:
                # Geographical Visualization
                year = st.slider("Select Year", 1960, 2023, 2023)

                df = fetch_wb_data_geo(variable, year)

                if not df.empty:
                    st.write(f"Displaying {variable} data for all countries in {year}")
                    fig = px.choropleth(
                        df,
                        locations="Country Code",
                        color="Value",
                        hover_name="Country",
                        color_continuous_scale=px.colors.sequential.Plasma,
                        title=f"{variable} in {year}",
                    )
                    st.plotly_chart(fig)
                else:
                    st.warning("No data available for the selected options.")
        else:
            # Exchange Rates Visualization
            st.subheader("Exchange Rates Against USD")
            df = fetch_exchange_rates()

            if not df.empty:
                st.write("Displaying current exchange rates against USD")

                # Option to filter currencies
                currencies = st.multiselect(
                    "Select Currencies to Display",
                    df['Currency'].tolist(),
                    default=['EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY']
                )
                filtered_df = df[df['Currency'].isin(currencies)]

                fig = px.bar(filtered_df, x='Currency', y='Exchange Rate', title='Exchange Rates Against USD')
                st.plotly_chart(fig)
            else:
                st.warning("Failed to fetch exchange rates.")

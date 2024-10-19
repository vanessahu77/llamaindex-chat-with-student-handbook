# 🦙📚 Regional Economic Outlook Copilot

Regional Economic Outlook Copilot is an AI-powered chatbot designed to answer questions about Regional Economic Outlook using information on reported produced by IMF and data from World Bank. It leverages the capabilities of OpenAI's GPT-4o and LlamaIndex to provide accurate and contextually relevant responses based on the data it has been trained on.

## Overview of the App

- Takes user queries via Streamlit's `st.chat_input` and displays both user queries and model responses with `st.chat_message`.
- Use `Copilot` class to interact with the chatbot by passing in a question and a list of messages and get a response.
- Uses LlamaIndex to load and index data and create a Retriever to retrieve context from that data to respond to each user query.
- `Economic Data Visualization` that pulls in historical and latest data on major world econmic indicators, and provides time series and geographical visualizations. 

## Demo App

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://llamaindex-chat-with-student-handbook-8tp48eikcchw2w9g9fvmsj.streamlit.app/)

## Run the app locally

1. Clone the repository
2. Install the dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
streamlit run streamlit_app.py
```

## Get an OpenAI API key

You can get your own OpenAI API key by following the following instructions:
1. Go to https://platform.openai.com/account/api-keys.
2. Click on the `+ Create new secret key` button.
3. Next, enter an identifier name (optional) and click on the `Create secret key` button, then copy the API key.
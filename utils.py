# utils.py

import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt(df: pd.DataFrame, question: str) -> str:
    try:
        prompt = f"""
You are a senior data analyst. Based on this dataset sample, answer the user's question.

Sample Data:
{df.head(20).to_csv(index=False)}

Question:
{question}

Answer (in bullet points if possible):
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", #"gpt-4",  # or "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"

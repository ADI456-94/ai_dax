import openai
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os

# Загружаем переменные окружения (если нужно)
load_dotenv()

# Используем секреты Streamlit для получения API ключа
openai.api_key = st.secrets["openai"]["api_key"]

# Общая функция генерации запроса (SQL или DAX), учитывающая загруженные колонки
def generate_query(user_query, df=None, mode="SQL"):
    system_prompt = {
        "SQL": """You are a helpful assistant that translates natural language into SQL queries.
Use correct logic for metrics like AOV (average order value = total revenue divided by number of distinct orders).
Use window functions when needed for cumulative calculations.
Always check for DISTINCT in aggregations when counting IDs like orders or customers.""",
        "DAX": "You are a helpful assistant that generates DAX formulas based on user requests."
    }
    prefix = {
        "SQL": "You are a helpful assistant that translates natural language into SQL queries. Use window functions like SUM() OVER for cumulative totals when needed. Assume the table includes fields like 'Date' or 'ID' for ordering.",
        "DAX": "Generate a DAX formula using the columns from this table: "
    }

    # Добавляем описание колонок из датафрейма
    schema_info = ""
    if df is not None:
        columns = df.columns.tolist()
        schema_info = "Columns: " + ", ".join(columns)

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": system_prompt[mode]
            }, {
                "role": "user", "content": f"{prefix[mode]} {schema_info}\nRequest: {user_query}"
            }],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# Загрузка файла Excel или CSV
def load_data():
    uploaded_file = st.file_uploader("Загрузите файл CSV или Excel", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
            st.write("Данные загружены:")
            st.dataframe(df)
            return df
        except Exception as e:
            st.error(f"Ошибка при загрузке файла: {e}")
    return None

# Главная функция Streamlit
def main():
    st.title("🧠 AI Assistant: SQL & DAX Generator")

    df = load_data()
    if df is not None:
        query_type = st.selectbox("Выберите тип запроса", ["SQL", "DAX"])
        user_query = st.text_input("Введите запрос на естественном языке")

        if user_query:
            result = generate_query(user_query, df=df, mode=query_type)
            if result.startswith("Error"):
                st.error(result)
            else:
                label = "SQL-запрос" if query_type == "SQL" else "DAX-формула"
                st.subheader(f"Сгенерированный {label}:")
                st.code(result, language="sql" if query_type == "SQL" else "text")
                st.info(f"Используйте сгенерированный {label} в соответствующем инструменте.")

if __name__ == "__main__":
    main()

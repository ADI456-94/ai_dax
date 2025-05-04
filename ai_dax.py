import openai
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

from smolagents import CodeAgent, OpenAIServerModel

# Загрузка переменных окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Ошибка: API ключ не найден. Проверь .env файл или настройки секретов Streamlit.")
    st.stop()

model = OpenAIServerModel(
    model_id="gpt-4o",
    client_kwargs={"api_key": api_key}
)
agent = CodeAgent(model=model, tools=[])

# Функция генерации SQL или DAX запросов
def generate_query(user_query, df, mode="SQL"):
    columns = ", ".join(df.columns)
    
    if mode == "SQL":
        prompt = f"""
You are an expert assistant in writing SQL queries.

The available columns are: {columns}.

Translate the following user request into a SQL query.

The SQL query MUST strictly follow this structure:
1. SELECT required columns or aggregations
2. FROM the available dataset
3. WHERE if logical
3. GROUP BY if needed (even if the user does not mention it)
4. ORDER BY if logical

Only output the raw SQL code inside a code block.
User request:
{user_query}
"""
    elif mode == "DAX":
        prompt = f"""
You are an expert assistant in writing DAX formulas for Power BI.

The available columns are: {columns}.

Translate the following user request into a valid DAX formula.

Use proper DAX functions such as SUMMARIZE, CALCULATE, FILTER, or others depending on the request.
The formula should be clean, efficient, and ready to use in Power BI.

Only output the raw DAX code inside a code block.
User request:
{user_query}
"""

    try:
        response = agent.run(prompt)
        if isinstance(response, dict):
            response = response.get("output", "")
        elif isinstance(response, list):
            response = "\n".join(str(x) for x in response)
        return response.strip()
    except Exception as e:
        return f"Ошибка при генерации {mode}: {e}"


# Функция загрузки данных
def load_data():
    uploaded_file = st.file_uploader("Загрузите CSV или Excel файл", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
            st.success("Файл успешно загружен.")
            st.dataframe(df)
            return df
        except Exception as e:
            st.error(f"Ошибка при загрузке файла: {e}")
    return None

# Функция для создания графиков
def create_chart(df, chart_type, x_col, y_col):
    if chart_type == "Line Chart":
        st.line_chart(df[[x_col, y_col]])
    elif chart_type == "Bar Chart":
        st.bar_chart(df[[x_col, y_col]])
    elif chart_type == "Histogram":
        fig, ax = plt.subplots()
        ax.hist(df[y_col], bins=20)
        ax.set_xlabel(y_col)
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
    elif chart_type == "Pie Chart":
        fig, ax = plt.subplots()
        df[y_col].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')
        st.pyplot(fig)

# Главная функция
def main():
    st.title("ChatGPT for SQL & DAX + Chart Maker")

    df = load_data()  # Загрузка данных
    if df is None:
        return

    tab1, tab2 = st.tabs(["🧠 Генерация SQL/DAX", "📊 Создание графиков"])

    # Генерация SQL/DAX запросов
    with tab1:
        st.header("Генерация SQL или DAX запросов")
        user_query = st.text_input("Введите ваш запрос на естественном языке:")
        mode = st.selectbox("Выберите язык запроса", ["SQL", "DAX"])

        if user_query:
            if st.button("Сгенерировать запрос"):
                query_result = generate_query(user_query, df, mode)
                if "Ошибка" in query_result:
                    st.error(query_result)
                else:
                    st.subheader(f"{mode} запрос:")
                    st.code(query_result, language="sql" if mode == "SQL" else "text")

    # Создание графиков
    with tab2:
        st.header("Создание графиков")
        
        chart_type = st.selectbox("Выберите тип графика", ["Line Chart", "Bar Chart", "Histogram", "Pie Chart"])

        x_col = st.selectbox("Выберите столбец для оси X", df.columns)
        y_col = st.selectbox("Выберите столбец для оси Y", df.columns)

        if st.button("Построить график"):
            create_chart(df, chart_type, x_col, y_col)

if __name__ == "__main__":
    main()

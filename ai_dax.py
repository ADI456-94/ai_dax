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
    prompt = f"""
You are an expert assistant in writing {mode} queries.

The available columns are: {columns}.

Translate the following user request into a valid {mode} query or formula.
Request: {user_query}

Respond ONLY with the {mode} code block.
Do NOT add explanations, comments, print statements, or execution results.
Just return the raw {mode} code.
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
    st.title("AI SQL & DAX Generator + Chart Maker")

    df = load_data()  # Загрузка данных
    if df is None:
        return

    # Вкладки для выбора функций
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
        
        # Выбор типа графика
        chart_type = st.selectbox("Выберите тип графика", ["Line Chart", "Bar Chart", "Histogram", "Pie Chart"])

        # Выбор столбцов для осей графика
        x_col = st.selectbox("Выберите столбец для оси X", df.columns)
        y_col = st.selectbox("Выберите столбец для оси Y", df.columns)

        if st.button("Построить график"):
            create_chart(df, chart_type, x_col, y_col)

if __name__ == "__main__":
    main()

import openai
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt

# Импорт агента
from smolagents import CodeAgent, DuckDuckGoSearchTool, OpenAIServerModel

# Загрузка переменных окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Инициализация агента через OpenAI
import streamlit as st
from dotenv import load_dotenv
import os
import openai
from smolagents import CodeAgent, OpenAIServerModel

# Загрузка переменных окружения
load_dotenv()

# Правильно сначала объявить переменную api_key:
api_key = os.getenv("OPENAI_API_KEY")

# Теперь проверка:
if not api_key:
    st.error("Ошибка: API ключ не найден. Проверь .env файл или настройки секретов Streamlit.")
    st.stop()

# Теперь передаем его OpenAI библиотеке (если нужно напрямую использовать openai)
openai.api_key = api_key

# И передаем в OpenAIServerModel
# Создание модели
model = OpenAIServerModel(
    model_id="gpt-4o",
    client_kwargs={"api_key": api_key}
)

# Создание агента
agent = CodeAgent(
    model=model,
    tools=[]  # <-- добавили tools (пока без инструментов)
)


# Генерация SQL/DAX запроса
def generate_query(user_query, df=None, mode="SQL"):
    system_prompt = {
        "SQL": """You are a helpful assistant that translates natural language into SQL queries.
    Start by generating the basic query structure. Then, I'll provide further instructions for each part of the query..""",
        "DAX": "You are a helpful assistant that generates DAX formulas based on user requests."
    }

    prefix = {
        "SQL": "You are a helpful assistant that translates natural language into SQL queries. Use window functions like SUM() OVER for cumulative totals when needed. Assume the table includes fields like 'Date' or 'ID' for ordering.",
        "DAX": "Generate a DAX formula using the columns from this table: "
    }

    try:
        task_prompt = f"{prefix[mode]} \n\nRequest: {user_query}"

        response = agent.run(task_prompt)
        return response
    except Exception as e:
        return f"Ошибка при запросе к агенту: {e}"

# Подсказка по типу графика
def suggest_chart_type(user_query, df):
    try:
        prompt = f"""You are a helpful assistant that suggests the best chart type and gives an example based on the user's question and the dataset columns.
Request: {user_query}
Columns: {', '.join(df.columns)}

Respond in the following format:
Chart Type: <Line chart / Bar chart / Histogram / Pie chart>
Example: <Short explanation or usage example>"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You suggest the best chart type and example for visualizing user data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error suggesting chart type: {e}"

# Подсказка по осям графика
def suggest_chart_columns(user_query, df):
    try:
        prompt = f"""You are an assistant that suggests which columns to use for plotting a chart based on a user query and the dataset.
Request: {user_query}
Columns: {', '.join(df.columns)}

Respond in the following format:
X: <column_name>
Y: <column_name>"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Suggest appropriate X and Y columns for a chart."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error suggesting columns: {e}"

# Загрузка данных
def load_data():
    uploaded_file = st.file_uploader("\U0001F4C2 Загрузите файл CSV или Excel", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
            st.write("Данные загружены:")
            st.dataframe(df)
            return df
        except Exception as e:
            st.error(f"Ошибка при загрузке файла: {e}")
    return None

# Визуализация
def draw_chart(df, chart_type, x_col, y_col):
    st.subheader(f"{chart_type} по {x_col} и {y_col}")
    try:
        if chart_type == "Линейный":
            st.line_chart(df.set_index(x_col)[y_col])
        elif chart_type == "Столбчатый":
            st.bar_chart(df.set_index(x_col)[y_col])
        elif chart_type == "Гистограмма":
            fig, ax = plt.subplots()
            ax.hist(df[y_col], bins=20)
            st.pyplot(fig)
        elif chart_type == "Круговая диаграмма":
            fig, ax = plt.subplots()
            pie_data = df.groupby(x_col)[y_col].sum()
            ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%')
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Ошибка при построении графика: {e}")

# Главная функция
def main():
    st.title("\U0001F9E0 AI Assistant: SQL & DAX Generator + Chart Suggestion")

    df = load_data()
    if df is not None:
        user_query = st.text_input("Введите ваш аналитический запрос (естественный язык)")
        language_choice = st.selectbox("Выберите язык запроса", ["SQL", "DAX"])

        if user_query:
            result = generate_query(user_query, df, language_choice)
            if str(result).startswith("Ошибка"):
                st.error(result)
            else:
                st.subheader("Сгенерированный код и объяснение:")
                st.markdown(result)

                suggestion = suggest_chart_type(user_query, df)
                if not suggestion.startswith("Error"):
                    st.success(f"\U0001F4A1 Рекомендация по визуализации:\n\n{suggestion}")

                    col_suggestion = suggest_chart_columns(user_query, df)
                    if not col_suggestion.startswith("Error") and "X:" in col_suggestion and "Y:" in col_suggestion:
                        try:
                            x_field = col_suggestion.split("X:")[1].split("Y:")[0].strip()
                            y_field = col_suggestion.split("Y:")[1].strip()
                            st.info(f"Предлагаемые поля:\n- X: {x_field}\n- Y: {y_field}")

                            if "Line" in suggestion:
                                draw_chart(df, "Линейный", x_field, y_field)
                            elif "Bar" in suggestion:
                                draw_chart(df, "Столбчатый", x_field, y_field)
                            elif "Histogram" in suggestion:
                                draw_chart(df, "Гистограмма", x_field, y_field)
                            elif "Pie" in suggestion:
                                draw_chart(df, "Круговая диаграмма", x_field, y_field)
                        except Exception as e:
                            st.warning(f"Ошибка при автоотрисовке: {e}")
                    else:
                        st.warning("Не удалось определить поля для осей.")
                else:
                    st.warning(suggestion)

if __name__ == "__main__":
    main()

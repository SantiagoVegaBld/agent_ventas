# src/agent/core_agent.py

import sqlite3
import pandas as pd
import plotly.express as px
from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
import os

class SQLConnector:
    """Conector simple a SQLite para ejecutar consultas SQL y devolver DataFrame."""
    def __init__(self, db_path="ventas.db"):
        self.db_path = db_path

    def execute_query(self, query: str) -> pd.DataFrame:
        # Abrir conexión SQLite y ejecutar consulta dentro de contexto para cierre automático
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df

class CoreAgent:
    def __init__(self, db_path="ventas.db"):
        # Configuración del modelo LLM y prompt para traducción NL -> SQL
        self.llm = OpenAI(temperature=0)
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template=(
                "Eres un asistente que traduce preguntas en lenguaje natural sobre ventas "
                "a consultas SQL seguras para la tabla 'ventas'. Solo genera consultas SELECT.\n"
                "Pregunta: {question}\nSQL:"
            )
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        self.sql_connector = SQLConnector(db_path)

    def nl_to_sql(self, question: str) -> str:
        """
        Traduce la pregunta en lenguaje natural a una consulta SQL usando el LLM.
        Luego sanitiza la consulta para seguridad.
        """
        sql_query = self.chain.run(question=question)
        sql_query = self._sanitize_sql(sql_query)
        return sql_query

    def _sanitize_sql(self, sql: str) -> str:
        """
        Valida que la consulta SQL sea segura:
        - Solo permite consultas SELECT.
        - No permite comandos peligrosos (DROP, DELETE, UPDATE, INSERT, ALTER).
        - Agrega LIMIT 100 si no está presente para limitar resultados.
        """
        sql_lower = sql.strip().lower()
        if not sql_lower.startswith("select"):
            raise ValueError("Solo se permiten consultas SELECT.")
        forbidden = ["drop", "delete", "update", "insert", "alter"]
        if any(word in sql_lower for word in forbidden):
            raise ValueError("Consulta SQL contiene comandos no permitidos.")
        if "limit" not in sql_lower:
            sql += " LIMIT 100"
        return sql

    def execute_sql(self, sql: str) -> pd.DataFrame:
        """Ejecuta la consulta SQL usando el conector y devuelve un DataFrame."""
        return self.sql_connector.execute_query(sql)

    def generate_plot(self, df: pd.DataFrame, question: str) -> str:
        """
        Genera un gráfico de barras sencillo:
        - Busca la primera columna como eje X.
        - Busca la primera columna numérica como eje Y.
        - Guarda el gráfico como archivo HTML con nombre único.
        """
        if df.empty:
            return "No hay datos para graficar."

        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) == 0:
            return "No hay columnas numéricas para graficar."

        x_col = df.columns[0]
        y_col = numeric_cols[0]

        fig = px.bar(df, x=x_col, y=y_col, title=question)
        graph_path = f"output/graph_{abs(hash(question))}.html"  # Nombre único para evitar sobrescribir
        os.makedirs(os.path.dirname(graph_path), exist_ok=True)
        fig.write_html(graph_path)
        return f"Gráfico generado y guardado en {graph_path}"

    def save_file(self, df: pd.DataFrame, filename="output/data.csv") -> str:
        """Guarda el DataFrame en un archivo CSV (puedes extender a Excel si quieres)."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)
        return f"Archivo guardado en {filename}"

    def handle_question(self, question: str):
        """
        Flujo principal para manejar preguntas:
        - Traduce NL a SQL.
        - Ejecuta consulta.
        - Decide si genera gráfico, guarda archivo o devuelve tabla según keywords.
        """
        try:
            sql = self.nl_to_sql(question)
            df = self.execute_sql(sql)

            question_lower = question.lower()
            if any(keyword in question_lower for keyword in ["gráfico", "grafico", "gráficos", "grafica"]):
                return self.generate_plot(df, question)
            elif any(keyword in question_lower for keyword in ["archivo", "csv", "excel"]):
                # Aquí podrías mejorar para detectar nombre de archivo dinámico
                filename = "output/ventas.csv"
                return self.save_file(df, filename)
            else:
                # Mostrar tabla simple (primeras 10 filas)
                if df.empty:
                    return "No se encontraron resultados."
                return df.head(10).to_string(index=False)
        except Exception as e:
            return f"Error: {e}"

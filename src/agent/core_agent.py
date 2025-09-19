# src/agent/core_agent.py

from langchain import LLMChain, PromptTemplate
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from langchain.llms import OpenAI
import re

# Herramientas MCP simuladas (deberían ser conectores reales)
class SQLTool(BaseTool):
    name = "sql"
    description = "Ejecuta consultas SQL seguras sobre la base de datos de ventas."

    def _run(self, query: str):
        # Validación simple: solo SELECT y limitación
        if not query.strip().lower().startswith("select"):
            return "Error: Solo consultas SELECT están permitidas."
        if "drop" in query.lower() or "delete" in query.lower():
            return "Error: Consultas destructivas no permitidas."
        # Aquí se llamaría al conector MCP real para ejecutar la consulta
        # Simulación de resultado:
        return f"Ejecutando SQL: {query}"

    async def _arun(self, query: str):
        return self._run(query)

class PlotTool(BaseTool):
    name = "plot"
    description = "Genera gráficos a partir de datos."

    def _run(self, data):
        # Aquí se generaría un gráfico usando matplotlib, plotly, etc.
        return f"Gráfico generado con datos: {data}"

    async def _arun(self, data):
        return self._run(data)

class FileTool(BaseTool):
    name = "file"
    description = "Guarda datos en archivos CSV o Excel."

    def _run(self, data):
        # Aquí se guardaría el archivo y se devolvería la ruta
        return f"Archivo guardado con datos: {data}"

    async def _arun(self, data):
        return self._run(data)

# Prompt para traducir lenguaje natural a SQL
PROMPT = PromptTemplate(
    input_variables=["question"],
    template=(
        "Eres un asistente que traduce preguntas en lenguaje natural sobre ventas "
        "a consultas SQL seguras para la tabla 'ventas'. Solo genera consultas SELECT. "
        "Pregunta: {question}\nSQL:"
    )
)

class CoreAgent:
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.sql_tool = SQLTool()
        self.plot_tool = PlotTool()
        self.file_tool = FileTool()
        self.chain = LLMChain(llm=self.llm, prompt=PROMPT)

    def nl_to_sql(self, question: str) -> str:
        sql_query = self.chain.run(question=question)
        sql_query = self._sanitize_sql(sql_query)
        return sql_query

    def _sanitize_sql(self, sql: str) -> str:
        # Validación básica para seguridad
        sql_lower = sql.lower()
        if not sql_lower.startswith("select"):
            raise ValueError("Solo se permiten consultas SELECT.")
        if any(word in sql_lower for word in ["drop", "delete", "update", "insert"]):
            raise ValueError("Consulta SQL contiene comandos no permitidos.")
        # Limitar resultados con LIMIT si no existe
        if "limit" not in sql_lower:
            sql += " LIMIT 100"
        return sql

    def execute_sql(self, sql: str):
        return self.sql_tool._run(sql)

    def generate_plot(self, data):
        return self.plot_tool._run(data)

    def save_file(self, data):
        return self.file_tool._run(data)

    def handle_question(self, question: str):
        try:
            sql = self.nl_to_sql(question)
            result = self.execute_sql(sql)
            # Simplificación: decidir acción por palabras clave en la pregunta
            if "gráfico" in question.lower() or "grafico" in question.lower():
                return self.generate_plot(result)
            elif "archivo" in question.lower() or "csv" in question.lower() or "excel" in question.lower():
                return self.save_file(result)
            else:
                return result
        except Exception as e:
            return f"Error: {e}"

# Ejemplo rápido de uso
if __name__ == "__main__":
    agent = CoreAgent()
    q1 = "Top 5 productos más vendidos en Medellín"
    print(agent.handle_question(q1))

    q2 = "Guarda las ventas por vendedor en un archivo CSV"
    print(agent.handle_question(q2))

    q3 = "Quién fue el vendedor con más ventas en Bogotá"
    print(agent.handle_question(q3))

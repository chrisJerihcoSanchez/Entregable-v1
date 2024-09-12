from flask import (
    Flask,
    render_template,
    request,
)
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import csv

app = Flask(__name__)
app.secret_key = "supersecretkey" 


def leer_csv_seguro(path):
    try:
        # Primer intento: Leer con configuración que maneja campos que contienen comillas y comas
        df = pd.read_csv(path, quoting=csv.QUOTE_ALL, escapechar="\\")
    except pd.errors.ParserError:
        try:
            # Segundo intento: Usar el motor Python para manejar casos más complejos
            df = pd.read_csv(
                path, quoting=csv.QUOTE_ALL, escapechar="\\", engine="python"
            )
        except Exception as e:
            print(f"Error al leer el archivo CSV: {e}")
            # Si todo falla, leer el archivo línea por línea
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()
            # Procesar manualmente las líneas
            headers = lines[0].strip().split(",")
            data = []
            for line in lines[1:]:
                fields = line.strip().split(",")
                # Asegurar que tenemos el número correcto de campos
                if len(fields) < len(headers):
                    fields.extend([""] * (len(headers) - len(fields)))
                elif len(fields) > len(headers):
                    # Combinar campos extra en el último campo (asumiendo que es la URL)
                    fields = fields[: len(headers) - 1] + [
                        ",".join(fields[len(headers) - 1 :])
                    ]
                data.append(fields)
            df = pd.DataFrame(data, columns=headers)

    return df


def limpiar_dataframe(df):
    # Elimina columnas no deseadas
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    # Elimina filas con valores nulos en todas las columnas
    df = df.dropna(how="all")
    return df


# Leer el archivo CSV de forma segura
productos = leer_csv_seguro("files/productos.csv")
limpiar_dataframe(productos)


def generate_recommendations(interests):
    # Asegurarse de que la columna 'categoria' no tenga valores NaN
    productos["categoria"] = productos["categoria"].fillna("")

    # Crear una lista de productos recomendados
    recommendations = []
    for interest in interests.split(","):
        interest = interest.strip().lower()
        for index, row in productos.iterrows():
            # Verificar si la categoría contiene el interés especificado
            if (
                isinstance(row["categoria"], str)
                and interest in row["categoria"].lower()
            ):
                recommendations.append(row)

    # Convertir la lista de productos recomendados a un DataFrame
    recommendations_df = pd.DataFrame(recommendations)
    return recommendations_df


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/recommendations", methods=["POST"])
def recommendations():
    interests = request.form.get("interests", "")
    if interests:
        recommended_products = generate_recommendations(interests)
    else:
        recommended_products = pd.DataFrame()  # No hay recomendaciones

    # Convertir el DataFrame a una lista de diccionarios
    recommendations_list = recommended_products.to_dict(orient="records")
    return render_template("index.html", recommendations=recommendations_list)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

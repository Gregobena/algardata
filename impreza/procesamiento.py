"""
Carga los archivos maestros de Clientes y Articulos exportados desde Impreza
(los que vienen sin extension, separados por ';') y los convierte en
DataFrames de pandas listos para trabajar.
"""

import pandas as pd


def _limpiar_texto(df):
    # los campos de texto vienen con relleno de espacios (formato de ancho fijo)
    # esto recorre solo las columnas de tipo texto y les saca los espacios de mas
    columnas_texto = df.select_dtypes(include="object").columns
    for columna in columnas_texto:
        df[columna] = df[columna].str.strip()
    return df


def _sacar_columnas_vacias(df):
    # el export siempre trae unas columnas finales sin nombre y vacias (basura)
    columnas_unnamed = [c for c in df.columns if c.startswith("Unnamed")]
    return df.drop(columns=columnas_unnamed)


def cargar_clientes(ruta_archivo):
    """
    Lee el archivo de clientes (Clientes_Ordenados_Alfabeticamente_con_Codigo)
    y devuelve un DataFrame con una fila por cliente.
    """
    df = pd.read_csv(
        ruta_archivo,
        sep=";",
        encoding="latin-1",
        lineterminator="\r",
        on_bad_lines="skip",  # algunas filas tienen un ';' de mas dentro del domicilio y se descartan
    )
    df = _sacar_columnas_vacias(df)
    df = _limpiar_texto(df)
    return df


def cargar_articulos(ruta_archivo):
    """
    Lee el archivo de articulos (Articulos_ordenados_por_codigo)
    y devuelve un DataFrame con una fila por articulo/servicio.
    """
    df = pd.read_csv(
        ruta_archivo,
        sep=";",
        encoding="latin-1",
        lineterminator="\r",
        on_bad_lines="skip",
    )
    df = _sacar_columnas_vacias(df)
    df = _limpiar_texto(df)
    return df


# cambiar por la ruta real de cada archivo
clientes = cargar_clientes(r"C:\Users\geono\OneDrive\Desktop\ALGARDATA\impreza\raw_data\Clientes_Ordenados_Alfabeticamente_con_Codigo")
articulos = cargar_articulos(r"C:\Users\geono\OneDrive\Desktop\ALGARDATA\impreza\raw_data\Articulos_ordenados_por_codigo")

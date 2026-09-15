"""
Script de limpieza para el dataset de CASOS (Tickets).

Flujo del script:
1. Se carga el archivo Excel original.
2. Se aplica una limpieza general (tipos de datos, columnas y filas).
3. Se aplica una limpieza especifica del dataset de Casos.
4. Se agregan las columnas 'cant_tiempos' e 'id_tiempos', cruzando cada
   caso con los registros de tiempo (Horas) que tiene asignados.
5. Se muestra el DataFrame final ya purificado (df_casos).
"""

import pandas as pd

# --------------------------------------------------------------------------
# CONFIGURACION: modificar segun corresponda
# --------------------------------------------------------------------------
RUTA_ARCHIVO = "raw_data/casos.xlsx"
HOJA = "Tickets"

# Archivo de Horas, necesario para calcular 'cant_tiempos' e 'id_tiempos'
RUTA_HORAS = "raw_data/horas.xlsx"
HOJA_HORAS = "Carga de Tiempo"

# Columnas que se consideran imprescindibles para que una fila sea valida
COLUMNAS_RELEVANTES_CASOS = ["Nº", "Fecha de Inicio", "Título", "Cuenta"]


# --------------------------------------------------------------------------
# FUNCIONES DE LIMPIEZA GENERAL (aplicables a cualquier dataset)
# --------------------------------------------------------------------------

def cargar_datos(ruta, hoja=0):
    """
    Carga un archivo Excel en un DataFrame de pandas.
    """
    return pd.read_excel(ruta, sheet_name=hoja)


def convertir_columna(serie, umbral_exito=0.9):
    """
    Intenta convertir una columna (Serie) de tipo texto a un tipo de dato
    mas manipulable: duracion en minutos, numero o fecha/hora.

    Se prueba en este orden:
    1) Duracion tipo "H:MM" -> minutos totales (numero).
    2) Numero (entero o decimal).
    3) Fecha/hora (datetime).

    Si ninguna conversion logra un porcentaje de exito mayor al umbral
    indicado, la columna se devuelve sin modificar (solo con los nulos
    disfrazados ya reemplazados por NaN).
    """
    if not (serie.dtype == object or pd.api.types.is_string_dtype(serie)):
        return serie

    # Se reemplazan valores que en realidad representan "nulo"
    valores_nulos_disfrazados = ["―", "-", "", "nan", "NaN", "None", "null"]
    serie_limpia = serie.replace(valores_nulos_disfrazados, pd.NA)

    no_nulos = serie_limpia.dropna()
    if no_nulos.empty:
        return serie_limpia

    # 1) Formato de duracion "H:MM" -> minutos totales
    proporcion_duracion = no_nulos.astype(str).str.fullmatch(r"\d{1,3}:\d{2}").mean()
    if proporcion_duracion > umbral_exito:
        def a_minutos(valor):
            horas, minutos = str(valor).split(":")
            return int(horas) * 60 + int(minutos)
        convertida = serie_limpia.apply(lambda v: a_minutos(v) if pd.notna(v) else None)
        return pd.to_numeric(convertida, errors="coerce").astype("Int64")

    # 2) Numero (entero o decimal)
    numerico = pd.to_numeric(serie_limpia, errors="coerce")
    if numerico.notna().sum() / len(no_nulos) > umbral_exito:
        return numerico

    # 3) Fecha/hora
    fechas = pd.to_datetime(serie_limpia, errors="coerce", dayfirst=True, format="mixed")
    if fechas.notna().sum() / len(no_nulos) > umbral_exito:
        return fechas

    return serie_limpia


def convertir_tipos(df):
    """
    Recorre todas las columnas del DataFrame e intenta convertirlas a un
    tipo de dato mas manipulable (ver convertir_columna).
    """
    df = df.copy()
    for columna in df.columns:
        df[columna] = convertir_columna(df[columna])
    return df


def eliminar_columnas_nulos(df, umbral=0.9):
    """
    Elimina las columnas cuya proporcion de valores nulos es mayor al
    umbral indicado (por defecto, mas del 90% de nulos).
    """
    proporcion_nulos = df.isna().mean()
    columnas_a_eliminar = proporcion_nulos[proporcion_nulos > umbral].index
    return df.drop(columns=columnas_a_eliminar)


def eliminar_columnas_baja_varianza(df, umbral=0.95):
    """
    Elimina las columnas que casi siempre tienen el mismo valor (baja
    varianza), ya que no aportan informacion util para el analisis.
    """
    columnas_a_eliminar = []
    for columna in df.columns:
        proporcion_max = df[columna].value_counts(normalize=True, dropna=False).iloc[0]
        if proporcion_max > umbral:
            columnas_a_eliminar.append(columna)
    return df.drop(columns=columnas_a_eliminar)


def eliminar_filas_nulos(df, columnas_relevantes=None, umbral_fila=0.5):
    """
    Elimina las filas que tienen demasiados valores nulos (mas del
    umbral_fila indicado sobre el total de columnas) o que tienen
    valores nulos en alguna de las columnas consideradas relevantes.
    """
    proporcion_nulos_fila = df.isna().mean(axis=1)
    mascara_muchos_nulos = proporcion_nulos_fila > umbral_fila

    if columnas_relevantes:
        columnas_relevantes = [c for c in columnas_relevantes if c in df.columns]
        mascara_nulos_relevantes = df[columnas_relevantes].isna().any(axis=1)
    else:
        mascara_nulos_relevantes = pd.Series(False, index=df.index)

    return df[~(mascara_muchos_nulos | mascara_nulos_relevantes)].copy()


def limpieza_general(df, columnas_relevantes=None):
    """
    Aplica, en orden, todos los pasos de limpieza general:
    1) Elimina columnas con muchos nulos.
    2) Elimina columnas de baja varianza.
    3) Convierte los tipos de datos de las columnas restantes.
    4) Elimina filas con demasiados nulos o nulos en columnas relevantes.
    """
    df = eliminar_columnas_nulos(df)
    df = eliminar_columnas_baja_varianza(df)
    df = convertir_tipos(df)
    df = eliminar_filas_nulos(df, columnas_relevantes=columnas_relevantes)
    return df


# --------------------------------------------------------------------------
# FUNCIONES DE LIMPIEZA ESPECIFICA DE CASOS
# --------------------------------------------------------------------------

def limpieza_especifica_casos(df):
    """
    Elimina columnas particulares del dataset de Casos que no aportan
    valor para el analisis.
    """
    columnas_a_eliminar = [
        "Tiempo Imputado",
        "Deslocation",
        "Tiempo de Viaje",
        "Pipeline desde el origen inicial",
        "Estado del pipeline de origen inicial",
        "Estado inicial de origen creado en",
        "Estado inicial del origen creado el",
        "Pipeline del origen final",
        "Estado del pipeline del origen final",
        "Estado final del origen creado en",
        "Estado final del origen creado el",
        "Historial de los estados del origen",
    ]
    return df.drop(columns=columnas_a_eliminar, errors="ignore")


def agregar_columnas_tiempos_casos(df, ruta_horas, hoja_horas=0):
    """
    Crea dos columnas en el dataset de Casos a partir de los registros
    de tiempo cargados en el archivo de Horas:
    - 'cant_tiempos': cantidad de tiempos asignados a cada caso.
    - 'id_tiempos'  : lista con los numeros (columna 'Nº' de Horas) de
                      esos tiempos.

    Para relacionar ambos archivos se extrae, de la columna 'Origen' de
    Horas, el numero de caso (solo para los registros cuyo origen es un
    'Caso'), y se lo cruza con el numero de caso (columna 'Nº') de Casos.
    """
    horas = pd.read_excel(ruta_horas, sheet_name=hoja_horas)
    horas_de_casos = horas[horas["Tipo de fuente"] == "Caso"].copy()
    horas_de_casos["id_caso"] = pd.to_numeric(
        horas_de_casos["Origen"].str.extract(r"Nº:\s*(\d+)")[0], errors="coerce"
    )

    resumen = horas_de_casos.groupby("id_caso")["Nº"].agg(
        cant_tiempos="count", id_tiempos=list
    )

    df = df.merge(resumen, how="left", left_on="Nº", right_index=True)
    df["cant_tiempos"] = df["cant_tiempos"].fillna(0).astype(int)
    df["id_tiempos"] = df["id_tiempos"].apply(lambda x: x if isinstance(x, list) else [])
    return df


# --------------------------------------------------------------------------
# FUNCION OPCIONAL: FILTRAR POR RANGO DE FECHAS (desactivada por defecto)
# --------------------------------------------------------------------------

def filtrar_por_rango_fechas(df, columna_fecha, fecha_inicio, fecha_fin):
    """
    Devuelve solo las filas cuya fecha (en columna_fecha) esta entre
    fecha_inicio y fecha_fin, ambas incluidas.

    fecha_inicio y fecha_fin deben ser objetos datetime, por ejemplo:
    datetime(2026, 7, 1) representa el dia 1, mes 7, año 2026 (d-m-Y).
    """
    return df[(df[columna_fecha] >= fecha_inicio) & (df[columna_fecha] <= fecha_fin)].copy()


# --------------------------------------------------------------------------
# EJECUCION DEL SCRIPT
# --------------------------------------------------------------------------

df_casos = cargar_datos(RUTA_ARCHIVO, HOJA)
df_casos = limpieza_general(df_casos, columnas_relevantes=COLUMNAS_RELEVANTES_CASOS)
df_casos = limpieza_especifica_casos(df_casos)
df_casos = agregar_columnas_tiempos_casos(df_casos, RUTA_HORAS, HOJA_HORAS)

# ---- Filtro opcional por rango de fechas (desactivado) ----
# Para activarlo, descomentar las siguientes lineas y asignar las fechas
# deseadas en formato dia-mes-año.
from datetime import datetime
fecha_inicio = datetime(2026, 1, 1)   
fecha_fin = datetime(2026, 5, 31)     
df_casos = filtrar_por_rango_fechas(df_casos, "Fecha de Inicio", fecha_inicio, fecha_fin)

print(df_casos.shape)
print(df_casos.dtypes)
print(df_casos.head())

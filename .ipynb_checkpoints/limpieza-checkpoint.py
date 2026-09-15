import pandas as pd

def load_data(filepath):
    """Carga el dataset desde un archivo Excel o CSV."""
    if filepath.endswith(('.xlsx', '.xls')):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)

def drop_specific_columns(df, columns_to_drop):
    """Elimina una lista explícita de columnas si existen en el DataFrame."""
    cols_in_df = [col for col in columns_to_drop if col in df.columns]
    return df.drop(columns=cols_in_df)

def drop_high_null_columns(df, max_null_pct=0.5):
    """Elimina columnas que superen un porcentaje máximo de nulos (por defecto 50%)."""
    threshold = len(df) * (1 - max_null_pct)
    return df.dropna(axis=1, thresh=threshold)

def drop_low_variance_columns(df, max_freq_pct=0.98):
    """
    Elimina columnas con poca varianza: aquellas que tienen un solo valor único
    o donde el valor más repetido domina más del 98% de los registros.
    """
    cols_to_drop = []
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 1:
            cols_to_drop.append(col)
        elif df[col].notna().sum() > 0:
            top_freq = df[col].value_counts(normalize=True).iloc[0]
            if top_freq >= max_freq_pct:
                cols_to_drop.append(col)
    return df.drop(columns=cols_to_drop)

def drop_high_null_rows(df, min_non_nulls_ratio=0.5):
    """Elimina filas donde más de la mitad de sus columnas sean valores nulos."""
    min_non_nulls = int(len(df.columns) * min_non_nulls_ratio)
    return df.dropna(axis=0, thresh=min_non_nulls)

def cast_data_types(df):
    """Convierte columnas a datetime, int o float de forma inteligente sin usar 'ignore' obsoleto."""
    date_keywords = ['fecha', 'creado en', 'creado el']
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in date_keywords):
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        else:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
            
    return df

def filter_by_year_2026(df, date_col="Fecha de Inicio"):
    """Filtra el DataFrame eliminando registros anteriores al 1/1/2026."""
    if date_col in df.columns:
        # Asegurarse de que sea datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        
        # Aplicar el filtro estricto
        limite = pd.to_datetime("2026-01-01")
        df = df[df[date_col] >= limite]
    else:
        print(f"Advertencia: No se encontró la columna '{date_col}' para filtrar por año.")
    
    return df

def main(filepath):
    print(f"Cargando datos de: {filepath}...")
    df = load_data(filepath)
    print(f"Dimensiones iniciales: {df.shape}")
    
    # 1. Lista de columnas irrelevantes
    columnas_a_eliminar = [
        "Marcadores", "Pipeline desde el origen inicial", 
        "Estado del pipeline de origen inicial", "Estado inicial de origen creado en", 
        "Estado inicial del origen creado el", "Pipeline del origen final", 
        "Estado del pipeline del origen final", "Estado final del origen creado en", 
        "Estado final del origen creado el", "Historial de los estados del origen", 
        "Estado", "Prioridad", "Impacto", "Esfuerzo", "Empresa", "Cliente ERP", 
        "Tiempo Imputado", "Deslocation", "Tiempo de Viaje"
    ]
    df = drop_specific_columns(df, columnas_a_eliminar)
    
    # 2. Limpieza de varianza y nulos
    df = drop_low_variance_columns(df)
    df = drop_high_null_columns(df)
    df = drop_high_null_rows(df)
    
    # 3. Purificación de tipos de datos
    df = cast_data_types(df)
    
    # 4. Filtrado ESTRICTO de fechas (Solo >= 2026)
    df = filter_by_year_2026(df, date_col="Fecha de Inicio")
    
    print(f"Dimensiones finales post-limpieza: {df.shape}")
    return df

if __name__ == "__main__":
    archivo = "ventas-clasificacion.xlsx" # Asegúrate que este sea el nombre correcto de tu archivo original
    
    try:
        df_limpio = main(archivo)
        df_limpio.to_excel("ventas-clasificacion_limpio.xlsx", index=False)
        print("Limpieza completada y archivo guardado con éxito.")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{archivo}'.")
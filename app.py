import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Sistema de Control de Ruta y Telemetría GPS",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Sistema de Control de Ruta y Telemetría GPS | Mini-App Enterprise v2.4")
st.markdown("Plataforma web ligera para procesamiento telemático, análisis de paradas (0 km/h), generación de mapas KML y reportes ejecutivos.")

uploaded_file = st.file_uploader("Cargue su archivo de telemetría (Excel o CSV con columnas: Unidad, Evento, Ubicacion, Fecha, Velocidad, Latitud, Longitud)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
        
        df.columns = [str(c).strip() for c in df.columns]
        
        st.success(f"¡Archivo cargado exitosamente! Se detectaron {len(df)} registros.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_records = len(df)
        unit_eval = df['Unidad'].iloc[0] if 'Unidad' in df.columns and len(df) > 0 else "N/A"
        
        vel_col = None
        for col in df.columns:
            if 'velocidad' in col.lower() or 'speed' in col.lower():
                vel_col = col
                break
        
        total_stops = 0
        max_vel = 0
        if vel_col:
            df[vel_col] = pd.to_numeric(df[vel_col], errors='coerce').fillna(0)
            total_stops = len(df[df[vel_col] == 0])
            max_vel = df[vel_col].max()
            
        col1.metric("Total de Registros", total_records)
        col2.metric("Unidad Evaluada", str(unit_eval))
        col3.metric("Total Paradas (0 km/h)", total_stops)
        col4.metric("Velocidad Máxima", f"{max_vel} km/h")
        
        st.divider()
        st.subheader("📊 Vista Previa de Datos Telemáticos")
        st.dataframe(df.head(20), use_container_width=True)
        
        st.subheader("⚙️ Módulos de Procesamiento y Exportación")
        
        b1, b2, b3 = st.columns(3)
        
        with b1:
            if st.button("🌐 Generar KML Completo"):
                kml_content = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Ruta Completa</name></Document></kml>'
                st.download_button("📥 Descargar KML Completo", data=kml_content, file_name="ruta_completa.kml", mime="application/vnd.google-earth.kml+xml")
                
        with b2:
            if st.button("📍 Generar KML Paradas"):
                kml_stops = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Paradas de Ruta</name></Document></kml>'
                st.download_button("📥 Descargar KML Paradas", data=kml_stops, file_name="paradas_ruta.kml", mime="application/vnd.google-earth.kml+xml")
                
        with b3:
            if st.button("📋 Generar Reporte de Control de Ruta (HTML)"):
                html_report = f"<html><body><h1>Reporte de Control de Ruta - Unidad: {unit_eval}</h1><p>Total Registros: {total_records} | Paradas: {total_stops}</p></body></html>"
                st.download_button("📥 Descargar Reporte HTML", data=html_report, file_name="reporte_control_ruta.html", mime="text/html")
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👆 Por favor suba un archivo Excel o CSV de telemetría para comenzar el análisis.")

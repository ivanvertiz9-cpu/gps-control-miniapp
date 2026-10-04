import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Sistema de Control de Ruta y Telemetría GPS",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Sistema de Control de Ruta y Telemetría GPS | Mini-App Enterprise v2.4")
st.markdown("Plataforma web ligera para procesamiento telemático, análisis de paradas (0 km/h), generación de mapas KML y reportes ejecutivos.")

uploaded_file = st.file_uploader("Cargue su archivo de telemetría (Excel o CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, skiprows=4)
        
        df.columns = [str(c).strip() for c in df.columns]
        
        # Detección inteligente y flexible de columnas clave
        unidad_col = next((c for c in df.columns if 'unidad' in c.lower()), df.columns[0])
        vel_col = next((c for c in df.columns if 'velocidad' in c.lower() or 'speed' in c.lower()), None)
        
        # Detección de coordenadas por nombre o por posición estricta (Columna F y G)
        lat_col = next((c for c in df.columns if 'lat' in c.lower()), None)
        lon_col = next((c for c in df.columns if 'lon' in c.lower() or 'long' in c.lower()), None)
        
        if not lat_col and len(df.columns) > 5:
            lat_col = df.columns[5] # Columna F
        if not lon_col and len(df.columns) > 6:
            lon_col = df.columns[6] # Columna G
            
        total_records = len(df)
        unit_eval = df[unidad_col].iloc[0] if unidad_col in df.columns and len(df) > 0 else "N/A"
        
        total_stops = 0
        max_vel = 0
        if vel_col:
            df[vel_col] = pd.to_numeric(df[vel_col], errors='coerce').fillna(0)
            total_stops = len(df[df[vel_col] == 0])
            max_vel = df[vel_col].max()
            
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Registros", total_records)
        col2.metric("Unidad Evaluada", str(unit_eval))
        col3.metric("Total Paradas (0 km/h)", total_stops)
        col4.metric("Velocidad Máxima", f"{max_vel} km/h")
        
        st.divider()
        st.subheader("📊 Vista Previa de Datos Telemáticos")
        st.dataframe(df.head(20), use_container_width=True)
        
        st.subheader("⚙️ Módulos de Procesamiento y Exportación OSRM")
        
        # Función espejo de tu macro VBA para consultar OSRM
        def obtener_ruta_osrm(dataframe, lat_c, lon_c):
            coords = []
            ultima = len(dataframe)
            paso = max(1, int(ultima / 60)) if ultima > 80 else 1
            
            for i in range(0, ultima, paso):
                row = dataframe.iloc[i]
                try:
                    lat = float(row[lat_c])
                    lon = float(row[lon_c])
                    if lat < 0 and lon > 0:
                        lat, lon = lon, lat
                    if lon > 80 and lon < 120:
                        lon = -lon
                    if 10 <= lat <= 40 and -130 <= lon <= -70:
                        coords.append(f"{lon},{lat}")
                except:
                    pass
            
            if len(coords) < 2:
                return ""
            
            coords_param = ";".join(coords)
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_param}?overview=full&geometries=geojson"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "routes" in data and len(data["routes"]) > 0:
                        geometry = data["routes"][0]["geometry"]["coordinates"]
                        kml_coords = []
                        for pt in geometry:
                            cLon, cLat = pt[0], pt[1]
                            if 10 <= cLat <= 40 and -130 <= cLon <= -70:
                                kml_coords.append(f"{cLon},{cLat},0")
                        return " ".join(kml_coords)
            except:
                pass
            
            # Respaldo en línea recta si OSRM no responde
            fallback = []
            for _, row in dataframe.iterrows():
                try:
                    lat = float(row[lat_c])
                    lon = float(row[lon_c])
                    if lat < 0 and lon > 0:
                        lat, lon = lon, lat
                    if lon > 80 and lon < 120:
                        lon = -lon
                    fallback.append(f"{lon},{lat},0")
                except:
                    pass
            return " ".join(fallback)

        b1, b2, b3 = st.columns(3)
        
        with b1:
            if st.button("🌐 Generar KML Completo con Carreteras (OSRM)"):
                if lat_col and lon_col:
                    with st.spinner("Conectando con motor de enrutamiento OSRM..."):
                        coords_str = obtener_ruta_osrm(df, lat_col, lon_col)
                    
                    kml_c = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Ruta Carretera - Unidad {unit_eval}</name>
    <Style id="estiloLineaNavegacion">
      <LineStyle><color>ffFF8800</color><width>5</width></LineStyle>
    </Style>
    <Placemark>
      <name>Trayecto Carretera</name>
      <styleUrl>#estiloLineaNavegacion</styleUrl>
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>{coords_str}</coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Completo", data=kml_c, file_name=f"ruta_carretera_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("No se detectaron las columnas de coordenadas.")
                
        with b2:
            if st.button("📍 Generar KML Paradas (0 km/h)"):
                if lat_col and lon_col and vel_col:
                    paradas_df = df[df[vel_col] == 0]
                    placemarks = []
                    for _, row in paradas_df.iterrows():
                        try:
                            lat = float(row[lat_col])
                            lon = float(row[lon_col])
                            if lat < 0 and lon > 0:
                                lat, lon = lon, lat
                            if lon > 80 and lon < 120:
                                lon = -lon
                            evento = row.get('Evento', 'Parada')
                            fecha = row.get('Fecha', '')
                            ubicacion = row.get('Ubicacion', '')
                            placemarks.append(f"""
    <Placemark>
      <name>Parada (0 km/h)</name>
      <description><![CDATA[<b>Unidad:</b> {unit_eval}<br><b>Fecha:</b> {fecha}<br><b>Ubicación:</b> {ubicacion}]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")
                        except:
                            pass
                    
                    kml_p = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Paradas - Unidad {unit_eval}</name>
    {''.join(placemarks)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Paradas", data=kml_p, file_name=f"paradas_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan columnas necesarias para paradas.")
                
        with b3:
            if st.button("📋 Generar Reporte de Control de Ruta (HTML)"):
                html_report = f"""<html>
<head><meta charset="utf-8"><title>Reporte Control de Ruta</title></head>
<body style="font-family:Arial; padding:20px;">
  <h2>Reporte Oficial de Control de Ruta y Telemetría</h2>
  <hr>
  <p><b>Unidad Evaluada:</b> {unit_eval}</p>
  <p><b>Total de Registros Procesados:</b> {total_records}</p>
  <p><b>Total de Paradas detectadas (0 km/h):</b> {total_stops}</p>
  <p><b>Velocidad Máxima Registrada:</b> {max_vel} km/h</p>
  <br>
  <p><i>Generado automáticamente por Mini-App Enterprise v2.4</i></p>
</body>
</html>"""
                st.download_button("📥 Descargar Reporte HTML", data=html_report, file_name=f"reporte_{unit_eval}.html", mime="text/html")
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👆 Por favor suba un archivo Excel o CSV de telemetría para comenzar el análisis.")

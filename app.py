import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Sistema de Control de Ruta y Telemetría GPS",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Sistema de Control de Ruta y Telemetría GPS | Mini-App Enterprise v2.4")
st.markdown("Plataforma web con corrección automática de coordenadas y marcadores telemáticos.")

uploaded_file = st.file_uploader("Cargue su archivo de telemetría (Excel o CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file, header=None)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
        
        header_row_idx = 0
        for idx, row in df_raw.iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            if ('unidad' in row_str or 'vehicle' in row_str) and ('lat' in row_str or 'velocidad' in row_str):
                header_row_idx = idx
                break
        
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=header_row_idx)
        else:
            df = pd.read_excel(uploaded_file, header=header_row_idx)
        
        df.columns = [str(c).strip() for c in df.columns]
        
        unidad_col = next((c for c in df.columns if 'unidad' in c.lower()), df.columns[0] if len(df.columns) > 0 else None)
        evento_col = next((c for c in df.columns if 'evento' in c.lower()), df.columns[1] if len(df.columns) > 1 else None)
        ubicacion_col = next((c for c in df.columns if 'ubicacion' in c.lower() or 'ubicación' in c.lower()), df.columns[2] if len(df.columns) > 2 else None)
        fecha_col = next((c for c in df.columns if 'fecha' in c.lower()), df.columns[3] if len(df.columns) > 3 else None)
        vel_col = next((c for c in df.columns if 'velocidad' in c.lower() or 'speed' in c.lower()), df.columns[4] if len(df.columns) > 4 else None)
        lat_col = next((c for c in df.columns if 'latitud' in c.lower() or 'lat' in c.lower()), df.columns[5] if len(df.columns) > 5 else None)
        lon_col = next((c for c in df.columns if 'longitud' in c.lower() or 'lon' in c.lower() or 'long' in c.lower()), df.columns[6] if len(df.columns) > 6 else None)
        
        total_records = len(df)
        unit_eval = df[unidad_col].iloc[0] if unidad_col and len(df) > 0 else "N/A"
        
        total_stops = 0
        max_vel = 0
        if vel_col:
            df[vel_col] = pd.to_numeric(df[vel_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
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
        
        st.subheader("⚙️ Módulos de Procesamiento y Exportación KML")
        
        def procesar_lat_lon(raw_lat, raw_lon):
            try:
                lat = float(str(raw_lat).strip().replace(',', '.'))
                lon = float(str(raw_lon).strip().replace(',', '.'))
                
                if abs(lat) > 50 and abs(lon) < 50:
                    lat, lon = lon, lat
                
                if lon > 0:
                    lon = -lon
                    
                return lat, lon
            except:
                return 0.0, 0.0

        def obtener_ruta_osrm_segura(dataframe, lat_c, lon_c):
            coords = []
            ultima = len(dataframe)
            paso = max(1, int(ultima / 40)) if ultima > 50 else 1
            
            for i in range(0, ultima, paso):
                row = dataframe.iloc[i]
                lat, lon = procesar_lat_lon(row[lat_c], row[lon_c])
                if 14 <= lat <= 33 and -118 <= lon <= -85:
                    coords.append(f"{lon},{lat}")
            
            if len(coords) < 2:
                fallback = []
                for _, row in dataframe.iterrows():
                    lat, lon = procesar_lat_lon(row[lat_c], row[lon_c])
                    if lat != 0 and lon != 0:
                        fallback.append(f"{lon},{lat},0")
                return " ".join(fallback)
            
            coords_param = ";".join(coords[:50])
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_param}?overview=full&geometries=geojson"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "routes" in data and len(data["routes"]) > 0:
                        geometry = data["routes"][0]["geometry"]["coordinates"]
                        kml_coords = []
                        for pt in geometry:
                            kml_coords.append(f"{pt[0]},{pt[1]},0")
                        return " ".join(kml_coords)
            except:
                pass
            
            fallback = []
            for _, row in dataframe.iterrows():
                lat, lon = procesar_lat_lon(row[lat_c], row[lon_c])
                if lat != 0 and lon != 0:
                    fallback.append(f"{lon},{lat},0")
            return " ".join(fallback)

        b1, b2, b3 = st.columns(3)
        
        with b1:
            if st.button("🌐 Generar KML Completo con Carreteras y Pines"):
                if lat_col and lon_col:
                    with st.spinner("Procesando ruta terrestre y pines..."):
                        coords_str = obtener_ruta_osrm_segura(df, lat_col, lon_col)
                        
                        placemarks_pines = []
                        for _, row in df.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if lat != 0 and lon != 0:
                                vel = float(row[vel_col]) if vel_col else 0
                                ev = row[evento_col] if evento_col in df.columns else 'Reporte'
                                fec = row[fecha_col] if fecha_col in df.columns else ''
                                ubi = row[ubicacion_col] if ubicacion_col in df.columns else ''
                                
                                if vel == 0:
                                    estilo = "#pinRojo"
                                elif vel <= 40:
                                    estilo = "#pinAmarillo"
                                else:
                                    estilo = "#pinVerde"
                                    
                                desc = f"<b>Unidad:</b> {unit_eval}<br><b>Evento:</b> {ev}<br><b>Fecha:</b> {fec}<br><b>Velocidad:</b> {vel} km/h<br><b>Ubicación:</b> {ubi}"
                                
                                placemarks_pines.append(f"""
    <Placemark>
      <name>{unit_eval} ({vel} km/h)</name>
      <styleUrl>{estilo}</styleUrl>
      <description><![CDATA[{desc}]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")

                    kml_c = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Ruta y Telemetría - Unidad {unit_eval}</name>
    <Style id="pinRojo"><IconStyle><scale>1.0</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href></Icon></IconStyle></Style>
    <Style id="pinAmarillo"><IconStyle><scale>1.0</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon></IconStyle></Style>
    <Style id="pinVerde"><IconStyle><scale>1.0</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle></Style>
    <Style id="lineaRuta"><LineStyle><color>ffFF8800</color><width>4</width></LineStyle></Style>
    <Placemark>
      <name>Trayecto Carretera</name>
      <styleUrl>#lineaRuta</styleUrl>
      <LineString><tessellate>1</tessellate><coordinates>{coords_str}</coordinates></LineString>
    </Placemark>
    {''.join(placemarks_pines)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Completo", data=kml_c, file_name=f"ruta_completa_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan columnas de coordenadas.")
                
        with b2:
            if st.button("📍 Generar KML Paradas (0 km/h)"):
                if lat_col and lon_col and vel_col:
                    paradas_df = df[df[vel_col] == 0]
                    placemarks = []
                    for _, row in paradas_df.iterrows():
                        lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                        if lat != 0 and lon != 0:
                            ev = row[evento_col] if evento_col in df.columns else 'Parada'
                            fec = row[fecha_col] if fecha_col in df.columns else ''
                            ubi = row[ubicacion_col] if ubicacion_col in df.columns else ''
                            placemarks.append(f"""
    <Placemark>
      <name>Parada (0 km/h)</name>
      <description><![CDATA[<b>Unidad:</b> {unit_eval}<br><b>Fecha:</b> {fec}<br><b>Ubicación:</b> {ubi}]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")
                    
                    kml_p = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Paradas - Unidad {unit_eval}</name>
    {''.join(placemarks)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Paradas", data=kml_p, file_name=f"paradas_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan columnas para procesar paradas.")
                
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

import streamlit as st
import pandas as pd
import requests
import time
import io
from datetime import datetime

st.set_page_config(
    page_title="Sistema de Control de Ruta y Telemetría GPS",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Sistema de Control de Ruta y Telemetría GPS | Mini-App Enterprise v2.4")
st.markdown("Plataforma web con enrutamiento OSRM, geocodificación y bitácora de control de ruta (Orígenes, Paradas y Destino).")

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
        
        if fecha_col and fecha_col in df.columns:
            try:
                df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')
                df = df.sort_values(by=fecha_col, ascending=True).reset_index(drop=True)
            except:
                pass

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
        
        st.subheader("⚙️ Módulos de Procesamiento y Exportación KML / Excel / HTML")
        
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

        def obtener_ruta_osrm_por_lotes(dataframe, lat_c, lon_c):
            puntos_totales = []
            for _, row in dataframe.iterrows():
                lat, lon = procesar_lat_lon(row[lat_c], row[lon_c])
                if 14 <= lat <= 33 and -118 <= lon <= -85:
                    puntos_totales.append((lon, lat))
            
            if len(puntos_totales) < 2:
                return ""
            
            chunk_size = 40
            chunks = [puntos_totales[i:i + chunk_size] for i in range(0, len(puntos_totales), chunk_size - 1)]
            kml_road_coords = []
            
            for chunk in chunks:
                if len(chunk) < 2:
                    continue
                coords_param = ";".join([f"{pt[0]},{pt[1]}" for pt in chunk])
                url = f"http://router.project-osrm.org/route/v1/driving/{coords_param}?overview=full&geometries=geojson"
                try:
                    response = requests.get(url, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        if "routes" in data and len(data["routes"]) > 0:
                            geometry = data["routes"][0]["geometry"]["coordinates"]
                            for pt in geometry:
                                kml_road_coords.append(f"{pt[0]},{pt[1]},0")
                            continue
                except:
                    pass
                for pt in chunk:
                    kml_road_coords.append(f"{pt[0]},{pt[1]},0")
            
            return " ".join(kml_road_coords)

        b1, b2, b3, b4 = st.columns(4)
        
        with b1:
            if st.button("🌐 KML Completo"):
                if lat_col and lon_col:
                    with st.spinner("Generando ruta completa..."):
                        coords_str = obtener_ruta_osrm_por_lotes(df, lat_col, lon_col)
                        placemarks_pines = []
                        for _, row in df.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if lat != 0 and lon != 0:
                                vel = float(row[vel_col]) if vel_col else 0
                                ev = row[evento_col] if evento_col in df.columns else 'Reporte'
                                fec = str(row[fecha_col]) if fecha_col in df.columns else ''
                                ubi = row[ubicacion_col] if ubicacion_col in df.columns else ''
                                estilo = "#pinRojo" if vel == 0 else ("#pinAmarillo" if vel <= 40 else "#pinVerde")
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
    <Style id="lineaRuta"><LineStyle><color>ff0000ff</color><width>4</width></LineStyle></Style>
    <Placemark>
      <name>Trayecto Vial Real</name>
      <styleUrl>#lineaRuta</styleUrl>
      <LineString><tessellate>1</tessellate><coordinates>{coords_str}</coordinates></LineString>
    </Placemark>
    {''.join(placemarks_pines)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML", data=kml_c, file_name=f"ruta_completa_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan coordenadas.")
                
        with b2:
            if st.button("📍 KML Paradas"):
                if lat_col and lon_col and vel_col:
                    with st.spinner("Calculando ruta y paradas..."):
                        coords_str = obtener_ruta_osrm_por_lotes(df, lat_col, lon_col)
                        lat_ini, lon_ini = 0, 0
                        lat_fin, lon_fin = 0, 0
                        for _, row in df.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if lat != 0 and lon != 0:
                                lat_ini, lon_ini = lat, lon
                                break
                        for _, row in df.iloc[::-1].iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if lat != 0 and lon != 0:
                                lat_fin, lon_fin = lat, lon
                                break
                        
                        kml_elements = []
                        if coords_str:
                            kml_elements.append(f"""
    <Placemark>
      <name>Ruta Carretera</name>
      <styleUrl>#estiloLineaNavegacion</styleUrl>
      <LineString><tessellate>1</tessellate><coordinates>{coords_str}</coordinates></LineString>
    </Placemark>""")
                        if lat_ini != 0:
                            kml_elements.append(f"""
    <Placemark>
      <name>ORIGEN / INICIO</name>
      <styleUrl>#pinInicio</styleUrl>
      <Point><coordinates>{lon_ini},{lat_ini},0</coordinates></Point>
    </Placemark>""")

                        contador_paradas = 0
                        for _, row in df.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if lat != 0 and lon != 0:
                                vel = float(row[vel_col]) if vel_col else 0
                                fec = str(row[fecha_col]) if fecha_col in df.columns else ''
                                ubi = row[ubicacion_col] if ubicacion_col in df.columns else ''
                                if vel == 0:
                                    contador_paradas += 1
                                    desc_parada = f"<b>[UNIDAD DETENIDA]</b><br><b>Unidad:</b> {unit_eval}<br><b>Fecha/Hora:</b> {fec}<br><b>Ubicación:</b> {ubi}"
                                    kml_elements.append(f"""
    <Placemark>
      <name>Parada #{contador_paradas} ({fec})</name>
      <styleUrl>#pinDetenido</styleUrl>
      <description><![CDATA[{desc_parada}]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")

                        if lat_fin != 0:
                            kml_elements.append(f"""
    <Placemark>
      <name>DESTINO / FIN</name>
      <styleUrl>#pinFin</styleUrl>
      <Point><coordinates>{lon_fin},{lat_fin},0</coordinates></Point>
    </Placemark>""")

                    kml_p = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Ruta de Navegación con Paradas - {unit_eval}</name>
    <Style id="estiloLineaNavegacion"><LineStyle><color>ffFF8800</color><width>5</width></LineStyle></Style>
    <Style id="pinInicio"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle></Style>
    <Style id="pinFin"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-square.png</href></Icon></IconStyle></Style>
    <Style id="pinDetenido"><IconStyle><scale>1.0</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon></IconStyle></Style>
    {''.join(kml_elements)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Paradas", data=kml_p, file_name=f"paradas_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan columnas necesarias.")
                
        with b3:
            if st.button("🔍 Extraer Ubicaciones"):
                if lat_col and lon_col and ubicacion_col:
                    with st.spinner("Consultando direcciones en OpenStreetMap..."):
                        progress_bar = st.progress(0)
                        total_filas = len(df)
                        df_geocoded = df.copy()
                        df_geocoded[ubicacion_col] = df_geocoded[ubicacion_col].astype(str)
                        
                        for idx, row in df_geocoded.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if 10 <= lat <= 35 and -120 <= lon <= -80:
                                url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
                                headers = {"User-Agent": "MiniAppEnterprise_GPS_Tool_v2"}
                                try:
                                    res = requests.get(url, headers=headers, timeout=5)
                                    if res.status_code == 200:
                                        data = res.json()
                                        display_name = data.get("display_name", "")
                                        if display_name:
                                            df_geocoded.at[idx, ubicacion_col] = display_name
                                        else:
                                            df_geocoded.at[idx, ubicacion_col] = "Ubicación no encontrada"
                                except:
                                    df_geocoded.at[idx, ubicacion_col] = "Error de conexión"
                                time.sleep(1.0)
                            else:
                                df_geocoded.at[idx, ubicacion_col] = "Coordenada fuera de rango"
                            progress_bar.progress(min(1.0, (idx + 1) / total_filas))
                        
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_geocoded.to_excel(writer, index=False, sheet_name='Telemetría Geocodificada')
                        excel_data = output.getvalue()
                        
                        st.success("¡Geocodificación completada!")
                        st.download_button("📥 Descargar Excel con Ubicaciones", data=excel_data, file_name=f"telemetria_ubicaciones_{unit_eval}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.error("No se detectó columna de ubicación.")

        with b4:
            if st.button("📋 Control de Ruta (HTML)"):
                if lat_col and lon_col and fecha_col:
                    with st.spinner("Generando reporte de control de ruta y paradas..."):
                        html_rows = []
                        contador_paso = 1
                        
                        # 1. ORIGEN (Primer punto válido)
                        for _, row in df.iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if 10 <= lat <= 35 and -120 <= lon <= -80:
                                f_val = str(row[fecha_col]) if fecha_col in df.columns else ""
                                u_val = str(row[ubicacion_col]) if ubicacion_col in df.columns else ""
                                html_rows.append(f"""<tr class="orig">
                                    <td>{contador_paso}</td>
                                    <td>ORIGEN / SALIDA</td>
                                    <td>{u_val}</td>
                                    <td>{lat:.4f}, {lon:.4f}</td>
                                    <td>{f_val}</td>
                                    <td>-</td>
                                    <td>-</td>
                                </tr>""")
                                contador_paso += 1
                                break
                        
                        # 2. INTERMEDIOS (Estrictamente Paradas de 0 km/h y su reinicio de marcha)
                        i = 0
                        while i < len(df):
                            row = df.iloc[i]
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            vel = float(row[vel_col]) if vel_col else 0
                            
                            if 10 <= lat <= 35 and -120 <= lon <= -80:
                                if vel == 0 and pd.notnull(row[fecha_col]):
                                    t_inicio = pd.to_datetime(row[fecha_col])
                                    ubi_parada = str(row[ubicacion_col]) if ubicacion_col in df.columns else ""
                                    lat_p, lon_p = lat, lon
                                    
                                    # Buscar el momento en que reinicia la marcha (> 0 km/h)
                                    j = i + 1
                                    t_fin = t_inicio
                                    texto_fin = "En detención"
                                    while j < len(df):
                                        next_row = df.iloc[j]
                                        next_vel = float(next_row[vel_col]) if next_vel else 0
                                        if next_vel > 0 and pd.notnull(next_row[fecha_col]):
                                            t_fin = pd.to_datetime(next_row[fecha_col])
                                            texto_fin = str(next_row[fecha_col])
                                            break
                                        j += 1
                                    
                                    if j >= len(df):
                                        ultima_valida = df.iloc[-1]
                                        if pd.notnull(ultima_valida[fecha_col]):
                                            t_fin = pd.to_datetime(ultima_valida[fecha_col])
                                            texto_fin = str(ultima_valida[fecha_col])
                                    
                                    minutos = int((t_fin - t_inicio).total_seconds() / 60)
                                    
                                    # Registrar solo si la parada es mayor a 5 minutos
                                    if minutos > 5:
                                        if minutos < 60:
                                            t_texto = f"{minutos} min"
                                        else:
                                            t_texto = f"{minutos // 60}h {minutos % 60}m"
                                            
                                        html_rows.append(f"""<tr class="parada">
                                            <td>{contador_paso}</td>
                                            <td>PARADA / DETENIDO</td>
                                            <td>{ubi_parada}</td>
                                            <td>{lat_p:.4f}, {lon_p:.4f}</td>
                                            <td>{t_inicio}</td>
                                            <td>{texto_fin}</td>
                                            <td class="tiempo">{t_texto}</td>
                                        </tr>""")
                                        contador_paso += 1
                                    
                                    i = j if j > i else i + 1
                                else:
                                    i += 1
                            else:
                                i += 1

                        # 3. DESTINO (Último punto válido)
                        for _, row in df.iloc[::-1].iterrows():
                            lat, lon = procesar_lat_lon(row[lat_col], row[lon_col])
                            if 10 <= lat <= 35 and -120 <= lon <= -80:
                                f_val = str(row[fecha_col]) if fecha_col in df.columns else ""
                                u_val = str(row[ubicacion_col]) if ubicacion_col in df.columns else ""
                                html_rows.append(f"""<tr class="dest">
                                    <td>{contador_paso}</td>
                                    <td>DESTINO / LLEGADA</td>
                                    <td>{u_val}</td>
                                    <td>{lat:.4f}, {lon:.4f}</td>
                                    <td>{f_val}</td>
                                    <td>-</td>
                                    <td>-</td>
                                </tr>""")
                                break

                        html_report = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Control de Ruta</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color: #1e293b; background-color: #f8fafc; }}
  .header {{ background-color: #0f172a; color: white; padding: 15px; text-align: center; border-radius: 6px; }}
  .sub {{ font-size: 11px; color: #94a3b8; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background-color: #1e293b; color: white; padding: 10px; font-size: 11px; text-align: left; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 11px; }}
  .orig {{ background-color: #dcfce7; font-weight: bold; }}
  .parada {{ background-color: #fee2e2; }}
  .dest {{ background-color: #e0e7ff; font-weight: bold; }}
  .tiempo {{ font-weight: bold; color: #991b1b; }}
  .no-print {{ margin-bottom: 15px; text-align: right; }}
  .btn-print {{ padding: 8px 16px; background: #0284c7; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }}
  @media print {{ body {{ background: white; margin: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
  <div class="no-print">
    <button class="btn-print" onclick="window.print()">🖨️️ Guardar como PDF / Imprimir</button>
  </div>
  <div class="header">
    <h2 style="margin:0;">CONTROL DE RUTA</h2>
    <div class="sub">Documento de Control de Tráfico (Paradas y Tiempos de Permanencia)</div>
  </div>
  <table>
    <thead>
      <tr>
        <th style="width:4%;">Movimiento</th>
        <th style="width:15%;">Tipo de Evento</th>
        <th style="width:33%;">Ubicación / Referencia</th>
        <th style="width:12%;">Coordenadas</th>
        <th style="width:13%;">Inicio de detenido</th>
        <th style="width:13%;">Fin / Reinicio</th>
        <th style="width:10%;">T. Detenido</th>
      </tr>
    </thead>
    <tbody>
      {''.join(html_rows)}
    </tbody>
  </table>
</body>
</html>"""
                        st.success("¡Reporte de Control de Ruta HTML generado con éxito!")
                        st.download_button(
                            "📥 Descargar Reporte HTML",
                            data=html_report,
                            file_name=f"control_ruta_{unit_eval}.html",
                            mime="text/html"
                        )
                else:
                    st.error("Faltan columnas de coordenadas o fecha.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👆 Por favor suba un archivo Excel o CSV de telemetría para comenzar el análisis.")

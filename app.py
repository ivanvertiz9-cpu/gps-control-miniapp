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

# ==========================================
# 🎨 ESTILOS CSS CON ALINEACIÓN PERFECTA
# ==========================================
st.markdown("""
<style>
    /* Fondo general de la aplicación */
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Estilo del título principal */
    h1 {
        color: #0f172a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    
    /* Estilo de los encabezados de sección */
    h2, h3 {
        color: #1e293b;
    }
    
    /* Personalización de la barra lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    
    /* 🚀 BOTONES Y ENLACES DE DESCARGA GRANDES Y VISIBLES */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #0284c7 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 18px !important;       
        padding: 1rem 1.5rem !important;  
        width: 100% !important;           
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #0369a1 !important;
        box-shadow: 0 6px 12px -1px rgba(0, 0, 0, 0.25) !important;
        transform: translateY(-2px);
    }
    
    div.stButton > button p, div.stDownloadButton > button p {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: white !important;
    }

    /* 🎯 ALINEACIÓN PERFECTA: Elimina el margen inferior predeterminado de Streamlit */
    div[data-testid="stHorizontalBlock"] div.stButton, 
    div[data-testid="stHorizontalBlock"] div.stDownloadButton {
        margin-bottom: -7px !important;
    }

    /* Tarjetas de métricas */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #0284c7;
    }
</style>
""", unsafe_allow_html=True)
st.title("🛰️ Sistema de Control de Ruta y Telemetría GPS | Mini-App Enterprise v2.7")
st.markdown("Plataforma web con detección de casetas, enrutamiento OSRM y reporte de control de ruta (Orígenes, Paradas y Destino).")
# ==========================================
# 📖 SECCIÓN DE MANUAL DE USUARIO / AYUDA
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/experimental-globe-zed.png", width=80)
    st.header("Panel de Control")
    
    # Botón en barra lateral para desplegar el manual de uso
    mostrar_manual = st.checkbox("📖 Ver Manual de Usuario", value=False)
    st.divider()

if mostrar_manual:
    with st.expander("📘 MANUAL DE USUARIO Y GUÍA DE OPERACIÓN", expanded=True):
        st.markdown("""
        ### Bienvenida al Sistema de Control de Ruta y Telemetría GPS
        Esta herramienta está diseñada para automatizar el análisis de telemetría vehicular, geocodificación, detección de casetas de peaje, generación de rutas en Google Earth (KML) y reportes ejecutivos en HTML/PDF.

        ---

        ### 📋 1. Requisitos del Archivo de Entrada (Excel / CSV)
        Para que la aplicación detecte automáticamente las columnas sin importar el orden, asegúrate de que tu archivo contenga encabezados que incluyan o se parezcan a:
        * **Unidad / Vehículo:** Identificador del tractocamión o unidad.
        * **Evento:** Descripción del evento reportado por el GPS.
        * **Ubicación:** Referencia textual o dirección reportada.
        * **Fecha / Hora:** Marca temporal del registro (indispensable para ordenar el trayecto cronológicamente).
        * **Velocidad / Speed:** Velocidad de desplazamiento en km/h.
        * **Latitud / Lat:** Coordenada de latitud.
        * **Longitud / Lon / Long:** Coordenada de longitud.

        ---

        ### 🛠️ 2. Descripción de Botones y Módulos de Exportación
        Una vez cargado y procesado tu archivo, aparecerán 4 opciones principales de exportación:

        1. **🌐 KML Completo:**
           * **Qué hace:** Traza la línea de recorrido vial real sobre las carreteras (usando OSRM) y coloca un pin en cada registro de telemetría.
           * **Colores de pines:** 🔴 Rojo (0 km/h - Detenido), 🟡 Amarillo (1 a 40 km/h - Tránsito lento), 🟢 Verde (> 40 km/h - Marcha regular).

        2. **📍 KML Paradas y Casetas:**
           * **Qué hace:** Genera un archivo limpio enfocado en la operación logística. Muestra el punto de **ORIGEN** (verde), cruza la ruta contra la base de datos de **Casetas de Peaje** (pines amarillos), marca exclusivamente las **Paradas de 0 km/h** con chinchetas rojas y finaliza con el **DESTINO** (cuadro rojo).

        3. **🔍 Extraer Ubicaciones:**
           * **Qué hace:** Utiliza geocodificación inversa en tiempo real (OpenStreetMap) para traducir coordenadas geográficas vacías a direcciones postales reales, entregando un Excel listo para auditoría.

        4. **📋 Control de Ruta (HTML):**
           * **Qué hace:** Crea un informe ejecutivo tabular detallando el **Origen**, los tiempos exactos de permanencia en **Paradas (> 5 minutos)** y el **Destino**. Incluye un botón integrado para imprimir o **Guardar como PDF** directamente desde tu navegador.

        ---

        ### ⚠️ Solución de Problemas Frecuentes
        * *Error al leer el archivo:* Verifica que tu archivo de Excel no tenga celdas combinadas en la fila de encabezados.
        * *Coordenadas invertidas:* El sistema cuenta con un autodetector inteligente que corrige automáticamente si la latitud y longitud vienen intercambiadas.
        """)
    st.divider()
# Base de datos integrada de Casetas (Nombre, Latitud, Longitud)
CASETAS_DB = [
    ("Esperanza", 18.870777, -97.385869), ("Amozoc II", 19.063585, -98.069075), ("Cantona", 19.507568, -97.497774),
    ("Cantona A1", 19.506554, -97.495453), ("Cantona A2", 19.509866, -97.497172), ("Cuapiaxtla", 19.310368, -97.797562),
    ("Cuapiaxtla A1", 19.304147, -97.805436), ("Cuapiaxtla A2", 19.304378, -97.805668), ("Perote", 19.55172, -97.289536),
    ("Cuyutlán", 18.927786, -104.081504), ("Arriaga", 16.245558, -93.880876), ("Jiquipilas", 16.620564, -93.60209),
    ("Ocozocuautla", 16.738493, -93.400414), ("Tierra y Libertad", 16.368058, -93.867043), ("Contepec", 19.876127, -100.177072),
    ("Contepec A1", 19.877644, -100.176358), ("Contepec A2", 19.875531, -100.176711), ("San Juanico", 19.830719, -99.905209),
    ("General Bravo", 25.813509, -99.169588), ("Los Herreras", 25.757295, -99.373856), ("Los Herreras", 25.759393, -99.37416),
    ("Los Ramones", 25.656016, -99.631035), ("Los Ramones", 25.662886, -99.628599), ("Altavista", 27.730842, -105.197882),
    ("Saucillo", 28.04638, -105.329342), ("La Antigua", 19.320385, -96.310715), ("San Julián", 23.293276, -96.257899),
    ("Zacatecas", 22.710779, -102.448879), ("Fortín", 18.907151, -96.999524), ("Fortín Aux.", 18.906565, -97.001589),
    ("San Mateo A1", 19.487334, -99.309881), ("San Mateo A2", 19.486228, -99.311503), ("San Mateo A3", 19.487093, -99.310115),
    ("San Mateo A4", 19.48819, -99.311068), ("Lomas Verdes", 19.519198, -99.286355), ("Madín A1", 19.544632, -99.277049),
    ("Madín A2", 19.545601, -99.277405), ("Madín A3", 19.548062, -99.276966), ("Madín A4", 19.548788, -99.277298),
    ("Atizapán", 19.582535, -99.271137), ("Lago de Guadalupe A.", 19.608832, -99.237113), ("Lago de Guadalupe A2", 19.6096, -99.236474),
    ("Seybaplaya", 19.636259, -90.671564), ("Compostela", 21.229472, -104.887417), ("Cuitláhuac", 18.839454, -96.746941),
    ("Cuitláhuac A1", 18.839314, -96.746978), ("Cuitláhuac A1-2", 18.839604, -96.746905), ("Cuitláhuac A2-1", 18.837511, -96.737458),
    ("Cuitláhuac A2-2", 18.83865, -96.739512), ("Paso del Toro", 19.081747, -96.198438), ("Huitzo", 17.275026, -96.915277),
    ("Huitzo A1", 17.278761, -96.914652), ("Miahuatlán", 18.264673, -97.315627), ("Coxtlahuaca A1", 17.726023, -97.353773),
    ("Coxtlahuaca A2", 17.725859, -97.352916), ("Tehuacán", 18.487127, -97.456212), ("Aeropuerto A1", 18.802293, -99.221241),
    ("Aeropuerto A2", 18.802741, -99.219852), ("Alpuyeca", 18.69853, -99.278053), ("Alpuyeca A1", 18.737779, -99.260215),
    ("Alpuyeca A2", 18.722419, -99.259948), ("D.I.E.Z.", 18.8375, -99.21537), ("La Venta", 16.928256, -99.801892),
    ("Palo Blanco", 17.423967, -99.466861), ("Paso Morelos", 18.231465, -99.215466), ("Xochitepec", 17.774978, -99.225314),
    ("Garavitos", 24.004477, -104.736419), ("Llano Grande", 23.868815, -105.203958), ("Mesillas", 23.259302, -106.049587),
    ("Durango", 24.131735, -104.534058), ("Yerbanís", 24.730769, -103.861923), ("Ecatepec", 19.611707, -99.025732),
    ("La Rumorosa", 32.562633, -116.047931), ("La Rumorosa 2", 32.555877, -116.036431), ("Villa Ahumada", 30.437079, -106.52185),
    ("Ensenada", 31.903121, -116.732727), ("Playas de Tijuana", 32.514036, -117.109538), ("Rosarito", 32.32425, -117.409016),
    ("Sánchez Magallanes", 18.030565, -93.812954), ("Sánchez Magallanes", 18.029932, -93.813072), ("Sánchez Magallanes", 18.031623, -93.813693),
    ("Asunción", 20.147427, -98.285747), ("Asunción A1", 20.146458, -98.286939), ("Asunción A2", 20.150099, -98.286642),
    ("Esperanza", 27.603722, -109.93909), ("Fundición", 27.320373, -109.719802), ("Guaymas", 28.036494, -110.924164),
    ("Hermosillo", 29.220733, -110.930184), ("La Jaula", 26.849818, -109.373311), ("Magdalena", 30.629274, -110.948775),
    ("Bermejillo", 25.923655, -103.622077), ("Ceballos", 26.586694, -104.057726), ("Acatlán", 20.415926, -103.55704),
    ("San Marcos", 19.433636, -103.49487), ("Arenal", 20.778748, -103.662386), ("Plan de Barrancas", 21.005379, -104.144084),
    ("Santa María del Oro", 21.328268, -104.644406), ("Santa María A1", 21.327973, -104.663151), ("Santa María A2", 21.327052, -104.664677),
    ("Tequepexpan A1", 21.213906, -104.592673), ("Tequepexpan A2", 21.213664, -104.594174), ("Tequila", 20.854129, -103.861211),
    ("La Joya", 20.604788, -103.138943), ("Cazones1", 20.469874, -97.254669), ("Totomoxtle 1", 20.461964, -97.245995),
    ("Totomoxtle 2", 20.460995, -97.247746), ("Jiménez", 27.244991, -104.933224), ("Oacalco", 18.931121, -99.02562),
    ("Tepoztlán", 18.98681, -99.112444), ("Acayucan", 17.910035, -94.937359), ("Cosamaloapan", 18.334975, -95.822252),
    ("Las Choapas", 17.944819, -94.172372), ("Las Choapas A1", 17.942707, -94.17224), ("Malpasito", 17.349101, -93.586411),
    ("Malpasito A1", 17.348467, -93.586933), ("Malpasito A2", 17.349152, -93.585518), ("Ocuilapa", 16.863172, -93.40687),
    ("Cuerámaro A1", 21.06969, -101.679198), ("Cuerámaro A2", 21.069085, -101.679401), ("Encarnación", 21.489618, -102.242304),
    ("León", 21.102736, -101.784601), ("San Francisco A1", 21.082341, -101.745577), ("San Francisco A2", 21.081411, -101.745975),
    ("San Pedro", 24.748965, -107.568618), ("Morín Chávez", 23.177959, -102.828733), ("Arandas", 20.737502, -101.379985),
    ("Arandas A1", 20.735284, -101.383209), ("Arandas A2", 20.73461, -101.381244), ("San Cristóbal", 20.601075, -101.438521),
    ("La Calera", 20.397139, -101.998746), ("La Calera Aux.", 20.395404, -101.998207), ("Matehuala", 23.664163, -100.607299),
    ("Matehuala A1", 23.664161, -100.606222), ("Matehuala A2", 23.663767, -100.608339), ("Mexicali A1", 32.533552, -115.40878),
    ("Nogales", 31.258312, -110.974723), ("Tecpan", 17.197011, -100.626768), ("Calera", 22.941811, -102.689998),
    ("Chichequillas", 20.705555, -100.343716), ("Atlacomulco II", 19.911815, -99.85251), ("Acambay", 19.223377, -99.844213),
    ("Jilotepec", 19.976547, -99.53149), ("Querétaro 1", 19.998688, -99.487671), ("Querétaro 2", 19.996155, -99.499495),
    ("Querétaro 3", 19.997821, -99.492), ("Querétaro 4", 20.000504, -99.489956), ("Tula II-1", 20.071871, -99.367698),
    ("Tula II-2", 20.070355, -99.368243), ("Tula II-3", 20.072661, -99.369804), ("Tula II-4", 20.071311, -99.368713),
    ("Tula I-1", 20.099725, -99.280562), ("Tula I-2", 20.098169, -99.283149), ("Tula I-3", 20.09821, -99.286059),
    ("Tula I-4", 20.100076, -99.28351), ("Atitalaquia 1", 20.067268, -99.218551), ("Atitalaquia 2", 20.064868, -99.219068),
    ("Ajoloapan 1", 19.956086, -99.053339), ("Ajoloapan 2", 19.955443, -99.052776), ("Ajoloapan 3", 19.955648, -99.055422),
    ("Ajoloapan 4", 19.955638, -99.05548), ("Pachuca", 19.927508, -98.891452), ("Tulancingo 1", 19.834861, -98.700138),
    ("Tulancingo 2", 19.83368, -98.698801), ("Tulancingo 3", 19.832456, -98.700121), ("Tulancingo 4", 19.83364, -98.701536),
    ("Cd. Sahagún 1", 19.756661, -98.628326), ("Cd. Sahagún 2", 19.75596, -98.628121), ("Cd. Sahagún 3", 19.755427, -98.62949),
    ("Cd. Sahagún 4", 19.756069, -98.630532), ("Calpulalpan 1", 19.62148, -98.547093), ("Calpulalpan 2", 19.62015, -98.547003),
    ("Calpulalpan 3", 19.619189, -98.54942), ("Calpulalpan 4", 19.619447, -98.54967), ("Sanctorum 1", 19.515572, -98.469019),
    ("Sanctorum 2", 19.512699, -98.469606), ("Sanctorum 3", 19.512702, -98.468831), ("Sanctorum 4", 19.513876, -98.466906),
    ("Sanctorum 5", 19.518652, -98.471763), ("Texmelucan", 19.301795, -98.409616), ("La Carbonera", 25.510976, -100.868373),
    ("San Nicolás de los Jas", 22.129759, -100.825106), ("Loma Real", 22.276443, -97.893343), ("Tampico", 22.275332, -97.893427),
    ("Ecuandureo", 20.17505, -102.191319), ("Huaniqueo A1", 19.884267, -101.510489), ("Huaniqueo A2", 19.882534, -101.511604),
    ("Jeráhuaro A1", 19.894416, -100.646701), ("Jeráhuaro A2", 19.893593, -100.651203), ("Ocotlán", 20.40586, -102.73889),
    ("Ocotlán A1", 20.406969, -102.738906), ("Ocotlán A2", 20.404903, -102.739378), ("Panindícuaro", 19.972189, -101.756945),
    ("Vista Hermosa A1", 20.269788, -102.43991), ("Vista Hermosa A2", 20.269344, -102.441826), ("Zinapécuaro", 19.901776, -100.788521),
    ("Zinapécuaro A1", 19.902373, -100.787561), ("Zinapécuaro A2", 19.900892, -100.789019), ("Costa Rica", 24.570288, -107.430223),
    ("Mármol", 23.471208, -106.569542), ("Quilá A1", 24.397637, -107.269976), ("Quilá A2", 24.396624, -107.271899),
    ("Pisté", 20.728862, -88.583181), ("Xcan", 20.87692, -87.63614), ("Tlalpan", 19.241915, -99.418321),
    ("Tres Marías A1", 19.050851, -99.241365), ("Tres Marías A2", 19.056209, -99.241097), ("Contadero 1", 19.333688, -99.313794),
    ("Contadero 2", 19.331793, -99.31516), ("La Venta", 19.332852, -99.314303), ("Santa Fe", 19.363385, -99.26732),
    ("Ojo de Agua", 19.618814, -99.029522), ("San Cristóbal", 19.602763, -99.038148), ("Chalco", 19.292034, -98.88175),
    ("San Marcos", 19.296387, -98.870735), ("San Martín", 19.241121, -98.385855), ("Jorobas A1", 19.826191, -99.250048),
    ("Jorobas A2", 19.825708, -99.250155), ("Palmillas", 20.296108, -99.929058), ("Polotitlán A1", 20.22643, -99.810686),
    ("Polotitlán A2", 20.225308, -99.810547), ("Tepotzotlán", 19.715364, -99.207569), ("Aguascalientes A1", 26.340266, -100.070469),
    ("Aguascalientes A2", 26.341505, -100.071739), ("Sabinas", 26.512104, -100.007159), ("Sabinas A1", 26.508381, -100.008192),
    ("Vallecillos", 26.642361, -99.942202), ("Playa 1 A1", 25.456853, -101.063694), ("Playa 1 A2", 25.457025, -101.063828),
    ("Playa 1 P", 25.44846, -101.064506), ("Playa 2 A1", 25.615722, -100.908414), ("Playa 2 A2", 25.616308, -100.908432),
    ("Playa 2 P", 25.612236, -100.913526), ("Playa 3 A1", 25.696264, -100.57736), ("La Cinta", 20.073484, -101.13663),
    ("Cuitzeo A1", 19.968867, -101.159727), ("Cuitzeo A2", 19.968282, -101.162062), ("Uriangato", 20.182921, -101.151187),
    ("Valle de Santiago", 20.372552, -101.147354), ("Valtierrilla", 20.542645, -101.377717), ("Valtierrilla A1", 20.553053, -101.136236),
    ("Valtierrilla A2", 20.553134, -101.136428), ("Feliciano", 18.006497, -101.961761), ("Feliciano A1", 18.004663, -101.9639),
    ("Feliciano A2", 18.004082, -101.961901), ("Las Cañas", 18.554181, -101.970317), ("Las Cañas A1", 18.553567, -101.972961),
    ("Zirahuén", 19.505606, -101.659297), ("Zirahuén A", 19.482235, -101.730717), ("Zurumucapio", 19.441166, -101.882235),
    ("Peñón", 19.468849, -99.004418), ("Texcoco", 19.502896, -98.912747), ("Las Vigas", 19.627722, -97.153089),
    ("Miradores", 19.472105, -96.772824), ("Amozoc", 19.049787, -98.032313), ("Alvarado", 18.769878, -95.744556),
    ("Cadereyta", 20.561059, -100.05737), ("Camargo", 26.362441, -98.806402), ("Caracol", 18.133114, -96.136671),
    ("Cd. Acuña", 29.325454, -100.928793), ("Coatzacoalcos", 18.115156, -94.410884), ("San Luis Río Colorado", 32.491685, -114.808756),
    ("Culiacán", 24.948879, -107.545718), ("Iguala", 18.33621, -99.508327), ("Dovalí", 18.013379, -94.396777),
    ("Dovalí Bis", 18.014055, -94.443264), ("El Zacatal", 18.61286, -91.860817), ("Juárez Lincoln", 27.498254, -99.502409),
    ("La Piedad", 20.352787, -102.025175), ("Isla Aguada", 18.785548, -91.494874), ("Laredo I", 27.49856, -99.507378),
    ("Las Flores", 26.060544, -97.50416), ("Libre Comercio", 26.021585, -97.738817), ("Los Tomates", 25.874233, -97.474692),
    ("Matamoros", 25.891382, -97.503914), ("Miguel Alemán", 26.402916, -99.020661), ("Nautla", 20.210215, -96.778734),
    ("Nuevo Laredo III", 27.595071, -99.514337), ("Ojinaga", 29.561043, -104.397206), ("Papaloapan", 18.159598, -96.096688),
    ("Paso del Norte", 31.745887, -106.486418), ("Pánuco", 22.148794, -98.144897), ("Piedras Negras", 28.705234, -100.512987),
    ("Piedras Negras II", 28.697047, -100.512395), ("Reynosa", 26.093215, -98.270947), ("Reynosa - Pharr", 26.041812, -98.20886),
    ("Rodolfo Robles", 14.677057, -92.149701), ("San Juan", 26.311873, -98.841957), ("San Miguel", 25.976312, -109.033558),
    ("Sinaloa", 25.512842, -108.347578), ("Solidaridad", 27.697345, -99.747804), ("Suchiate II", 14.702181, -92.151404),
    ("Tampico", 22.218325, -97.824741), ("Tecolutla", 20.437802, -97.086444), ("Tlacotalpan", 18.704609, -95.641325),
    ("Usumacinta", 17.859877, -91.783643), ("Zaragoza", 31.670895, -106.34067), ("Los Chorros", 25.186754, -100.731938),
    ("Huachichil", 25.24548, -100.801484), ("Cerro Gordo", 20.591875, -101.137274), ("Querétaro", 20.525718, -100.472837),
    ("Salamanca", 20.598452, -100.180914), ("Salamanca A1", 20.599141, -101.180695), ("Salamanca A2", 20.597586, -101.181031),
    ("Salamanca A3", 20.590023, -101.136035), ("Villagrán A1", 20.582207, -100.992157), ("Villagrán A2", 20.579417, -100.99235),
    ("Taxo", 18.588623, -99.559597), ("Nuevo Progreso A2", 26.037152, -97.954566), ("Nuevo Progreso P1", 26.036267, -97.954442),
    ("Rayón", 21.864264, -96.618995), ("El Hongo", 32.521819, -116.319985), ("El Hongo A1", 32.521141, -116.163914),
    ("El Hongo A2", 32.522047, -116.31983), ("Ixtepec A1", 16.561071, -95.134966), ("Ixtepec A2", 16.561481, -95.134292),
    ("Ixtepec A3", 16.561823, -95.136055), ("Ixtepec", 16.561154, -95.135615), ("Tehuantepec", 16.162139, -94.804051),
    ("San José del Cabo", 23.04992, -109.719559), ("Acapulco", 19.301587, -98.404051), ("Santa Ana", 30.58679, -111.284143),
    ("Esperanza", 32.525485, -116.690261), ("Tecate", 32.54579, -116.690261), ("Nuevo Necaxa", 20.183843, -97.992761),
    ("Acaponeta A1", 22.453835, -105.424726), ("Acaponeta A2", 22.454088, -105.418817), ("Rosario A1", 22.984707, -105.878039),
    ("Rosario A2", 22.985107, -105.875277), ("Ruíz A1", 21.953097, -105.12077), ("Ruíz A2", 21.951811, -110.116064),
    ("Trapichillo", 21.571769, -104.987465), ("Yago A1", 21.844631, -105.084918), ("Yago A2", 21.845203, -105.056015),
    ("La Cuchilla", 25.627001, -102.878215), ("Plan de Ayala", 25.444123, -101.303947), ("Chiapas de Corzo", 16.730618, -93.0095),
    ("Santa Casilda", 19.152932, -101.97813), ("Santa Casilda A1", 19.156446, -101.976093), ("Taretán", 19.355443, -101.917902),
    ("Taretán A1", 19.351874, -101.917902), ("Cuencamé III", 24.981671, -103.73525), ("Cuencamé III A2", 24.980948, -103.736669),
    ("Cuencamé III A1", 24.980356, -103.734326), ("León Guzmán A2", 25.519483, -103.63969), ("León Guzmán", 25.520619, -103.639462),
    ("León Guzmán A1", 25.519463, -103.639408), ("Zacapalco", 18.537976, -99.447394), ("Jalostotitlán A1", 21.117576, -102.455541),
    ("Jalostotitlán A1", 21.119064, -102.455793), ("Jalostotitlán A2", 21.120273, -102.455859), ("San Juan A1", 21.224694, -102.313144),
    ("San Juan A2", 21.220673, -102.313651), ("Tepatitlán", 20.824618, -102.794958), ("Tepatitlán Aux.", 20.82091, -102.794064)
]

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
        
        st.subheader("⚙️ Módulos de Procesamiento y Exportación KML / HTML")
        
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
                    st.error("Faltan columnas de coordenadas.")
                
        with b2:
            if st.button("📍 KML Paradas y Casetas"):
                if lat_col and lon_col and vel_col:
                    with st.spinner("Calculando ruta, casetas y paradas..."):
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

                        casetas_agregadas = set()
                        for _, row in df.iterrows():
                            lat_gps, lon_gps = procesar_lat_lon(row[lat_col], row[lon_col])
                            ev = str(row[evento_col]).upper() if evento_col in df.columns else ''
                            ubi = str(row[ubicacion_col]).upper() if ubicacion_col in df.columns else ''
                            
                            if lat_gps != 0 and lon_gps != 0:
                                for c_nombre, c_lat, c_lon in CASETAS_DB:
                                    if c_nombre not in casetas_agregadas:
                                        if (abs(lat_gps - c_lat) < 0.03 and abs(lon_gps - c_lon) < 0.03) or (c_nombre.upper() in ubi or c_nombre.upper() in ev):
                                            casetas_agregadas.add(c_nombre)
                                            desc_caseta = f"<b>[CASETA DE PEAJE]</b><br><b>Nombre:</b> {c_nombre}"
                                            kml_elements.append(f"""
    <Placemark>
      <name>{c_nombre}</name>
      <styleUrl>#pinCaseta</styleUrl>
      <description><![CDATA[{desc_caseta}]]></description>
      <Point><coordinates>{c_lon},{c_lat},0</coordinates></Point>
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
    <name>Ruta de Navegación con Casetas y Paradas - {unit_eval}</name>
    <Style id="estiloLineaNavegacion"><LineStyle><color>ffFF8800</color><width>5</width></LineStyle></Style>
    <Style id="pinInicio"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle></Style>
    <Style id="pinFin"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-square.png</href></Icon></IconStyle></Style>
    <Style id="pinDetenido"><IconStyle><scale>1.0</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon></IconStyle></Style>
    <Style id="pinCaseta"><IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-blank.png</href></Icon></IconStyle></Style>
    {''.join(kml_elements)}
  </Document>
</kml>"""
                    st.download_button("📥 Descargar KML Paradas y Casetas", data=kml_p, file_name=f"paradas_casetas_{unit_eval}.kml", mime="application/vnd.google-earth.kml+xml")
                else:
                    st.error("Faltan columnas necesarias para procesar las paradas.")
 
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
                        
                        # 2. INTERMEDIOS (Paradas estrictas de 0 km/h y reinicio de marcha)
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
                                        next_vel = float(next_row[vel_col]) if next_row[vel_col] is not None else 0
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
    <button class="btn-print" onclick="window.print()">🖨️ Guardar como PDF / Imprimir</button>
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

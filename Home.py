import streamlit as st
import requests
from datetime import date
from streamlit_autorefresh import st_autorefresh

# -------- Datos y funciones comunes --------
API_KEY = "2284f2ce83e1755bd15e0554cf0288fe"
HEADERS = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': API_KEY
}

def limpiar_nombre(nombre):
    return nombre.strip().lower()

def obtener_partidos_por_fecha(fecha):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": fecha.strftime("%Y-%m-%d")}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        partidos = data.get("response", [])
        return partidos
    except Exception as e:
        st.error(f"Error al obtener partidos: {e}")
        return []

def limpiar_nombre_equipo(nombre):
    return nombre.strip().lower()

def obtener_resultado(fecha, equipo_local, equipo_visitante):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": fecha}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error al obtener partidos: {e}")
        return None

    for partido in data.get("response", []):
        home = limpiar_nombre_equipo(partido["teams"]["home"]["name"])
        away = limpiar_nombre_equipo(partido["teams"]["away"]["name"])
        if limpiar_nombre_equipo(equipo_local) == home and limpiar_nombre_equipo(equipo_visitante) == away:
            score = partido.get("score", {}).get("fulltime")
            if score and score["home"] is not None and score["away"] is not None:
                return score["home"], score["away"]
    return None


# -------- Variables coordinador --------
USUARIO_COORDINADOR = "admin"
CONTRASENA_COORDINADOR = "1234"

# -------- Interfaz --------

st.title("Bienvenido a Betplay FMS ⚽")
st.write("Esta aplicación permite a los usuarios registrar predicciones de partidos de fútbol y al coordinador fijar el partido actual.")

opcion = st.sidebar.selectbox("Selecciona una opción:", ["🧑‍💼 Coordinador", "👥 Usuarios"])

if opcion == "🧑‍💼 Coordinador":
    # --- Panel Coordinador ---
    st.header("Panel del Coordinador - Fijar partido")

    if "logueado" not in st.session_state:
        st.session_state.logueado = False

    if not st.session_state.logueado:
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if usuario == USUARIO_COORDINADOR and contrasena == CONTRASENA_COORDINADOR:
                st.session_state.logueado = True
                st.success("¡Acceso concedido!")
            else:
                st.error("Usuario o contraseña incorrectos.")
    else:
        st.success("✅ Usuario coordinador logueado")

        fecha_partido = st.date_input("📅 Selecciona fecha del partido", value=date.today())

        partidos = obtener_partidos_por_fecha(fecha_partido)

        if partidos:
            lista_partidos = [f"{p['teams']['home']['name']} vs {p['teams']['away']['name']}" for p in partidos]
            partido_seleccionado = st.selectbox("⚽ Selecciona partido para fijar", lista_partidos)

            if st.button("Fijar partido"):
                partido_index = lista_partidos.index(partido_seleccionado)
                fixture = partidos[partido_index]["fixture"]
                fixture_id = fixture["id"]

                st.session_state.partido_fijado = {
                    "fecha": fecha_partido.strftime("%Y-%m-%d"),
                    "partido": partido_seleccionado,
                    "fixture_id": fixture_id
                }

                with open("partido_fijado.txt", "w") as f:
                    f.write(f"{fecha_partido.strftime('%Y-%m-%d')}|{partido_seleccionado}|{fixture_id}")

                st.success(f"🎯 Partido fijado: {partido_seleccionado} el {fecha_partido.strftime('%Y-%m-%d')}")
        else:
            st.warning("⚠️ No se encontraron partidos para esta fecha.")


elif opcion == "👥 Usuarios":
    # --- Panel Usuarios ---
    st.header("⚽ Usuarios - Registrar predicciones")

    # Refrescar cada 10 minutos
    st_autorefresh(interval=600000, key="autorefresh")

    if "partido_fijado" not in st.session_state:
        st.warning("Aún no hay partido fijado por el coordinador.")
        st.stop()

    partido_fijado = st.session_state.partido_fijado
    fecha = partido_fijado["fecha"]
    partido = partido_fijado["partido"]
    st.write(f"Partido fijado: **{partido}** el {fecha}")

    try:
        equipo_local, equipo_visitante = [x.strip() for x in partido.split("vs")]
    except Exception:
        st.error("Error al interpretar el partido fijado.")
        st.stop()

    if "predicciones" not in st.session_state:
        st.session_state.predicciones = []

    with st.form("form_prediccion"):
        nombre = st.text_input("Nombre del jugador").strip()
        goles_local = st.number_input("Goles equipo local (predicción)", min_value=0, step=1)
        goles_visitante = st.number_input("Goles equipo visitante (predicción)", min_value=0, step=1)
        submit = st.form_submit_button("Guardar predicción")

        if submit:
            if not nombre:
                st.error("Por favor, ingresa tu nombre.")
            else:
                marcador = (goles_local, goles_visitante)
                marcadores_existentes = [p["marcador"] for p in st.session_state.predicciones]
                if marcador in marcadores_existentes:
                    st.error("⚠️ Ya existe una predicción con ese marcador. Elige otro resultado.")
                else:
                    st.session_state.predicciones.append({
                        "nombre": nombre,
                        "marcador": marcador
                    })
                    st.success(f"Predicción registrada para {nombre}.")

    if st.session_state.predicciones:
        st.write("### Predicciones registradas:")
        for p in st.session_state.predicciones:
            st.write(f"- {p['nombre']}: {p['marcador'][0]} - {p['marcador'][1]}")
    else:
        st.info("No hay predicciones registradas aún.")

    resultado_real = obtener_resultado(fecha, equipo_local, equipo_visitante)
    if resultado_real:
        goles_local_real, goles_visitante_real = resultado_real
        st.success(f"Resultado real: {equipo_local} {goles_local_real} - {goles_visitante_real} {equipo_visitante}")

        if goles_local_real > goles_visitante_real:
            st.info(f"Está ganando: {equipo_local}")
        elif goles_visitante_real > goles_local_real:
            st.info(f"Está ganando: {equipo_visitante}")
        else:
            st.info("El partido está empatado.")

        ganadores = [p["nombre"] for p in st.session_state.predicciones if p["marcador"] == resultado_real]
        if ganadores:
            st.balloons()
            st.subheader("🏆 ¡Ganador(es)!")
            for g in ganadores:
                st.write(f"🎉 {g}")
    else:
        st.warning("Resultado real no disponible aún o partido no ha comenzado.")

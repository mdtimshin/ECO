import math
import operator
import time
import uuid
from datetime import datetime, timedelta
import asyncio
from itertools import groupby

import aiohttp
import folium
import numpy as np
import pandas as pd
import plost
import pytz
import requests
from PIL import Image
from dateutil.relativedelta import relativedelta
from folium.plugins import HeatMapWithTime, HeatMap
from threading import local
import streamlit as st
from folium import DivIcon, LatLngPopup
from st_btn_select import st_btn_select
from streamlit.components.v1 import html
from streamlit.runtime.legacy_caching import clear_cache
from streamlit_folium import folium_static
from streamlit_javascript import st_javascript
from streamlit_option_menu import option_menu
import streamlit_scrollable_textbox as stx

import utils

ORS_API_KEY = '5b3ce3597851110001cf6248956c5852f3124220971192bdb7b2909f'

thread_local = local()

wind_directions_markers = []

current_latitude = 0
current_longitude = 0

st.set_page_config(layout="wide")


async def create_wind_marker(wind_direction, wind_speed, latitude, longtitude):
    scale_coef = 40
    arrow_scale = (wind_speed / scale_coef) * 2 + 1
    marker = folium.Marker(location=(latitude, longtitude), icon=DivIcon(icon_size=(150, 36),
                                                                         icon_anchor=(7, 20),
                                                                         html=f'<svg fill="#3F6078"'
                                                                              f'width="20"'
                                                                              f'height="20"'
                                                                              f'xmlns="http://www.w3.org/2000/svg"'
                                                                              f'fill-rule="evenodd"'
                                                                              f'clip-rule="evenodd"'
                                                                              f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
                                                                              f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
                                                                              f'</svg>',
                                                                         ))
    wind_directions_markers.append(marker)


async def get_wind_data(lat, long, num_points):
    async with aiohttp.ClientSession() as client:
        for latitude in np.linspace(lat - 0.1, lat + 0.1, 4):
            for longitude in np.linspace(long - 0.2, long + 0.2, 4):
                parameters = {
                    'latitude': str(latitude),
                    'longitude': str(longitude),
                    'current_weather': 'True',
                    'windspeed_unit': 'ms',
                    'timezone': 'auto'
                }
                async with client.get('https://api.open-meteo.com/v1/forecast', params=parameters) as response:
                    if response.status > 399:
                        response.raise_for_status()
                    
                    data = await response.json()
                    wind = (data["current_weather"]["winddirection"], data["current_weather"]["windspeed"])
                    await create_wind_marker(wind[0], wind[1], latitude, longitude)


def start_gathering_wind_data(lat, long, num_points):
    asyncio.run(get_wind_data(lat, long, num_points))


@st.cache
def geocode(query):
    parameters = {
        'api_key': ORS_API_KEY,
        'text': query
    }
    
    response = requests.get(
        'https://api.openrouteservice.org/geocode/search',
        params=parameters)
    if response.status_code == 200:
        data = response.json()
        if data['features']:
            x, y = data['features'][0]['geometry']['coordinates']
            return (y, x)


@st.cache
def current_weather(lat, long):
    parameters = {
        'latitude': lat,
        'longitude': long,
        'current_weather': True,
        'windspeed_unit': 'ms',
        'timezone': 'auto'
    }
    
    response = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params=parameters
    )
    if response.status_code == 200:
        data = response.json()
        return data


@st.cache
def get_gas_analyzers_data():
    parameters = {}
    response = requests.get("http://localhost:8000/gas_analyzers")
    if response.status_code == 200:
        data = response.json()
        return data


@st.cache
def get_companies_data():
    parameters = {}
    response = requests.get("http://localhost:8000/companies")
    if response.status_code == 200:
        data = response.json()
        return data


@st.cache
def get_pipes_data():
    parameters = {}
    response = requests.get("http://localhost:8000/pipes")
    if response.status_code == 200:
        data = response.json()
        return data


@st.cache
def get_analyzer_data(analyzer_id, date_from, date_to):
    date_from = date_from.strftime('%Y-%m-%d %H:%M:%S')
    date_to = date_to.strftime('%Y-%m-%d %H:%M:%S')
    parameters = {
        "measurement": f"Gaz_Analyzer_{analyzer_id}",
        "date_from": f"{date_from}",
        "date_to": f"{date_to}"
    }
    
    response = requests.get("http://localhost:8000/influx/gas_analyzer", params=parameters)
    if response.status_code == 200:
        data = response.json()
        return data


def get_substances_data():
    response = requests.get("http://localhost:8000/guide")
    if response.status_code == 200:
        data = response.json()
        return data


def add_substance(substance_name, pdk_mr, pdk_ss):
    data = {
        "substance_name": substance_name,
        "pdk_mr": pdk_mr,
        "pdk_ss": pdk_ss
    }
    response = requests.post("http://localhost:8000/guide", json=data)
    if response.status_code == 200:
        data = response.json()
        #         # print(data)
        return data


def delete_substance(id):
    parameters = {"id": id}
    response = requests.delete(f"http://localhost:8000/guide/{id}", params=parameters)
    if response.status_code == 200:
        data = response.json()
        return data


def add_analyzer(name, city_id, latitude, longitude, description):
    data = {
        "measurement": name,
        "city_id": city_id,
        "latitude": latitude,
        "longitude": longitude,
        "description": description
    }
    response = requests.post("http://localhost:8000/gas_analyzers", json=data)
    if response.status_code == 200:
        data = response.json()
        return data


def add_pipe(name, city_id, latitude, longitude):
    data = {
        "measurement": name,
        "company_id": city_id,
        "latitude": latitude,
        "longitude": longitude
    }
    response = requests.post("http://localhost:8000/pipes", json=data)
    if response.status_code == 200:
        data = response.json()
        #         # print(data)
        return data


if 'analyzers' not in st.session_state:
    st.session_state.analyzers = list()

if 'pipes' not in st.session_state:
    st.session_state.pipes = list()

if 'analyzers_data' not in st.session_state:
    st.session_state.analyzers_data = list()

if 'analyzers_dataframe' not in st.session_state:
    st.session_state.analyzers_dataframe = pd.DataFrame(columns=['Date'])

if 'logs' not in st.session_state:
    st.session_state.logs = []

if 'current_logs' not in st.session_state:
    st.session_state.current_logs = []

if 'time_delay' not in st.session_state:
    st.session_state.time_delay = 0

if 'logging' not in st.session_state:
    st.session_state.logging = False

if 'heatmap_data' not in st.session_state:
    st.session_state.heatmap_data = {}

if 'substances_data' not in st.session_state:
    st.session_state.substances_data = []


def generate_log(date, analyzer_name, value):
    warning_circle = ''
    if value < 0.9:
        warning_circle = "\U0001F7E2"
    elif 0.9 <= value < 1:
        warning_circle = "\U0001F7E1"
    elif value >= 1:
        warning_circle = "\U0001F534"
    st.session_state.logs.append({
        "date": date,
        "analyzer_name": analyzer_name,
        "value": value,
        "text": f'{date} Датчик {analyzer_name} зафиксировал значение ПДК = {value} {warning_circle} {chr(10)} {chr(10)}'
    }
    )


def create_action_log(string):
    st.session_state.logs.append(f'{"=" * 6} {string} {"=" * 6}')


def alert():
    stop_js = """
    var iframe = document.getElementsByTagName("iframe")[2];
    var pauseButton = iframe.contentWindow.document.getElementsByClassName("wrapper")[0];
    var button = pauseButton.firstChild;
    button.click();
    alert('Hello');
    """
    stop_html = f'<script language="javascript">{stop_js}</script>'
    html(stop_html)
    

if __name__ == "__main__":
    column_logs, column_settings = st.columns((4, 1))
    with st.sidebar:
        image = Image.open('hselogo_fullsize.png')
        st.image(image=image, width=50)
        choose = option_menu("ECO monitoring", ["About", "Simulation", "Plots", "Substances"],
                             icons=['house'], menu_icon="app-indicator", default_index=1,
                             styles={
                                 "container": {"padding": "5!important", "background-color": "#fafafa"},
                                 "icon": {"color": "orange", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#eee"},
                                 "nav-link-selected": {"background-color": "#02ab21"},
                             })
    
    if choose == "About":
        st.title('Система идентификации источников выбросов')
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown(""" <style> .font {
                    font-size:35px ; font-family: 'Cooper Black';}
                    </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">О приложении</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="font">Система представляет собой экспериментальный стенд-прототип, позволяющий выполнять следующие функции:</p>',
                unsafe_allow_html=True)
            st.markdown("""
            <ul>
                <li>
                    1.	Добавление меток промышленных предприятий и источников выбросов внутри предприятия на карту;
                </li>
                <li>
                    2.	Добавление меток газоанализаторов на карту;
                </li>
                <li>
                    3.	Отображение санитарной зоны предприятия на карте по радиусу в метрах;
                </li>
                <li>
                    4.	Работа со справочником ПДК;
                </li>
                <li>
                    5.	Работа с погодными данными (температура, ветер, давление);
                </li>
                <li>
                    6.	Построение графиков измерений для газоанализаторов;
                </li>
                <li>
                    7.	Симуляция
                </li>
                <li>
                    <ul>
                        <li>7.1.	Симуляция поведения газоанализаторов посредством использования загруженных данных;</li>
                        <li>7.2.	Идентификация источника выброса при фиксации превышения на измерительном приборе;</li>
                        <li>7.3.	Построение модели выброса на карте</li>
                    </ul>
                </li>
            </ul>
            """, unsafe_allow_html=True)
            
            st.markdown(
                '<p class="font">Для идентификации и построение выброса используется только математические методы:</p>',
                unsafe_allow_html=True)
            
            st.markdown("""
                        <ul>
                            <li>
                                1.	Для процесса идентификации выстраивается вектор по направлению ветра и находится кратчайшее расстояние от точки до прямой, за счет чего выявляется ближайший источник, который принимается за выбросившего;
                            </li>
                            <li>
                                2.	Выброс осуществляется по направлению ветра с разбросом, покрывая некоторую область на карте.
                            </li>
                        </ul>
                        """, unsafe_allow_html=True)
            
        st.write('**************************************')
        
        footer = st.container()
        with footer:
            with col1:
                st.image(image=image, width=100)
            
            with col2:
                st.markdown("""<div style="display: flex; justify-content: flex-end">
                                    <div>
                                        <div>
                                            Работу выполняли студенты 4 курса ПИ из НИУ ВШЭ:
                                        </div>
                                        <ul>
                                            <li>Тимшин Михаил</li>
                                            <li>Черницин Игорь</li>
                                            <li>Костин Виктор</li>
                                            <li>Шорохова Анжелика</li>
                                            <li>Филатова Валерия</li>
                                        </ul>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
    
    elif choose == "Simulation":
        wind_direction_variable = {
            "Gaz_Analyzer_2": {
                # "pipe_1": 240,
                "wind_direction": 74,
            },
            "Gaz_Analyzer_1": {
                "wind_direction": 330,
                # "pipe_2": 18,
            },
            "Gaz_Analyzer_3": {
                "wind_direction": 97,
            },
            "Gaz_Analyzer_4": {
                "wind_direction": 130,
            },
            "Gaz_Analyzer_7": {
                "wind_direction": 270,
            },
            "Gaz_Analyzer_8": {
                "wind_direction": 310,
            },
            "Gaz_Analyzer_5": {
                "wind_direction": 170,
            },
            "Gaz_Analyzer_6": {
                "wind_direction": 259,
            },
        }
        
        with st.sidebar:
            with st.form(key='add_analyzer_form'):
                st.title("Добавить газоанализатор")
                name = st.text_input(label="Наименование")
                latitude = st.number_input(label='Координаты долготы', step=.0001, format="%.4f")
                longitude = st.number_input(label='Координаты широты', step=.0001, format="%.4f")
                submit = st.form_submit_button(label='Добавить газоанализатор')
                if submit and len(name) != 0 and latitude != 0 and longitude != 0:
                    add_analyzer(name, 1, latitude, longitude, "")
                    info = st.empty()
                    with info:
                        info.success("Добавлено")
                        time.sleep(3)
                        info = st.empty()
            
            with st.form(key='add_pipe_form'):
                st.title("Добавить источник")
                name = st.text_input(label="Наименование")
                latitude = st.number_input(label='Координаты долготы', step=.0001, format="%.4f")
                longitude = st.number_input(label='Координаты широты', step=.0001, format="%.4f")
                submit = st.form_submit_button(label='Добавить источник')
                if submit and len(name) != 0 and latitude != 0 and longitude != 0:
                    add_pipe(name, 1, latitude, longitude)
                    with info:
                        info.success("Добавлено")
                        time.sleep(3)
                        info = st.empty()
        
        PIPES = get_pipes_data()
        ANALYZERS = get_gas_analyzers_data()
        COMPANIES = get_companies_data()
        
        
        with column_settings:
            
            start_date = st.date_input('Начальная дата', datetime(year=2022, month=1, day=23))
            end_date = st.date_input('Конечная дата', datetime(year=2022, month=1, day=24))
            
            if st.button("Ввод") and start_date < end_date:
                analyzers_data = []
                analyzers_names = []
                flags = {}
                
                for analyzer in ANALYZERS:
                    analyzer_id = analyzer["measurement"][-1]
                    data = get_analyzer_data(analyzer_id, date_from=start_date, date_to=end_date)
                    analyzers_data.extend(data)
                    analyzer_name = f"Gaz_Analyzer_{analyzer_id}"
                    analyzers_names.append(analyzer_name)
                    flags[f'{analyzer_name}'] = False
                    st.session_state.analyzers_dataframe[f'{analyzer_name}'] = 0
                    
                analyzers_data.sort(key=operator.itemgetter('_time'))
                grouped_data = []
                
                for key, value in groupby(analyzers_data, key=operator.itemgetter('_time')):
                    grouped_data.append({"Date": key, "data": [k for k in value]})
                
                df = pd.DataFrame()
                
                for measurements in grouped_data:
                    new_row = {}
                    new_row["Date"] = datetime.fromisoformat(measurements["Date"])
                    for i in analyzers_names:
                        new_row[i] = 0
                    
                    for data in measurements["data"]:
                        
                        if pd.to_numeric(data["value"]) >= 1 and flags[f'{data["_measurement"]}'] == True:
                            new_row[f'{data["_measurement"]}'] = 0
                        
                        elif pd.to_numeric(data["value"]) >= 1 and flags[f'{data["_measurement"]}'] == False:
                            new_row[f'{data["_measurement"]}'] = data["value"]
                            flags[f'{data["_measurement"]}'] = True
                        
                        elif pd.to_numeric(data["value"]) < 1:
                            flags[f'{data["_measurement"]}'] = False
                            new_row[f'{data["_measurement"]}'] = data["value"]
                    
                    st.session_state.analyzers_dataframe = st.session_state.analyzers_dataframe.append(new_row,
                                                                                                       ignore_index=True)
                
                info = st.empty()
                with info:
                    info.success("Данные получены")
                    time.sleep(3)
                    info = st.empty()
                    
            
            time_delay = st.slider("Задержка симуляции sec.", min_value=1, max_value=300, value=1)
            st.session_state.time_delay = time_delay
            
            if st.button("Начать симуляцию"):
                st.session_state.logging = True
                
                analyzers_data = st.session_state.analyzers_dataframe.to_dict('records')
                
                for measurement in analyzers_data:
                    date = measurement["Date"].to_pydatetime()
                    date = str(date)[:-6]
                    
                    names = list(measurement.keys())[1:]
                    values = list(measurement.values())[1:]
                    for name, value in zip(names, values):
                        if value > 0.5:
                            generate_log(date=date, analyzer_name=name, value=value)
                        else:
                            continue
                
            selection_container = st.empty()
                
            selection = st_btn_select(("Pause", "Play", "Stop"), key='1')
                
            if selection == "Pause":
                    st.session_state.logging = False
            if selection == "Play":
                st.session_state.logging = True
            if selection == "Stop":
                st.session_state.logging = False
                st.session_state.analyzers = list()
                st.session_state.pipes = list()
                st.session_state.analyzers_data = list()
                st.session_state.analyzers_dataframe = pd.DataFrame(columns=['Date'])
                st.session_state.logs = []
                st.session_state.current_logs = []
                st.session_state.time_delay = 0
                st.session_state.logging = False
                st.session_state.heatmap_data = {}
                info = st.empty()
                with info:
                    info.warning("Симуляция прекращена")
                    time.sleep(3)
                    info = st.empty()
                clear_cache()

                nav_script = """
                        <meta http-equiv="refresh" content="0; url='%s'">
                    """ % ("http://localhost:8501/")
                st.write(nav_script, unsafe_allow_html=True)
        
        with column_logs:
            st.title('Логи')
            logs = []
            time_delay = 0
            try:
                logs = [x for x in st.session_state.logs]
                time_delay = st.session_state.time_delay
            except AttributeError:
                logs = []
                time_delay = 0
            
            placeholder = st.empty()
            current_logs = []
            container = st.empty()
            with container:
                if time_delay != 0:
                    while st.session_state.logging:
                        if len(st.session_state.current_logs) == 0:
                            warning_container = st.empty()
                            for index, log in enumerate(logs):
                                current_logs.append(log)
                                with placeholder:
                                    text = ''.join([x["text"] for x in current_logs[::-1]])
                                    stx.scrollableTextbox(text=text, height=400,
                                                          fontFamily='Helvetica',
                                                          border=True, key=str(uuid.uuid4()))
                                
                                time.sleep(time_delay)
                                
                                st.session_state.current_logs = current_logs
                                
                                if log["value"] >= 1:
                                    warning_container.error(f"Превышение на {log['analyzer_name']}. Симуляция приостановлена")
                                    time.sleep(3)
                                    
                                    info = st.empty()
                                    pipe = 0
                                    wind_direction = 0
                                    with info:
                                        info.info(f"Происходит расчет ")
                                        time.sleep(3)
                                        
                                        st.session_state.logging = False
                                        analyzer_id = log["analyzer_name"][-1]
                                        analyzer_name = f"gas_analyzer_{analyzer_id}"
                                        analyzer = next(
                                            item for item in ANALYZERS if item["measurement"] == analyzer_name)
                                        
                                        wind_data = wind_direction_variable[f"{log['analyzer_name']}"]
                                        pipe_warning, wind_direction = next(iter((wind_data.items())))
                                        wind_direction = 180 + wind_direction
                                        pipe = utils.compute_warning_pipe(analyzer_lat=analyzer["latitude"],
                                                                          analyzer_long=analyzer["longitude"],
                                                                          pipes=PIPES,
                                                                          wind_direction=wind_direction)
        
                                        info = st.empty()
                                        
                                        if pipe != 0:
                                            with info:
                                                info.info(f"Выброс поризошел из источника {pipe['measurement']}")
                                                time.sleep(3)
                                            
                                            data, time_index = utils.createHeatmapData(pipe_lat=pipe['latitude'],
                                                                                       pipe_long=pipe['longitude'],
                                                                                       wind_direction=180 + wind_direction,
                                                                                       wind_speed=0)
                                            
                                            st.session_state.heatmap_data["data"] = data
                                            st.session_state.heatmap_data["time_index"] = time_index
                                            
                                            with info:
                                                info.success(f"Данные получены, визуализация готова. Нажмите на кнопку паузы")
                                                time.sleep(3)
                                    break
                            placeholder.empty()
                        else:
                            warning_container = st.empty()
                            logs = st.session_state.logs
                            current_logs = st.session_state.current_logs
                            next_logs = logs[len(current_logs):]
                            for index, log in enumerate(next_logs):
                                current_logs.append(log)
                                with placeholder:
                                    text = ''.join([x["text"] for x in current_logs[::-1]])
                                    stx.scrollableTextbox(text=text, height=400,
                                                          fontFamily='Helvetica',
                                                          border=True, key=str(uuid.uuid4()))
                                time.sleep(time_delay)
                                st.session_state.current_logs = current_logs
                                
                                if log["value"] >= 1:
                                    warning_container.error(
                                        f"Превышение на {log['analyzer_name']}. Симуляция приостановлена")
                                    time.sleep(3)
                                    info = st.empty()
                                    pipe = 0
                                    wind_direction = 0
                                    with info:
                                        info.info(f"Происходит расчет ")
                                        time.sleep(3)
                                        st.session_state.logging = False
                                        analyzer_id = log["analyzer_name"][-1]
                                        analyzer_name = f"gas_analyzer_{analyzer_id}"
                                        analyzer = next(
                                            item for item in ANALYZERS if item["measurement"] == analyzer_name)
                                        wind_data = wind_direction_variable[f"{log['analyzer_name']}"]
                                        pipe_warning, wind_direction = next(iter((wind_data.items())))
                                        wind_direction = 180 + wind_direction
                                        #                                         # print(pipe_warning, wind_direction)
                                        pipe = utils.compute_warning_pipe(analyzer_lat=analyzer["latitude"],
                                                                          analyzer_long=analyzer["longitude"],
                                                                          pipes=PIPES,
                                                                          wind_direction=wind_direction)
    
                                        info = st.empty()

                                    if pipe != 0:
                                        with info:
                                            info.info(f"Выброс поризошел из источника {pipe['measurement']}")
                                            time.sleep(3)
                                            # info = st.empty()
    
                                        data, time_index = utils.createHeatmapData(pipe_lat=pipe['latitude'],
                                                                                   pipe_long=pipe['longitude'],
                                                                                   wind_direction=180 + wind_direction,
                                                                                   wind_speed=0)
    
                                        st.session_state.heatmap_data["data"] = data
                                        st.session_state.heatmap_data["time_index"] = time_index
    
                                        with info:
                                            info.success(f"Данные получены, визуализация готова. Нажмите на кнопку паузы")
                                            time.sleep(3)
                                            # info = st.empty()

                                    # warning = st.empty()
                                break
                        placeholder.empty()
                    
                
                if not st.session_state.logging:
                    with placeholder:
                        text = ''.join([x["text"] for x in st.session_state.current_logs[::-1]])
                        stx.scrollableTextbox(text=text, height=400,
                                              fontFamily='Helvetica',
                                              border=True, key=str(uuid.uuid4()))
        
        address = st.text_input('Введите адрес.')
        
        if address:
            results = geocode(address)
            current_latitude = results[0]
            current_longitude = results[1]
            
            if results:
                st.write('Географические координаты: {}, {}'.format(results[0], results[1]))
                
                m = folium.Map(location=(COMPANIES[0]['latitude'], COMPANIES[0]['longitude']), zoom_start=12,
                               tiles="cartodbpositron")
                
                company_group = folium.FeatureGroup(name="Companies").add_to(m)
                for company in COMPANIES:
                    company_group.add_child(folium.Marker(location=(company['latitude'], company['longitude']),
                                                          popup=company['name']))
                    company_group.add_child(
                        folium.Circle(location=(company['latitude'], company['longitude']),
                                      radius=company['sanitary_zone_radius'],
                                      fill_color='red'))
                
                pipes_group = folium.FeatureGroup(name="Pipes").add_to(m)
                for pipe in PIPES:
                    marker = folium.Marker(location=(pipe['latitude'], pipe['longitude']),
                                           icon=folium.Icon(color='red', icon='industry', prefix='fa'),
                                           popup=pipe["measurement"])
                    pipes_group.add_child(marker)
                
                analyzers_group = folium.FeatureGroup(name="Analyzers").add_to(m)
                for analyzer in ANALYZERS:
                    marker = folium.Marker(location=(analyzer['latitude'], analyzer['longitude']),
                                           icon=folium.Icon(color='lightgray', icon='eye', prefix='fa'),
                                           popup=analyzer["measurement"])
                    analyzers_group.add_child(marker)
                
                coordinates_popup = LatLngPopup()
                m.add_child(coordinates_popup)
                
                folium.TileLayer('Stamen Terrain').add_to(m)
                folium.TileLayer('Stamen Toner').add_to(m)
                folium.TileLayer('Stamen Water Color').add_to(m)
                folium.TileLayer('openstreetmap').add_to(m)
                folium.TileLayer('cartodbdark_matter').add_to(m)
                
                lat = results[0]
                long = results[1]
                
                start_gathering_wind_data(lat, long, 5)
                
                wind_group = folium.FeatureGroup(name="Winds").add_to(m)
                
                for marker in wind_directions_markers:
                    wind_group.add_child(marker)
                
                try:
                    data = st.session_state.heatmap_data['data']
                    time_index = st.session_state.heatmap_data['time_index']
                    
                    heatmap_with_time = HeatMapWithTime(data=data, index=time_index, name='heatmap with time',
                                                        auto_play=False,
                                                        max_opacity=0.3,
                                                        radius=0.007,
                                                        scale_radius=True
                                                        )
                    heatmap_with_time.add_to(m)
                except KeyError:
                    pass
                
                folium.LayerControl().add_to(m)
                folium_static(m, width=1000, height=650)
            
            else:
                st.error('Результатов не найдено.')
    
    
    
    
    
    elif choose == "Plots":
        # PIPES = get_pipes_data()
        ANALYZERS = get_gas_analyzers_data()
        # COMPANIES = get_companies_data()
        
        names = []
        for name in ANALYZERS:
            names.append(f"{'Gaz_Analyzer_' + name['measurement'][-1]}")
        
        analyzer_name = st.selectbox(label='Выберите газоанализатор',
                                     options=["Gaz_Analyzer_" + name["measurement"][-1] for name in ANALYZERS])
        
        start_date = st.date_input('Начальная дата', datetime(year=2021, month=1, day=3))
        end_date = st.date_input('Конечная дата', datetime(year=2023, month=1, day=4))
        
        plot_col, metric_col = st.columns((4, 1))
        
        if st.button("Submit"):
            for name in names:
                if name == analyzer_name:
                    analyzer_id = name[-1]
                    data = get_analyzer_data(analyzer_id, date_from=start_date, date_to=end_date)
                    df = pd.DataFrame(data)
                    df["date"] = df["_time"].map(lambda x: datetime.fromisoformat(x))
                    df["value"] = pd.to_numeric(df["value"])
                    mean = df["value"].mean()
                    max = df["value"].max()
                    min = df["value"].min()
                    #                     # print(mean, max, min)
                    with plot_col:
                        plost.line_chart(data=df, x='date', y='value', title='Значения ПДК',
                                         pan_zoom='minimap', width=900)
                    with metric_col:
                        st.title('Метрики')
                        st.metric("Mean", round(mean, 3))
                        st.metric("Max", max)
                        st.metric("Min", min)
    
    
    elif choose == "Substances":
        substances = get_substances_data()
        st.session_state.substances_data = substances
        table_col, inputs_col = st.columns((3, 1))
        with table_col:
            try:
                ids = [x['id'] for x in substances]
                names = [x['substance_name'] for x in substances]
                pdk_mr = [x['pdk_mr'] for x in substances]
                pdk_ss = [x['pdk_ss'] for x in substances]
                
                df = pd.DataFrame(list(zip(ids, names, pdk_mr, pdk_ss)),
                                  columns=["ID", "Название вещества", "PDK_MR", "PDK_SS"])
                
                st.table(df)
            except TypeError:
                st.title("Данных нет")
        
        with inputs_col:
            with st.form("add_subs"):
                st.text("Добавить вещество")
                name = st.text_input("Название вещества")
                pdk_ss = st.number_input("PDK_SS")
                pdk_mr = st.number_input("PDK_MR")
                
                submitted = st.form_submit_button("Добавить")
                if submitted and len(name) != 0 and pdk_ss != 0 and pdk_mr != 0:
                    result = add_substance(name, pdk_mr, pdk_ss)
                    st.session_state.substances_data.append(result)
                    st.write("Добавлено")
                    # print(result)
            with st.form("del_subs"):
                st.text("Удалить вещество")
                id = st.number_input("ID вещества", step=1)
                
                submitted = st.form_submit_button("Удалить")
                if submitted:
                    result = delete_substance(id)
                    st.write("Удалено")
                    # print(result)

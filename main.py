import concurrent.futures
from datetime import datetime, timedelta
import math
import asyncio
from multiprocessing import cpu_count
from unittest import result

import aiohttp
from aiohttp.client import ClientSession
import folium
import numpy as np
import requests
from folium.plugins import HeatMapWithTime, HeatMap
from requests.sessions import Session
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Thread, local
import streamlit as st
from folium import plugins, DivIcon, LatLngPopup
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

ORS_API_KEY = '5b3ce3597851110001cf6248956c5852f3124220971192bdb7b2909f'

thread_local = local()

wind_directions_markers = []

current_latitude = 0
current_longitude = 0

st.set_page_config(layout="wide")

company_list = [
    {
        'name': 'Лукойл',
        'latitude': 56,
        'longitude': 57,
        'SPZ_width': 2,
        'emission_sourses': [
            {
                'number': 1,
                'latitude': 56,
                'longitude': 57
            },
            {
                'number': 2,
                'latitude': 56,
                'longitude': 57
            }
        ]
    },
    {
        'name': 'Минеральные удобрения',
        'latitude': 56.5,
        'longitude': 57,
        'SPZ_width': 2,
        'emission_sourses': [
            {
                'number': 1,
                'latitude': 56,
                'longitude': 57
            },
            {
                'number': 2,
                'latitude': 56,
                'longitude': 57
            }
        ]
    },
    {
        'name': 'СИБУР-Химпром',
        'latitude': 56,
        'longitude': 57.5,
        'SPZ_width': 2,
        'emission_sourses': [
            {
                'number': 1,
                'latitude': 56,
                'longitude': 57
            },
            {
                'number': 2,
                'latitude': 56,
                'longitude': 57
            }
        ]
    }
]


# scale_coef = 10


# def get_session() -> Session:
#     if not hasattr(thread_local, 'session'):
#         thread_local.session = requests.Session()
#     return thread_local.session
#
#
# def get_current_weather(lat, long):
#     parameters = {
#         'latitude': lat,
#         'longitude': long,
#         'current_weather': True,
#         'windspeed_unit': 'ms',
#         'timezone': 'auto'
#     }
#
#     response = requests.get(
#         'https://api.open-meteo.com/v1/forecast',
#         params=parameters
#     )
#     if response.status_code == 200:
#         data = response.json()
#         return data
#
#
# async def get_current_wind_data(lat, long, session: ClientSession):
#     parameters = {
#         'latitude': lat,
#         'longitude': long,
#         'current_weather': True,
#         'windspeed_unit': 'ms',
#         'timezone': 'auto'
#     }
#
#     async with session.get('https://api.open-meteo.com/v1/forecast', params=parameters) as response:
#         result = await response.json()
#         wind = (result["current_weather"]["winddirection"], result["current_weather"]["windspeed"])
#         wind_direction = wind[0]
#         wind_speed = wind[1]
#         arrow_scale = (wind_speed / scale_coef) * 2 + 1
#         marker = folium.Marker(location=(lat, long), icon=DivIcon(icon_size=(150, 36),
#                                                                   icon_anchor=(7, 20),
#                                                                   html=f'<svg width="20"'
#                                                                        f'height="20"'
#                                                                        f'xmlns="http://www.w3.org/2000/svg"'
#                                                                        f'fill-rule="evenodd"'
#                                                                        f'clip-rule="evenodd"'
#                                                                        f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
#                                                                        f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
#                                                                        f'</svg>',
#                                                                   ))
#         wind_directions_markers.append(marker)
#     # response = requests.get(
#     #     'https://api.open-meteo.com/v1/forecast',
#     #     params=parameters
#     # )
#
#     # if response.status_code == 200:
#     #     data = response.json()
#     #     wind = (data["current_weather"]["winddirection"], data["current_weather"]["windspeed"])
#     #     return wind
#
#
# async def fetch_async(latitude):
#     my_conn = aiohttp.TCPConnector(limit=10)
#     tasks = []
#     async with aiohttp.ClientSession(connector=my_conn) as session:
#         for i in np.linspace(latitude, latitude + 0.1, 101):
#             for j in np.linspace(current_longitude, current_longitude + 1, 1001):
#                 task = asyncio.ensure_future(get_current_wind_data(lat=i, long=j, session=session))
#                 tasks.append(task)
#         await asyncio.gather(*tasks)
#     # print(f'responses = {responses}')
#     # return responses
#
#
# def do_current_wind_thread(latitude):
#     asyncio.run(fetch_async(latitude))
# #     loop = asyncio.get_event_loop()
# #     future = asyncio.ensure_future()
# #     # my_conn = aiohttp.TCPConnector(limit=10)
# #     # async with aiohttp.ClientSession(connector=my_conn) as session:
# #     #     tasks = []
# #     #     for i in np.linspace(latitude, latitude + 0.1, 101):
# #     #         for j in np.linspace(current_longitude, current_longitude + 1, 1001):
# #     #             task = asyncio.ensure_future(get_current_wind(lat=i, long=j, session=session))
# #     #             task.result()
# #     #             tasks.append(task)
# #     #             wind_direction = wind[0]
# #     #             wind_speed = wind[1]
# #     #             arrow_scale = (wind_speed / scale_coef) * 2 + 1
# #     #             marker = folium.Marker(location=(i, j), icon=DivIcon(icon_size=(150, 36),
# #     #                                                                  icon_anchor=(7, 20),
# #     #                                                                  html=f'<svg width="20"'
# #     #                                                                       f'height="20"'
# #     #                                                                       f'xmlns="http://www.w3.org/2000/svg"'
# #     #                                                                       f'fill-rule="evenodd"'
# #     #                                                                       f'clip-rule="evenodd"'
# #     #                                                                       f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
# #     #                                                                       f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
# #     #                                                                       f'</svg>',
# #     #                                                                  ))
# #     #             wind_directions_markers.append(marker)
# #     #     await asyncio.gather(*tasks, return_exceptions=True)
#
#
# def get_all_wind_direction(lat, long) -> None:
#     wind_directions_markers = []
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         for i in np.linspace(current_latitude, current_latitude + 1, 11):
#             executor.submit(do_current_wind_thread, i)
#             # wind_directions_markers.append(executor.submit(get_current_wind, lat=i, long=current_longitude))
#
# async def get(latitude, longitude, session):
#     parameters = {
#         'latitude': str(latitude),
#         'longitude': str(longitude),
#         'current_weather': 'True',
#         'windspeed_unit': 'ms',
#         'timezone': 'auto'
#     }
#     try:
#         async with session.get(url='https://api.open-meteo.com/v1/forecast', params=parameters) as response:
#             response = await response.read()
#             print(f'{latitude}, {longitude}')
#     except Exception as e:
#         print(e)
#
#
# async def loop(latitude, longitude):
#     async with aiohttp.ClientSession() as session:
#         # ret = await asyncio.gather(*[get(latitude, longitude, session)])
#         # # gather_array = []
#         for lat in np.linspace(latitude, latitude + 1, 1001):
#             for long in np.linspace(longitude, longitude + 1, 1001):
#                 ret = await asyncio.gather(*[get(lat, long, session)])
#     print('Finalized all')


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
    # parameters = {
    #     'latitude': str(lat),
    #     'longitude': str(long),
    #     'current_weather': 'True',
    #     'windspeed_unit': 'ms',
    #     'timezone': 'auto'
    # }
    async with aiohttp.ClientSession() as client:
        # for i in range(num_points):
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


# def multiprocessing_wind_data(latitude, longtitude):
#     NUM_LATITUDE_POINTS = 1000
#     NUM_CORES = cpu_count()-2
#
#     POINTS_PER_CORE = math.floor(NUM_LATITUDE_POINTS / NUM_CORES)
#     POINTS_FOR_FINAL_CORE = POINTS_PER_CORE + NUM_LATITUDE_POINTS % POINTS_PER_CORE
#
#     futures = []
#
#     with ProcessPoolExecutor(NUM_CORES) as executor:
#         for i in range(NUM_CORES):
#             new_future = executor.submit(
#                 start_gathering_wind_data,
#                 lat=latitude,
#                 long=longtitude,
#                 num_points=POINTS_PER_CORE
#             )
#             futures.append(new_future)
#
#         futures.append(
#             executor.submit(
#                 start_gathering_wind_data,
#                 lat=latitude,
#                 long=longtitude,
#                 num_points=POINTS_FOR_FINAL_CORE
#             ))
#
#     concurrent.futures.wait(futures)


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


if 'analyzers' not in st.session_state:
    st.session_state.analyzers = list()
    
if 'pipes' not in st.session_state:
    st.session_state.pipes = list()


def add_analyzer(latitude, longitude):
    marker = folium.Marker(location=(latitude, longitude), icon=folium.Icon(color='lightgray', icon='eye', prefix='fa'))
    st.session_state.analyzers.append(marker)


def add_pipe(latitude, longitude):
    marker = folium.Marker(location=(latitude, longitude), icon=folium.Icon(color='red', icon='industry', prefix='fa'))
    st.session_state.pipes.append(marker)




if __name__ == "__main__":
    with st.sidebar:
        choose = option_menu("ECO monitoring", ["About", "Map", "Wind", "Function 3"],
                             icons=['house'], menu_icon="app-indicator", default_index=0,
                             styles={
                                 "container": {"padding": "5!important", "background-color": "#fafafa"},
                                 "icon": {"color": "orange", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#eee"},
                                 "nav-link-selected": {"background-color": "#02ab21"},
                             })
        with st.form(key='add_analyzer_form'):
            st.title("Добавить газоанализатор")
            latitude = st.number_input(label='Координаты долготы', step=.0001, format="%.4f")
            longitude = st.number_input(label='Координаты широты', step=.0001, format="%.4f")
            submit = st.form_submit_button(label='Добавить газоанализатор')
            if submit:
                add_analyzer(latitude, longitude)
        
        with st.form(key='add_pipe_form'):
            st.title("Добавить источник")
            latitude = st.number_input(label='Координаты долготы', step=.0001, format="%.4f")
            longitude = st.number_input(label='Координаты широты', step=.0001, format="%.4f")
            submit = st.form_submit_button(label='Добавить источник')
            if submit:
                add_pipe(latitude, longitude)
    
    if choose == "About":
        st.title('Система идентификации источников выбросов')
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown(""" <style> .font {
                    font-size:35px ; font-family: 'Cooper Black';} 
                    </style> """, unsafe_allow_html=True)
            st.markdown('<p class="font">О приложении</p>', unsafe_allow_html=True)
        
        st.write('**************************************')
    
    elif choose == "Map":
        st.markdown('Приложение использует [OpenRouteService API](https://openrouteservice.org/) '
                    'для определения координат и представления карты.')
        address = st.text_input('Введите адрес.')
        
        if address:
            results = geocode(address)
            if results:
                lat = results[0]
                long = results[1]
                
                st.write('Географические координаты: {}, {}'.format(results[0], results[1]))
                
                m = folium.Map(location=results, zoom_start=11, )
                
                # perm = folium.map.FeatureGroup()
                # perm.add_child(
                #     folium.features.CircleMarker(
                #         location=results, radius=1, color='red', fill_color='Red'
                #     )
                # )
                #
                # m.add_child(perm)
                #
                # folium.Marker(
                #     results,
                #     popup=address,
                #     icon=folium.Icon(color='green', icon='crosshairs', prefix='fa')
                # ).add_to(m)
                folium.TileLayer('Stamen Terrain').add_to(m)
                folium.TileLayer('Stamen Toner').add_to(m)
                folium.TileLayer('Stamen Water Color').add_to(m)
                folium.TileLayer('cartodbpositron').add_to(m)
                folium.TileLayer('cartodbdark_matter').add_to(m)
                
                hm_data = [[56, 57, 5], [56.5, 57, 10], [56, 57.5, 7]]
                
                hm = HeatMap(data=hm_data, name='heatmap', radius=18, auto_play=False, max_opacity=0.8)
                hm.add_to(m)
                
                np.random.seed(3141592)
                initial_data = (np.random.normal(size=(100, 2)) * np.array([[1, 1]]) + np.array([[48, 5]]))
                move_data = np.random.normal(size=(100, 2)) * 0.01
                data = [(initial_data + move_data * i).tolist() for i in range(100)]
                
                time_index = [(datetime.now() + k * timedelta(1)).strftime('%Y-%m-%d') for k in range(len(data))]
                
                heatmap_with_time = HeatMapWithTime(data, index=time_index, name='heatmap with time', auto_play=False,
                                                    max_opacity=0.3)
                heatmap_with_time.add_to(m)
                
                
                
                for company in company_list:
                    folium.Marker(location=(company['latitude'], company['longitude']), popup=company['name']).add_to(m)
                    folium.Circle(location=(company['latitude'], company['longitude']), radius=company['SPZ_width'],
                                  fill_color='red').add_to(m)
                    for sourse in company['emission_sourses']:
                        folium.Marker(location=(sourse['latitude'], sourse['longitude']),
                                      popup=sourse['number']).add_to(m)
                
                coordinates_popup = LatLngPopup()
                m.add_child(coordinates_popup)
                
                analyzers = st.session_state.analyzers
                analyzers_group = folium.FeatureGroup(name="Analyzers").add_to(m)
                
                for analyzer_marker in analyzers:
                    analyzers_group.add_child(analyzer_marker)

                pipes = st.session_state.pipes
                pipes_group = folium.FeatureGroup(name="Pipes").add_to(m)

                for pipe_marker in pipes:
                    pipes_group.add_child(pipe_marker)

                start_gathering_wind_data(lat, long, 5)
                
                wind_group = folium.FeatureGroup(name="Winds").add_to(m)

                for marker in wind_directions_markers:
                    wind_group.add_child(marker)
                
                folium.LayerControl().add_to(m)
                folium_static(m, width=1200, height=650)
            else:
                st.error('Результатов не найдено.')
    
    elif choose == "Wind":
        st.title("Ветра")
        
        address = st.text_input('Введите адрес.')
        
        if address:
            results = geocode(address)
            current_latitude = results[0]
            current_longitude = results[1]
            
            if results:
                # weather_now = current_weather(results[0], results[1])
                # st.write(weather_now["current_weather"])
                
                st.write('Географические координаты: {}, {}'.format(results[0], results[1]))
                
                m = folium.Map(location=results, zoom_start=16)
                
                folium.TileLayer('Stamen Terrain').add_to(m)
                folium.TileLayer('Stamen Toner').add_to(m)
                folium.TileLayer('Stamen Water Color').add_to(m)
                folium.TileLayer('cartodbpositron').add_to(m)
                folium.TileLayer('cartodbdark_matter').add_to(m)
                
                # hm_data = [[56, 57, 5], [56.5, 57, 10], [56, 57.5, 7]]
                #
                # hm = HeatMap(data=hm_data, name='heatmap', radius=18, auto_play=False, max_opacity=0.8)
                # hm.add_to(m)
                #
                folium.LayerControl().add_to(m)
                
                lat = results[0]
                long = results[1]
                # scale_coef = 10
                #
                # for i in np.linspace(0, 1, 1001):
                #     for j in np.linspace(0, 1, 1001):
                #         cur_weather = current_weather(lan + i, long + j)
                #         wind_direction = cur_weather["current_weather"]["winddirection"]
                #         wind_speed = cur_weather["current_weather"]["windspeed"]
                #         arrow_scale = (wind_speed / scale_coef) * 2 + 1
                #         marker = folium.Marker(location=(lan + i, long + j), icon=DivIcon(icon_size=(150, 36),
                #                                                                           icon_anchor=(7, 20),
                #                                                                           html=f'<svg width="20"'
                #                                                                                f'height="20"'
                #                                                                                f'xmlns="http://www.w3.org/2000/svg"'
                #                                                                                f'fill-rule="evenodd"'
                #                                                                                f'clip-rule="evenodd"'
                #                                                                                f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
                #                                                                                f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
                #                                                                                f'</svg>',
                #                                                                           ))
                #         marker.add_to(m)
                
                # multiprocessing_wind_data(lat, long)
                
                # asyncio.run(loop(lat, long))
                
                start_gathering_wind_data(lat, long, 5)
                
                for marker in wind_directions_markers:
                    marker.add_to(m)
                
                folium_static(m, width=800)
            
            else:
                st.error('Результатов не найдено.')

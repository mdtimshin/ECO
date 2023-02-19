from datetime import datetime, timedelta
import asyncio
import aiohttp
import folium
import numpy as np
import pandas as pd
import plost
import requests
from folium.plugins import HeatMapWithTime, HeatMap
from threading import Thread, local
import streamlit as st
from folium import plugins, DivIcon, LatLngPopup
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu
import streamlit_scrollable_textbox as stx

ORS_API_KEY = '5b3ce3597851110001cf6248956c5852f3124220971192bdb7b2909f'

thread_local = local()

wind_directions_markers = []

current_latitude = 0
current_longitude = 0

st.set_page_config(layout="wide")

# with open('style.css') as f:
#     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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


if 'logs' not in st.session_state:
    st.session_state.logs = []


def generate_log(date: datetime, pipe_id):
    st.session_state.logs.append(
        {'message': f'{date.strftime("%m/%d/%Y, %H:%M:%S")} {chr(10)}'
                    f'Датчик номер {pipe_id} зафиксировал высокую концентрацию серы'}
    )


if __name__ == "__main__":
    column_map, column_chat = st.columns((4, 1))
    with st.sidebar:
        choose = option_menu("ECO monitoring", ["About", "Map", "Simulation", "Plots"],
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
                folium_static(m, width=1000, height=650)
            else:
                st.error('Результатов не найдено.')
    
    elif choose == "Simulation":
        
        pipes = [
            {
                'id': 1,
                'lat': 57.9647,
                'long': 56.2778
            },
            {
                'id': 2,
                'lat': 57.9720,
                'long': 56.3254
            }
        ]
        
        analyzers = [
            {
                'id': 1,
                'lat': 57.9818,
                'long': 56.2788
            },
            {
                'id': 2,
                'lat': 57.9664,
                'long': 56.3075
            },
            {
                'id': 3,
                'lat': 57.9488,
                'long': 56.2802
            },
            {
                'id': 4,
                'lat': 57.9662,
                'long': 56.2462
            },
            {
                'id': 5,
                'lat': 57.9834,
                'long': 56.3252
            },
            {
                'id': 6,
                'lat': 57.9724,
                'long': 56.3458
            },
            {
                'id': 7,
                'lat': 57.9599,
                'long': 56.3252
            },
            {
                'id': 8,
                'lat': 57.9712,
                'long': 56.3049
            }
        ]
        
        # data = [
        #     [
        #         [57.9647, 56.2778]
        #     ],
        #     [
        #         [57.9647, 56.2778],
        #         [57.9648, 56.2785],
        #         [57.9650, 56.2783],
        #     ],
        #     [
        #         [57.9647, 56.2778],
        #         [57.9648, 56.2785],
        #         [57.9650, 56.2783],
        #         [57.9650, 56.2795],
        #         [57.9653, 56.2796],
        #         [57.9657, 56.2791],
        #     ],
        #     [
        #         [57.9647, 56.2778],
        #         [57.9648, 56.2785],
        #         [57.9650, 56.2783],
        #         [57.9650, 56.2795],
        #         [57.9653, 56.2796],
        #         [57.9657, 56.2791],
        #         [57.9657, 56.2822],
        #         [57.9657, 56.2820],
        #         [57.9662, 56.2817],
        #         [57.9666, 56.2813],
        #     ],
        # ]
        #
        # injection_data = data
        # added_points = injection_data[-1]
        #
        # for i in range(10):
        #     last_points = added_points
        #     points = last_points
        #     list = []
        #     for point in points:
        #         new_points = [round(0.001 + x, ndigits=4) for x in point]
        #         list.append(new_points)
        #
        #     added_points = last_points + list
        #     injection_data.append(added_points)
        
        data = []
        iterations = 10
        
        pipe_lat = pipes[0]['lat']
        pipe_long = pipes[0]['long']
        
        data.append([[pipe_lat, pipe_long]])
        
        for iteration in range(iterations):
            last_points = data[-1].copy()
            new_points = []
            if len(last_points) == 1:
                new_points.extend([[last_points[0][0] + 0.0016, last_points[0][1]],
                                   [last_points[0][0] + 0.0016,
                                    last_points[0][1] + 0.0009],
                                   [last_points[0][0], last_points[0][1] + 0.0005]])
                # data.append(last_points.extend(new_points))
            else:
                new_points.extend([[last_points[0][0] + 0.0016, last_points[0][1]]])
                # [round(0.0001 + x, ndigits=4) for x in last_points[1:-1]],
                # [last_points[-1][0], round(last_points[-1][1] + 0.0001, ndigits=4)]]
                middle_list = last_points.copy()
                middle_points = []
                for point in middle_list:
                    middle_points.append([0.0016 + x for x in point])
                new_points.extend(middle_points)
                new_points.append([last_points[-1][0], last_points[-1][1] + 0.0001])
                
                # data.append(last_points.extend(new_points))
            
            list = last_points.copy()
            list.extend(new_points)
            data.append(list)
        
        # time_index = [(datetime.now() + k * timedelta(1)).strftime('%Y-%m-%d') for k in range(len(injection_data))]
        time_index = [(datetime.now() + k * timedelta(minutes=1)).strftime("%m/%d/%Y, %H:%M:%S") for k in
                      range(len(data))]
        # time_index = [
        #     datetime(2023, 1, 16, 23, 30),
        #     datetime(2023, 1, 16, 23, 31),
        #     datetime(2023, 1, 16, 23, 32),
        #     datetime(2023, 1, 16, 23, 33)
        # ]
        with column_map:
            address = st.text_input('Введите адрес.')
            
            if address:
                results = geocode(address)
                current_latitude = results[0]
                current_longitude = results[1]
                
                if results:
                    st.write('Географические координаты: {}, {}'.format(results[0], results[1]))
                    
                    m = folium.Map(location=results, zoom_start=16)
                    
                    coordinates_popup = LatLngPopup()
                    m.add_child(coordinates_popup)
                    
                    folium.TileLayer('Stamen Terrain').add_to(m)
                    folium.TileLayer('Stamen Toner').add_to(m)
                    folium.TileLayer('Stamen Water Color').add_to(m)
                    folium.TileLayer('cartodbpositron').add_to(m)
                    folium.TileLayer('cartodbdark_matter').add_to(m)
                    
                    lat = results[0]
                    long = results[1]
                    
                    start_gathering_wind_data(lat, long, 5)
                    
                    wind_group = folium.FeatureGroup(name="Winds").add_to(m)
                    
                    for marker in wind_directions_markers:
                        wind_group.add_child(marker)
                    
                    pipes_group = folium.FeatureGroup(name='Pipes').add_to(m)
                    
                    for pipe in pipes:
                        marker = folium.Marker(location=(pipe['lat'], pipe['long']),
                                               icon=folium.Icon(color='red', icon='industry', prefix='fa'))
                        pipes_group.add_child(marker)
                    
                    analyzers_group = folium.FeatureGroup(name='Analyzers').add_to(m)
                    
                    for analyzer in analyzers:
                        marker = folium.Marker(location=(analyzer['lat'], analyzer['long']),
                                               icon=folium.Icon(color='lightgray', icon='eye', prefix='fa'))
                        pipes_group.add_child(marker)
                    
                    heatmap_with_time = HeatMapWithTime(data=data, index=time_index, name='heatmap with time',
                                                        auto_play=False,
                                                        max_opacity=0.3)
                    heatmap_with_time.add_to(m)
                    
                    folium.LayerControl().add_to(m)
                    folium_static(m, width=1000, height=650)
                
                else:
                    st.error('Результатов не найдено.')
        with column_chat:
            
            st.title('Логи')
            
            for id in range(10):
                generate_log(datetime.now() + timedelta(minutes=id), id)
            
            logs = [x['message'] for x in st.session_state.logs]
            logs = chr(10).join(logs)
            
            stx.scrollableTextbox(text=logs, height=700, fontFamily='Helvetica', border=True)
    
    elif choose == "Plots":
        
        analyzer_id = st.selectbox(label='Выберите номер газоанализатора', options=('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        
        if analyzer_id == '9':
            df_analyzer = pd.read_csv('datasets/PM10_9_74040129_272.csv', header=None,
                                        names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])
            
            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '8':
            df_analyzer = pd.read_csv('datasets/PM10_8_74040128_260.csv', header=None,
                                        names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])
    
            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '7':
            df_analyzer = pd.read_csv('datasets/PM10_7_74040127_248.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])

            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '6':
            df_analyzer = pd.read_csv('datasets/PM10_6_74040126_236.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])

            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '5':
            df_analyzer = pd.read_csv('datasets/PM10_5_74040125_224.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])

            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '4':
            df_analyzer = pd.read_csv('datasets/PM10_4_74040124_212.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])

            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '3':
            df_analyzer = pd.read_csv('datasets/PM10_3_74040123_200.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])
    
            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '2':
            df_analyzer = pd.read_csv('datasets/PM10_2_74040122_188.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])
    
            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации')
        if analyzer_id == '1':
            df_analyzer = pd.read_csv('datasets/PM10_1_74040121_176.csv', header=None,
                                      names=['date', 'value'])
            df_analyzer.dropna(axis=0, inplace=True)
            df_analyzer.iloc[:, 0] = pd.to_datetime(df_analyzer.iloc[:, 0])
    
            plost.line_chart(data=df_analyzer, x='date', y='value', title='Значения концентрации', pan_zoom='minimap')
        
        
            # history = [
            #     {
            #         'message': 'Привет',
            #         'is_user': False
            #     },
            #     {
            #         'message': 'Здесь можно увидеть логи',
            #         'is_user': False
            #     },
            # ]
            #
            # for message in history:
            #     st_message(**message)
            #
            # for id in range(10):
            #     generate_log(datetime.now() + timedelta(minutes=id), id)
            #
            # for chat in st.session_state.logs:
            #     st_message(**chat)
        
        # address = st.text_input('Введите адрес.')
        #
        # if address:
        #     results = geocode(address)
        #     current_latitude = results[0]
        #     current_longitude = results[1]
        #
        #     if results:
        #         st.write('Географические координаты: {}, {}'.format(results[0], results[1]))
        #
        #         m = folium.Map(location=results, zoom_start=16)
        #
        #         coordinates_popup = LatLngPopup()
        #         m.add_child(coordinates_popup)
        #
        #         folium.TileLayer('Stamen Terrain').add_to(m)
        #         folium.TileLayer('Stamen Toner').add_to(m)
        #         folium.TileLayer('Stamen Water Color').add_to(m)
        #         folium.TileLayer('cartodbpositron').add_to(m)
        #         folium.TileLayer('cartodbdark_matter').add_to(m)
        #
        #         lat = results[0]
        #         long = results[1]
        #
        #         start_gathering_wind_data(lat, long, 5)
        #
        #         wind_group = folium.FeatureGroup(name="Winds").add_to(m)
        #
        #         for marker in wind_directions_markers:
        #             wind_group.add_child(marker)
        #
        #         pipes_group = folium.FeatureGroup(name='Pipes').add_to(m)
        #
        #         for pipe in pipes:
        #             marker = folium.Marker(location=(pipe['lat'], pipe['long']),
        #                                    icon=folium.Icon(color='red', icon='industry', prefix='fa'))
        #             pipes_group.add_child(marker)
        #
        #         analyzers_group = folium.FeatureGroup(name='Analyzers').add_to(m)
        #
        #         for analyzer in analyzers:
        #             marker = folium.Marker(location=(analyzer['lat'], analyzer['long']),
        #                                    icon=folium.Icon(color='lightgray', icon='eye', prefix='fa'))
        #             pipes_group.add_child(marker)
        #
        #         heatmap_with_time = HeatMapWithTime(data=data, index=time_index, name='heatmap with time', auto_play=False,
        #                                             max_opacity=0.3)
        #         heatmap_with_time.add_to(m)
        #
        #         folium.LayerControl().add_to(m)
        #         folium_static(m, width=1200, height=650)
        #
        #     else:
        #         st.error('Результатов не найдено.')

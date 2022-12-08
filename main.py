import math
import folium
import numpy as np
import requests
import streamlit as st
from folium import plugins, DivIcon
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

ORS_API_KEY = '5b3ce3597851110001cf6248956c5852f3124220971192bdb7b2909f'


def arrow_points_calculate(ini_lat, ini_long, heading):
    lenght_scale = 0.012
    sides_scale = 0.0025
    sides_angle = 25

    latA = ini_lat
    longA = ini_long

    latB = lenght_scale * math.cos(math.radians(heading)) + latA
    longB = lenght_scale * math.sin(math.radians(heading)) + longA

    latC = sides_scale * math.cos(math.radians(heading + 180 - sides_angle)) + latB
    longC = sides_scale * math.sin(math.radians(heading + 180 - sides_angle)) + longB

    latD = sides_scale * math.cos(math.radians(heading + 180 + sides_angle)) + latB
    longD = sides_scale * math.sin(math.radians(heading + 180 + sides_angle)) + longB

    pointA = (latA, longA)
    pointB = (latB, longB)
    pointC = (latC, longC)
    pointD = (latD, longD)

    point = [pointA, pointB, pointC, pointD, pointB]
    return point


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
            st.write('Географические координаты: {}, {}'.format(results[0], results[1]))

            m = folium.Map(location=results, zoom_start=11, )

            perm = folium.map.FeatureGroup()
            perm.add_child(
                folium.features.CircleMarker(
                    location=results, radius=1, color='red', fill_color='Red'
                )
            )

            m.add_child(perm)

            folium.Marker(
                results,
                popup=address,
                icon=folium.Icon(color='green', icon='crosshairs', prefix='fa')
            ).add_to(m)
            folium.TileLayer('Stamen Terrain').add_to(m)
            folium.TileLayer('Stamen Toner').add_to(m)
            folium.TileLayer('Stamen Water Color').add_to(m)
            folium.TileLayer('cartodbpositron').add_to(m)
            folium.TileLayer('cartodbdark_matter').add_to(m)
            folium.LayerControl().add_to(m)
            folium_static(m, width=800)
        else:
            st.error('Результатов не найдено.')

elif choose == "Wind":
    st.title("Ветра")

    address = st.text_input('Введите адрес.')

    if address:
        results = geocode(address)

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
            folium.LayerControl().add_to(m)

            lan = results[0]
            long = results[1]
            scale_coef = 10

            for i in np.linspace(0, 1, 1001):
                for j in np.linspace(0, 1, 1001):
                    cur_weather = current_weather(lan + i, long + j)
                    wind_direction = cur_weather["current_weather"]["winddirection"]
                    wind_speed = cur_weather["current_weather"]["windspeed"]
                    arrow_scale = (wind_speed/scale_coef)*2 + 1
                    marker = folium.Marker(location=(lan + i, long + j), icon=DivIcon(icon_size=(150, 36),
                                                                      icon_anchor=(7, 20),
                                                                      html=f'<svg width="20"'
                                                                           f'height="20"'
                                                                           f'xmlns="http://www.w3.org/2000/svg"'
                                                                           f'fill-rule="evenodd"'
                                                                           f'clip-rule="evenodd"'
                                                                           f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
                                                                           f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
                                                                           f'</svg>',
                                                                      ))
                    marker.add_to(m)


            # wind_direction = weather_now["current_weather"]["winddirection"]
            # wind_speed = weather_now["current_weather"]["windspeed"]
            # scale_coef = 10
            # arrow_scale = (wind_speed/scale_coef)*2 + 1

            # marker = folium.Marker(location=results, icon=DivIcon(icon_size=(150, 36),
            #                                                       icon_anchor=(7, 20),
            #                                                       html=f'<svg width="20"'
            #                                                            f'height="20"'
            #                                                            f'xmlns="http://www.w3.org/2000/svg"'
            #                                                            f'fill-rule="evenodd"'
            #                                                            f'clip-rule="evenodd"'
            #                                                            f'transform="rotate({wind_direction}) scale(1 {arrow_scale})">'
            #                                                            f'<path d="M11 2.206l-6.235 7.528-.765-.645 7.521-9 7.479 9-.764.646-6.236-7.53v21.884h-1v-21.883z"/>'
            #                                                            f'</svg>',
            #                                                       ))
            # marker.add_to(m)

            folium_static(m, width=800)
        else:
            st.error('Результатов не найдено.')

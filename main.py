import folium
import requests
import streamlit as st
from streamlit_folium import folium_static

st.title('Система мониторинга выбросов')
st.markdown('Приложение использует [OpenRouteService API](https://openrouteservice.org/) '
            'для определения координат и представления карты.')

address = st.text_input('Введите адрес.')

ORS_API_KEY = '5b3ce3597851110001cf6248956c5852f3124220971192bdb7b2909f'

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


if address:
    results = geocode(address)
    if results:
        st.write('Географические координаты: {}, {}'.format(results[0], results[1]))

        m = folium.Map(location=results, zoom_start=11, )
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
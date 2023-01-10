import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium


def create_map(list_points):
    m = folium.Map()
    points=[]
    for i in range(len(list_points)):
        points.append([list_points[i][1], list_points[i][0]])
    df=pd.DataFrame(points, columns=['Lat','Long'])
    for i in range(len(list_points)-2):
        folium.Marker(points[i],  popup=('Add'), icon = folium.Icon(color='green',icon='plus')).add_to(m)
    sw = df[['Lat', 'Long']].min().values.tolist()
    ne = df[['Lat', 'Long']].max().values.tolist()
    m.fit_bounds([sw, ne])
    return m

def extract_pop_metrics(df, Color):
    if Color=='All':
        df_ok=df
    else:
        df_ok=df[df['Primary Fur Color']==Color]
    tot_pop=df_ok.shape[0]
    pc_pop=round(tot_pop/df.shape[0]*100,1)
    tot_Hectare=len(df_ok.Hectare.unique().tolist())
    mean_pop_hect=round(tot_pop/tot_Hectare,1)
    pc_young=round(df_ok[df_ok.Age=='Juvenile'].shape[0]/tot_pop*100,1)
    pc_trees=round(df_ok[df_ok.Location=='Above Ground'].shape[0]/tot_pop*100,1)

    return [tot_pop, pc_pop, tot_Hectare, mean_pop_hect, pc_young, pc_trees]

class Hectare_socio_colour:
    def __init__(self, name, colour):
        self.name = name
        self.colour = colour

    def compute_count(self, df):
        if self.colour=='All':
            df_ok = df[(df.Hectare == self.name)]
            self.tot_otherSquirrel = 0
        else:
            df_ok = df[(df.Hectare == self.name) & (df['Primary Fur Color'] == self.colour)]
            self.tot_otherSquirrel = df[(df.Hectare == self.name) & (df['Primary Fur Color'] != self.colour)].shape[0]
        self.tot_count = df_ok.shape[0]
        self.tot_unattentive = df_ok[(df_ok.Running) & (df_ok.Foraging)].shape[0]
        self.tot_eating = df_ok[df_ok.Eating].shape[0]
        self.tot_indifferent = df_ok[df_ok.Indifferent].shape[0]

        list_alerts = ['Kuks', 'Quaas', 'Moans', 'Tail flags', 'Tail twitches']
        self.tot_alerts = sum([df_ok[df_ok[my_alert] == True].shape[0] for my_alert in list_alerts])

    def compute_GPS(self,df):
        if self.colour=='All':
            df_ok = df[(df.Hectare == self.name)]
        else:
            df_ok = df[(df.Hectare == self.name) & (df['Primary Fur Color'] == self.colour)]
        mean_X=df_ok.X.mean()
        mean_Y=df_ok.Y.mean()
        self.mean_GPS=[mean_X, mean_Y]

    def compute_score(self):
        self.score = self.tot_unattentive * 0.5 + self.tot_indifferent + self.tot_otherSquirrel * 0.1 + self.tot_eating * 2 + self.tot_alerts * -0.2

def get_optimum_position(Color, df, pc_max_score=30):
    list_hectare = df.Hectare.unique().tolist()
    results = []
    # we loop on each Hectare to compute its score
    for my_hect in list_hectare:
        the_Hect = Hectare_socio_colour(my_hect, Color)
        the_Hect.compute_count(df)
        the_Hect.compute_score()
        results.append([my_hect, the_Hect.score])
    # we build a results dataframe
    results_df = pd.DataFrame(results, columns=['Hectare', 'score']).sort_values(by=['score'],ascending=False).reset_index(drop=True)
    results_df['cumulative_score'] = results_df.score.cumsum()

    # we list the Hectares where it is works advertising to reach the % of the max cumulative impact_score
    max_score = int(results_df.cumulative_score.iloc[-1])
    max_target_score = round(pc_max_score * max_score / 100, 1)
    list_best_Hectares = results_df[results_df.cumulative_score <= max_target_score].Hectare.tolist()

    #we list the mean positions of the max 10 best spots
    if len(list_best_Hectares)<10:
        max_iter=len(list_best_Hectares)
    else:
        max_iter=10
    list_GPS_best=[]
    for i in range(max_iter):
        my_hect=list_best_Hectares[i]
        the_Hect = Hectare_socio_colour(my_hect, Color)
        the_Hect.compute_GPS(df)
        list_GPS_best.append(the_Hect.mean_GPS)

    #compare to a random positioning of the same number of adds
    # TO CONTINUE

    return list_best_Hectares, max_score, pc_max_score, Color, list_GPS_best

### Main streamlit code

st.image('squirrels.jpeg')
st.title("🌰🐿👁‍🗨 Squirrels 'n Nuts" )
st.subheader('Advertise Nuts for Squirrels in Central Park- NYC')
st.write("Let's imagine YOU want to invest for advertising specifc nuts in Central Park \n to target specifc Squirrels populations.")
st.subheader("Let's show YOU where to go!")

df=pd.read_csv('Squirrels-Census_data.csv')
squirr_color_list=['All','Gray','Cinnamon','Black']

col1, col2=st.columns(2)
#chose the color
chosen_color=col1.selectbox('Which Squirrels Population to target?', tuple(squirr_color_list))

#chose the percent of max impact
pc_max_score=col2.number_input('Target Impact of the adds (% of max Impact)', min_value=1, max_value=100, value=30)
#extract main metrics
main_stats = extract_pop_metrics(df, chosen_color)

#show main metrics
list_prop=['# Individuals','% of tot','# Hectares','# per Hectare','% young','% in trees']
cols=st.columns(len(list_prop))
for i in range(len(list_prop)):
    cols[i].metric(list_prop[i], str(main_stats[i]), delta=None,delta_color="normal")

#extract Hectares info
list_best_Hectares, max_score, pc_max_score, Color, list_GPS_best=get_optimum_position(chosen_color, df, pc_max_score)
st.write('{} adds for {} Squirrels to reach {}% of the maxscore={}'.format(len(list_best_Hectares), Color, pc_max_score, max_score))
#we add the minimum and maximum GPS positions to the list of best points at the end
min_X=df.X.min()
max_X=df.X.max()
min_Y=df.Y.min()
max_Y=df.Y.max()
min_GPS=[min_X, min_Y]
max_GPS=[max_X, max_Y]
list_GPS_best.append(min_GPS)
list_GPS_best.append(max_GPS)

print(list_GPS_best)

map =create_map(list_GPS_best, value_to_write='best Adds positions')
st.write('Showing positions for the best Adds (max. 10) 🎯')
st.session_state['map'] = map
# st.session_state['list_map_objects']=[polyline,spans,dict_output]
# st.session_state['synthesis']=synthesis
# st.write(st.session_state['synthesis'])
folium_static(st.session_state['map'])

st.write("*******************************************")
st.caption("Hypothesis for the Adds campaign impact computation are: "
           "1.there are zone of the parks with clusters of population of squirrels; "
           "2. running or foraging squirrels do not pay attention to adds as they are stressed (factor 0.5); "
           "3.while eating, squirrels are very attentive to adds  (factor 2); "
           "4.only indifferent squirrels count (factor 1);"
           "5.some squirrels like the taste of others squirrels populations: so total squirrel population which is not the targetted colour count for 0.1  (factor 0.1); "
           "6.Squirrels alerted of predators do not pay attention to adds and make other do not look: it is a negative factor (factor -0.2)")
st.caption("Dataset can be found here: https://catalog.data.gov/dataset/2018-central-park-squirrel-census-squirrel-data")
st.caption("Developped by Jean MILPIED")

import copy#deep copying objects, which allows us to create an independent copy
import pandas as pd
import streamlit as st
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static
from config.config_loader import get_config_with_name
#two measures we will add as point layers:trip_count & passenger count
#each measure will be represented as a seperate layer based on selection
point_measures=["trip_count","passenger_count"]
h3_measures=["trip_count","passenger_count"]
line_measures=["trip_count","passenger_count"]

def add_layer_to_config(
    config,layer_id,layer_type,layer_template,tooltip_fields
):
    layer_config=copy.deepcopy(layer_template[layer_type])
    layer_config["id"]=layer_id
    layer_config["config"]["dataID"]=layer_id
    layer_config["config"]["label"]=layer_id
    
    #The layer serves as the name tag for the layer displayed on the map一个名称
    #The layer ID is a unique value used internally to identify each layer and is not visible on the map
    #The data ID specifies the data set used by the layer (must match the name used when calling data, ensuring the map configuration is properly linked to the data
    
    config["config"]["visState"]["interactionConfig"]["tooltip"]["fieldsToShow"]={
      layer_id:tooltip_fields 
    
    }#configure the tooltip fields, allowing users to view specific information when exploring the map
    
    #add layer config to the list of layers and config, ensuring the new layer is reflected in the map settings
    config["config"]["visState"]["layers"].append(layer_config)
    return config

def add_boundary_layers(boundary_df,map_obj,config,layer_template):#有很多块地界
    for i in range(len(boundary_df)):
        #a unique layer id is generated for each boundary to wnsure it can be uniquely identified
        #ensures that a seperate layer is created for each boundary in 纽约
        layer_id=f"Boundary{boundary_df.iloc[i].boundary_id}"
        #add the boundary data row to map object and assign layer ID as its name
        map_obj.add_data(data=boundary_df.iloc[[i]],name=layer_id)
        #define the fields to display in the tooltip
        tooltip_fields=[
            {"name":"boundary_id","format":None},
            {"name":"boundary_name","format":None},
        ]
        #add layer to config
        config=add_layer_to_config(
            config=config,
            layer_id=layer_id,
            layer_type="boundary",
            layer_template=layer_template,
            tooltip_fields=tooltip_fields,

        )
    return map_obj, config

def add_point_layers(
        point_df,selected_point_measures,map_obj,config,layer_template
):
    for measure in selected_point_measures:
        filtered_point_df=point_df[point_df[measure]>0]#only data with values are displayed
       #generate a unique layer id for each measure
        layer_id=f"Point {measure}"

        point_data=[]
        for _, row in filtered_point_df.iterrows():
            point_data.append(
                {
                    "lat":row["lat"],
                    "lng":row["lng"],
                    "measure":row[measure],
                }
            )
        #转成dataframe
        point_df_converted=pd.DataFrame(point_data).applymap(
            #missing value转成none，因为一般来说没有数据都会变成nan，但nan会导致报错
            lambda x: None if pd.isna(x) else x
        )
        map_obj.add_data(data=point_df_converted,name=layer_id)
        #allow the measure field to be displayed in tooltips
        tooltip_fields=[
            {"name":"measure","format":None},
        ]
        config=add_layer_to_config(
            config=config,
            layer_id=layer_id,
            layer_type="point",
            layer_template=layer_template,
            tooltip_fields=tooltip_fields,


        )
    return map_obj,config
def add_h3_layers(
        h3_df,selected_h3_measures,map_obj,config,layer_template
):
    for measure in selected_h3_measures:
        filtered_h3_df=h3_df[h3_df[measure]>0]
        layer_id=f"H3 {measure}"
        h3_data=[]
        for _, row in filtered_h3_df.iterrows():
            h3_data.append(
                {
                    "h3_resolution":row["h3_resolution"],
                    "h3_index":row["h3_index"],
                    "measure":row[measure],
                }
            )
        h3_df_converted=pd.DataFrame(h3_data).applymap(
            lambda x:None if pd.isna(x) else x
        )
        map_obj.add_data(data=h3_df_converted,name=layer_id)
        tooltip_fields=[
            {"name":"h3_resolution","format":None},
            {"name":"h3_index","format":None},
            {"name":"measure","format":None},
        ]
        config=add_layer_to_config(
            config=config,
            layer_id=layer_id,
            layer_type="h3",
            layer_template=layer_template,
            tooltip_fields=tooltip_fields,
        )
    return map_obj,config
def add_line_layers(
        line_df,selected_line_measures,map_obj,config,layer_template   
):
    for measure in selected_line_measures:
        filtered_line_df=line_df[line_df[measure]>0]
        line_layer_id=f"Line {measure}"
        line_start_layer_id=f"Line Start {measure}"

        line_data=[]
        line_start_data=[]
        for _, row in filtered_line_df.iterrows():
            line_data.append(
                {
                    "start_lat":row["start_lat"],
                    "start_lng":row["start_lng"],
                    "end_lat":row["end_lat"],
                    "end_lng":row["end_lng"],
                    "measure":row[measure],
                }
            )
            line_start_data.append(
                 {
                    "start_lat":row["start_lat"],
                    "start_lng":row["start_lng"],
                    "measure":row[measure],
                }
            )
        line_df_converted=pd.DataFrame(line_data).applymap(
            lambda x:None if pd.isna(x) else x
        )
        line_start_df_converted=pd.DataFrame(line_start_data).applymap(
            lambda x:None if pd.isna(x) else x

        )
        map_obj.add_data(data=line_df_converted,name=line_layer_id)
        map_obj.add_data(data=line_start_df_converted,name=line_start_layer_id)
        tooltip_fields=[
            {"name":"measure","format":"None"},

        ]
        config=add_layer_to_config(
            config=config,
            layer_id=line_layer_id,
            layer_type="line",
            layer_template=layer_template,
            tooltip_fields=tooltip_fields,
        )
        config=add_layer_to_config(
            config=config,
            layer_id=line_start_layer_id,
            layer_type="line_start",
            layer_template=layer_template,
            tooltip_fields=tooltip_fields,

        )
    return map_obj,config





def initialize_session_state():#初始配置
    default_values={
        "map_initialized":False,
        "map_obj":None,
        "boundary_df":pd.DataFrame(),
        "point_df":pd.DataFrame(),
        "h3_df":pd.DataFrame(),
        "line_df":pd.DataFrame(),
        "show_boundary":False,
        "show_point":False,
        "show_h3":False,
        "show_line":False,
        "selected_point_measures":[],
        "selected_h3_measures":[],
        "selected_line_measures":[],




    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key]=value
def create_map(layer_order):
    config=get_config_with_name ("base")  
#load a layer template from the JSON file
    layer_template=get_config_with_name("new_york_city_taxi")
    map_obj=KeplerGl(height=800,config=config)
    for layer in layer_order:
        if layer=="boundary" and st.session_state.get("show_boundary",False):
            map_obj,config=add_boundary_layers(
                st.session_state["boundary_df"],
                map_obj,
                config,
                layer_template,   

            )
        elif layer=="point" and st.session_state.get("show_point",False):
            map_obj,config=add_point_layers(
                st.session_state["point_df"],
                st.session_state["selected_point_measures"],
                map_obj,
                config,
                layer_template,
            )

        elif layer=="h3" and st.session_state.get("show_h3",False):
            map_obj,config=add_h3_layers(
                st.session_state["h3_df"],
                st.session_state["selected_h3_measures"],
                map_obj,
                config,
                layer_template,

            )
        elif layer=="line" and st.session_state.get("show_line",False):
            map_obj,config=add_line_layers(
                st.session_state["line_df"],
                st.session_state["selected_line_measures"],
                map_obj,
                config,
                layer_template,
            )

    map_obj.config=config
    return map_obj

def display_map():
    if st.session_state["map_initialized"]:
        keplergl_static(st.session_state["map_obj"],center_map=True)
    else:
        st.warning("Click 'Apply' to display the map.")



def main():
    st.title("New York City Taxi")
    initialize_session_state()
#include an expandable section
#以下的写法不会自动更新，需要另外点击apply键
    with st.form(key="conditions"):
        #define filters to apply to the data
        with st.expander("Data confitions",expanded=True):
            #四列
            cols=st.columns(4)
            with cols[0]:
                location_base=st.selectbox("Location Base",["PICKUP","DROPOFF"])
            with cols[1]:
                h3_resolution=st.slider(
                    "H3 Resolution",min_value=5,max_value=7,value=5
                )

        with st.expander("Select layers",expanded=True):
            cols=st.columns(4)
            with cols[0]:
                st.session_state["show_boundary"]=st.checkbox(
                    "Boundaries",
                    value=st.session_state["show_boundary"],

                )
            selected_point_measures=[]
            with cols[1]:
                for measure in point_measures:
                    is_selected=st.checkbox(
                        f"Point {measure}",
                        value=False,
                        key=f"pont_{measure}",
                    )
                    if is_selected:
                        selected_point_measures.append(measure)
                st.session_state["show_point"]=len(selected_point_measures)>0
                st.session_state["selected_point_measures"]=selected_point_measures

            selected_h3_measures=[]
            with cols[2]:
                for measure in h3_measures:
                    is_selected=st.checkbox(
                        f"H3 {measure}",
                        value=False,
                        key=f"h3_{measure}",
                    )
                    if is_selected:
                        selected_h3_measures.append(measure)
                st.session_state["show_h3"]=len(selected_h3_measures)>0
                st.session_state["selected_h3_measures"]=selected_h3_measures

            selected_line_measures=[]
            with cols[3]:
                for measure in line_measures:
                    is_selected=st.checkbox(
                        f"Line {measure}",
                        value=False,
                        key=f"line_{measure}",
                    )
                    if is_selected:
                        selected_line_measures.append(measure)
                st.session_state["show_line"]=len(selected_h3_measures)>0
                st.session_state["selected_line_measures"]=selected_line_measures
        with st.expander("Select Layer Order",expanded=False):
            layer_order=st.multiselect(
                "Layer Order (Top <-> Bottom)",
                ["line","point","h3","boundary"],
                default=["line","point","h3","boundary"],

            )




        submit_button=st.form_submit_button(label="Apply")
    if submit_button:
        #provide a loading message
        with st.spinner("The map is being generated."):
            if st.session_state.get("show_boundary",False):
                boundary_df=pd.read_csv("data/boundary_data.csv")
                st.session_state["boundary_df"]=boundary_df
            if st.session_state.get("show_point",False):
                point_df=pd.read_csv("data/point_data.csv")
                point_df=point_df[point_df["location_base"]==location_base]
                st.session_state["point_df"]=point_df
            if st.session_state.get("show_h3",False):
                h3_df=pd.read_csv("data/h3_data.csv")
                h3_df=h3_df[(h3_df["location_base"]==location_base)&(h3_df["h3_resolution"]==h3_resolution)]
                st.session_state["h3_df"]=h3_df
            if st.session_state.get("show_line",False):
                line_df=pd.read_csv("data/line_data.csv")
                st.session_state["line_df"]=line_df
                






            st.session_state["map_obj"]=create_map(layer_order)
            st.session_state["map_initialized"]=True
    display_map()
    
          

if __name__ == "__main__":
    main()

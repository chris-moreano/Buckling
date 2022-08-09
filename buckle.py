import os #used to crawl into directories to find files
import pandas as pd
import numpy as np
from io import BytesIO
from fpdf import FPDF
pd.options.mode.chained_assignment = None  # default='warn'
import matplotlib.pyplot as plt

from bb_lib import *

# Go to BB_LIB.PY and make sure your tube ID and info is filled into the dictionary
# should be around like 315, dictionary name is break_dic.
# ==============================================================
#Iterate through Parent Directory
#Generates Dictionary with Batches as Key, Filepaths as values
# INPUT: None
# OUTPUT: [[filename,filepath],[filename2,path2]]
# ==============================================================

decimal_places = 9
cwd = os.getcwd()
listofcsvs = []
graphTitle = []
pathcsv = []
item_dic = {'Properties\Sample': ["Mandrel Diameter[m]",
                        "Laminate Thickness[m]",
                        "Span[m]",
                        "Failure Span Location[m]",
                        "Post Buckled Displacement[m]",
                        "Load at Failure[N]",
                        "Outside Radius[m]",
                        "Inside Radius[m]",
                        "Cross Sectional Area[m^2]",
                        "Second Moment of Area[m^4]",
                        "Peak Eccentricity[m]",
                        "Eccentricity at Failure Location[m]",
                        "Axial Stress[Pa]",
                        "Bending Moment[Nm]",
                        "Bending Stress[Pa]",
                        "Peak Laminate Failure Stress[Mpa]"]}
property_list = []
bytes_list = []
for subdir, dirs, files in os.walk(cwd):
    
    for file in files:
        filepath = subdir + os.sep + file
        if file.endswith(".csv") and not file.endswith("Events.csv"):
            if file.startswith("M"):
                if os.path.getsize(filepath) > 10000: # Magic number to filter out empty CSVs , 10000 bytes = 10kb
                    tempString = file.translate({ ord(c): None for c in "-" }) 
                    listofcsvs.append(tempString)
                    pathcsv.append(filepath)
                    graphTitle.append(tempString[6:14])
                    #listofcsvs.append([tempString, filepath])
                    #print("file: " + file + " Filepath: " + filepath)


print (pathcsv)

#print(len(listofcsvs))

for iname,files in enumerate(pathcsv):
    with open(files) as file_name:
        
                #if filename is a csv file... process data file
        if ".csv" in files:
            #print(datafile)
            file_data = pd.read_csv(file_name)
            #some files dont have the S:load column but Ch:load, 
            # if found, rename and reassign to dataframe
            tempString = "Ch:Load (lbs)"
            if tempString in file_data.columns:
                file_data = file_data.rename(columns={"Ch:Load (lbs)": "S:Load (lbs)"})
     
            file_data=file_data[["S:Load (lbs)","S:Position (in)","Time (sec)"]]
            file_data = file_data.loc[:,~file_data.columns.duplicated()]
        
    
    file_data.drop(file_data.columns.difference(["S:Load (lbs)","S:Position (in)","Time (sec)"]), 1, inplace=True)
    load = file_data["S:Load (lbs)"].values
    position = file_data["S:Position (in)"].values

    loadmax = np.amax(load) #Find largest peak in Load
    max_len = np.amax(position)

    #print(loadmax)
    #print(max_len)

        # Process Data for Buckling
        # All data seems similar
        # and area to be analyzes is between 4000 and 6000 pounds
        # save this portion of data and perform analysis
    slope_data = file_data.loc[(file_data["S:Load (lbs)"] >= 4000) & (file_data["S:Load (lbs)"] < 6000)]
        
    #print("RTD Slope Data")
    #print(slope_data)
    slope_data["S:Load (lbs)"] = slope_data["S:Load (lbs)"].values
    slope_data["S:Position (in)"] = slope_data["S:Position (in)"].values

    # Slope Data of initial slope
    slope_m,slope_b = np.polyfit(slope_data["S:Load (lbs)"],slope_data["S:Position (in)"],1)

    print(slope_m)
    print(slope_b)


        # Calculate the percent change of all load values,  pc = x2-x1/x1 
    file_data["%_Change"] = file_data["S:Load (lbs)"].pct_change(periods = 1)

    last_ten = file_data.iloc[-10:]
     
    last_ten["%_Change"] = last_ten["%_Change"].abs()


        # Look for percent change in between .20 and 1
        # save index to last_point
    last_point = last_ten.loc[(last_ten["%_Change"] >= .20) & (last_ten["%_Change"] <= 1.0009)].index

        # Find the point before the drop 
    last_p_value = file_data.iloc[last_point-1].values[0][0]

    number_rows = len(file_data.index)

        # take the data and find the roots of the intersecting lines.
    z = find_roots(position,load-last_p_value)
        #print(z)

        # this is not the real value#
    # INITIAL AND FINAL POSITION
    buckle_initial = round(z[0],6)
    buckle_final = z[len(z)-1]


    print("\nInitial Position: ",buckle_initial)
    print("Final Position: ",buckle_final)

    load_initial = file_data[file_data["S:Position (in)"]== find_nearest(position,buckle_initial)].index
    load_final = file_data[file_data["S:Position (in)"]== find_nearest(position,buckle_final)].index

        #maxindex = np.where(loadpeaks == loadmax) #Find index of largest peak
    #FINAL and INITIAL TIME
    initial_time = float(file_data["Time (sec)"].iloc[load_initial].values)
    final_time = float(file_data["Time (sec)"].iloc[load_final].values)

    #FINAL AND INITIAL LOAD
    load_initial = round(float(file_data["S:Load (lbs)"].iloc[load_initial].values),3)
    load_final = round(float(file_data["S:Load (lbs)"].iloc[load_final].values),3)




    print("Initial Time: ",initial_time)
    print("Final Time: ",final_time)

    #post buckling displacement 
    rate_change = (buckle_final-buckle_initial)

    print("Initial Position: ",z[0])
    print("Final Position: ",z[len(z)-1])

    print("Initial Load: " ,load_initial)
    print("Final Load: ",load_final)
    print("Post Buckling Displacement: ",rate_change*0.0254)
    span_Var = float(break_dic[graphTitle[iname]][0])
    p_e = peak_eccentricity((float(buckle_final)-buckle_initial)*.0254,span_Var)
    eal = eccentricity_fail_location(p_e,float(break_dic[graphTitle[iname]][1]),span_Var)
    a_s = axial_stress(load_final*4.44822,cross_sectional_area)
    b_m = bending_moment(load_final*4.4482,eal)
    b_s = bending_stress(outside_radius,b_m,moment_area)
    plfs = (a_s + b_s)/1000000

    property_list = [str(round(mandrel_Diameter,decimal_places)),str(round(laminate_Thickness,decimal_places)),str(span_Var),str(round(break_dic[graphTitle[iname]][1],decimal_places)),
                    str(round(rate_change*0.0254,decimal_places)),str(round(load_final*4.4482,decimal_places)),str(round(outside_radius,decimal_places)),str(round(inside_radius,decimal_places)),str(round(cross_sectional_area,decimal_places)),str('{:.5e}'.format(moment_area)),
                    str(round(p_e,decimal_places)),str(round(eal,decimal_places)),str(round(a_s,5)),str(round(b_m,decimal_places)),str(round(b_s,5)),str(round(plfs,decimal_places))]
   
    #property_list.append(10)
    #print(property_list)

    item_dic[graphTitle[iname]] = property_list

    #property_list.clear()

            #Graph
    fig = plt.figure(figsize=(10,5))

    plt.title(graphTitle[iname])
    plt.ylabel("Load [lbs]")
    plt.xlabel("Crosshead Displacement [in]")
    plt.plot(position,load , label = "Load VS Position")

        #plt.plot(position,slope_m*position, label ='Linear Regression')
        #plt.axline((0,slope_b),slope =slope_m, color='black', label='by slope',linewidth=10)
    plt.plot(slope_data["S:Position (in)"], slope_m*slope_data["S:Position (in)"] + slope_b, color = "black",linewidth = 5) 
    plt.axhline(last_p_value,color= "orange", linestyle="-", label = "Drop Value")
    plt.axvline(buckle_initial,color = 'red', linestyle ='dotted', label = "Initial Intersection")
    plt.axvline(buckle_final,color = 'green', linestyle ='dotted',label = "Final Intersection")
    plt.legend()
    if loadmax < 200:
        plt.ylim(0,200)
        
    else:
        plt.ylim(200,10000)
    plt.xlim(0,max_len+.05)
    plt.tick_params(labelsize = 10)

    #plt.annotate( "Initial Position: " + str(round(buckle_initial,4)) , xy = (.1,-.2), xycoords='axes fraction')
    #plt.annotate( "Final Load:" + str(load_final) + ", Final Position: " + str(round(buckle_final,4)), xy = (.7,-.2), xycoords='axes fraction')

    #plt.annotate( "\u0394Position/\u0394Time (m/sec) = " + str((rate_change)), xy = (.1,-.25), xycoords='axes fraction')
    #plt.annotate( "Temperature(\u00b0F) : " + temperature, xy = (.7,-.25), xycoords='axes fraction')

    #plt.annotate( "Sample Length(mm): " + tube_length, xy = (.1,-.3), xycoords='axes fraction')
   # plt.annotate( "Break from end distance(mm): " + break_end, xy = (.7,-.3), xycoords='axes fraction')
    plt.grid()
    bio = BytesIO()
    fig.savefig(bio, format="png", bbox_inches='tight')
    bytes_list.append(bio)

    #print(bio)



    #or figure in bytes_list:


max_page_width = 270

    # Instantiation of inherited class
pdf = PDF()

    # Calls total page number for footer
pdf.alias_nb_pages()

    # Adds page because there is currently no page
pdf.add_page()

    #Set fonts for pdf
pdf.set_font('helvetica', 'B', 7)
pdf.set_fill_color(225,225,234)
pdf.set_font("Times", size=10)

pdf.create_table(table_data = item_dic,title='Bending Stress Calculations', cell_width='even' , emphasize_data= get_property_names(), emphasize_style='BIU',emphasize_color=(0,0,0))
pdf.ln()
pdf.ln()
pdf.ln()
#pdf.create_table(table_data = data,title='my title is the best title',cell_width='uneven',x_start=25)
#pdf.ln()
#pdf.create_table(table_data = data,title='my title is the best title',cell_width=22,x_start=50) 
#pdf.ln()

#pdf.create_table(table_data = data_as_dict,title='Is my text red',align_header='R', align_data='R', cell_width=[15,15,10,45,], x_start='C', emphasize_data=['45','Jules'], emphasize_style='BIU',emphasize_color=(255,0,0))
#pdf.ln()


#pdf.create_table(table_data = item_dic,align_header='R', align_data='R', cell_width=[15,15,10,45,], x_start='C') 
for index, figure in enumerate(bytes_list):

    pdf.image(name='data://image/png;base64,' + base64.b64encode(figure.getvalue()).decode()  , x =20 , w=170, h=120, type='png')


pdf.output('MT061_Batch_4.pdf')

# Need to create obejct as pdf
print(item_dic)
#pdf.output('table_with_cells.pdf')

#print(item_dic)
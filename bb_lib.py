#import numpy as np
import numpy as np
from fpdf import FPDF
from io import BytesIO
import base64
import math
#import urllib

# ==============================================================
# Given Constants / Calculations
# Below you will find given constants and some calculations that
# are given in the google spreeadsheet thats posted above
# the dictionaries spec_dic/buck_dic are containers filled with
# given data for some samples.
# ==============================================================
# CONSTANTS FOR BENDING
mandrel_Diameter =0.04450                               #m
laminate_Thickness = 0.001120                           #m
#span_Var = 1.686                                        #m
inside_radius = mandrel_Diameter/2                      #m
outside_radius = laminate_Thickness + inside_radius     #m

# Second Moment of Area
moment_area =  (math.pi/ 4*(outside_radius**4 - inside_radius**4))   #m^2                                   

# Cross Sectional Area
cross_sectional_area = math.pi * (outside_radius**2 - inside_radius**2) #m^4


def find_roots(x,y):
    np.seterr(divide = 'ignore')
    s = np.abs(np.diff(np.sign(y))).astype(bool)
    value = x[:-1][s] + np.diff(x)[s]/(np.abs(y[1:][s]/y[:-1][s])+1)
    np.seterr(divide = 'warn') 
    return value
    
def find_nearest(array, value):
    #array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


# FORMULAS/EQUATIONS
"""
Formulas and constants can be found in this excel spreadsheet made by Dan Foster
MT061 - CFRP Buckling Post-Hoop Damage 
(Under buckling strees calcs tab)
https://docs.google.com/spreadsheets/d/1E_udTrTWaQ_PSnOER0Ssk3IjKFw-yfmca2awrDQ3A14/edit#gid=1005744455
"""
def peak_eccentricity(displacement,span):  
    return float((2*math.sqrt(displacement*span))/math.pi)

def eccentricity_fail_location(peak_e,fail_loc,span):
    return peak_e*math.sin((math.pi*fail_loc)/span)

def axial_stress(load_at_fail,cs_area):
    return load_at_fail/cs_area

def bending_moment(load_at_fail,eccent_at_fail):
    return load_at_fail*eccent_at_fail

def bending_stress(outside_radius,bending_moment,second_mnt_are):
    return ((bending_moment*outside_radius)/second_mnt_are)

# ==============================================================
# Set up FPDF class
# ==============================================================
# BEGIN Dictionary Value Adder
class PDF(FPDF):
    def header(self):
        # Logo
        #self.image('LtaLogo.png', 10, 8, 33)
        # Arial bold 15
        self.set_font('helvetica', 'B', 20)
        # Move to the right
        self.cell(80)
        
        # Title - Insert tittle in the code below.
        self.cell(40, 10, "MT061R&D Tube Characterization - Report", 0, 0, 'C')
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def load_resource(self, reason, filename):
        if reason == "image":
            if filename.startswith("http://") or filename.startswith("https://"):
                f = BytesIO(urlopen(filename).read())
            elif filename.startswith("data"):
                f = filename.split('base64,')[1]
                f = base64.b64decode(f)
                f = io.BytesIO(f)
            else:
                f = open(filename, "rb")
            return f
        else:
            self.error("Unknown resource loading reason \"%s\"" % reason)


    def create_table(self, table_data, title='', data_size = 10, title_size=12, align_data='L', align_header='L', cell_width='even', x_start='x_default',emphasize_data=[], emphasize_style=None,emphasize_color=(0,0,0)): 
        """
        table_data: 
                    list of lists with first element being list of headers
        title: 
                    (Optional) title of table (optional)
        data_size: 
                    the font size of table data
        title_size: 
                    the font size fo the title of the table
        align_data: 
                    align table data
                    L = left align
                    C = center align
                    R = right align
        align_header: 
                    align table data
                    L = left align
                    C = center align
                    R = right align
        cell_width: 
                    even: evenly distribute cell/column width
                    uneven: base cell size on lenght of cell/column items
                    int: int value for width of each cell/column
                    list of ints: list equal to number of columns with the widht of each cell / column
        x_start: 
                    where the left edge of table should start
        emphasize_data:  
                    which data elements are to be emphasized - pass as list 
                    emphasize_style: the font style you want emphaized data to take
                    emphasize_color: emphasize color (if other than black) 
        
        """
        default_style = self.font_style
        if emphasize_style == None:
            emphasize_style = default_style
        # default_font = self.font_family
        # default_size = self.font_size_pt
        # default_style = self.font_style
        # default_color = self.color # This does not work

        # Get Width of Columns
        def get_col_widths():
            col_width = cell_width
            if col_width == 'even':
                col_width = self.epw / len(data[0]) - 1  # distribute content evenly   # epw = effective page width (width of page not including margins)
            elif col_width == 'uneven':
                col_widths = []

                # searching through columns for largest sized cell (not rows but cols)
                for col in range(len(table_data[0])): # for every row
                    longest = 0 
                    for row in range(len(table_data)):
                        cell_value = str(table_data[row][col])
                        value_length = self.get_string_width(cell_value)
                        if value_length > longest:
                            longest = value_length
                    col_widths.append(longest + 4) # add 4 for padding
                col_width = col_widths



                        ### compare columns 

            elif isinstance(cell_width, list):
                col_width = cell_width  # TODO: convert all items in list to int        
            else:
                # TODO: Add try catch
                col_width = int(col_width)
            return col_width

        # Convert dict to lol
        # Why? because i built it with lol first and added dict func after
        # Is there performance differences?
        if isinstance(table_data, dict):
            header = [key for key in table_data]
            data = []
            for key in table_data:
                value = table_data[key]
                data.append(value)
            # need to zip so data is in correct format (first, second, third --> not first, first, first)
            data = [list(a) for a in zip(*data)]

        else:
            header = table_data[0]
            data = table_data[1:]

        line_height = self.font_size * 2.5

        col_width = get_col_widths()
        self.set_font(size=title_size)

        # Get starting position of x
        # Determin width of table to get x starting point for centred table
        if x_start == 'C':
            table_width = 0
            if isinstance(col_width, list):
                for width in col_width:
                    table_width += width
            else: # need to multiply cell width by number of cells to get table width 
                table_width = col_width * len(table_data[0])
            # Get x start by subtracting table width from pdf width and divide by 2 (margins)
            margin_width = self.w - table_width
            # TODO: Check if table_width is larger than pdf width

            center_table = margin_width / 2 # only want width of left margin not both
            x_start = center_table
            self.set_x(x_start)
        elif isinstance(x_start, int):
            self.set_x(x_start)
        elif x_start == 'x_default':
            x_start = self.set_x(self.l_margin)


        # TABLE CREATION #

        # add title
        if title != '':
            self.multi_cell(0, line_height, title, border=0, align='j', ln=3, max_line_height=self.font_size)
            self.ln(line_height) # move cursor back to the left margin

        self.set_font(size=data_size)
        # add header
        y1 = self.get_y()
        if x_start:
            x_left = x_start
        else:
            x_left = self.get_x()
        x_right = self.epw + x_left
        if  not isinstance(col_width, list):
            if x_start:
                self.set_x(x_start)
            for datum in header:
                self.multi_cell(col_width, line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                x_right = self.get_x()
            self.ln(line_height) # move cursor back to the left margin
            y2 = self.get_y()
            self.line(x_left,y1,x_right,y1)
            self.line(x_left,y2,x_right,y2)

            for row in data:
                if x_start: # not sure if I need this
                    self.set_x(x_start)
                for datum in row:
                    if datum in emphasize_data:
                        self.set_text_color(*emphasize_color)
                        self.set_font(style=emphasize_style)
                        self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                        self.set_text_color(0,0,0)
                        self.set_font(style=default_style)
                    else:
                        self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                self.ln(line_height) # move cursor back to the left margin
        
        else:
            if x_start:
                self.set_x(x_start)
            for i in range(len(header)):
                datum = header[i]
                self.multi_cell(col_width[i], line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                x_right = self.get_x()
            self.ln(line_height) # move cursor back to the left margin
            y2 = self.get_y()
            self.line(x_left,y1,x_right,y1)
            self.line(x_left,y2,x_right,y2)


            for i in range(len(data)):
                if x_start:
                    self.set_x(x_start)
                row = data[i]
                for i in range(len(row)):
                    datum = row[i]
                    if not isinstance(datum, str):
                        datum = str(datum)
                    adjusted_col_width = col_width[i]
                    if datum in emphasize_data:
                        self.set_text_color(*emphasize_color)
                        self.set_font(style=emphasize_style)
                        self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                        self.set_text_color(0,0,0)
                        self.set_font(style=default_style)
                    else:
                        self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                self.ln(line_height) # move cursor back to the left margin
        y3 = self.get_y()
        self.line(x_left,y3,x_right,y3)

def get_property_names():
    return ["Mandrel Diameter[m]",
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
                        "Peak Laminate Failure Stress[Mpa]"]


#Break from END LIST 
break_dic = {
                #KEY : [ VA1 , VAL2]
                #Sample : [ span , brek from end ] all values converted from mm to m
                "KF021810":[1.8,0.89],
                "KF021821":[1.8,0.95],
                "KF021854":[1.799,0.915],
                "KF021855":[1.798,0.915],
                "KF021860":[1.799,0.9],
                "KF021861":[1.8,0.86],
                "KF021868":[1.8,0.95],
                "KF021870":[1.8,0.95],
                "KF021885":[1.8,1],
                "KF021887":[1.798,0.875],
                "KF021889":[1.8,0.905],
                "KF021890":[1.798,0.85],
                "KF021915":[1.799,0.915],
                "KF021923":[1.799,0.895],
                "KF021925":[1.797,0.905],
                "KF021927":[1.799,0.885],
                "KF021932":[1.799,0.875],
                "KF021943":[1.798,0.905],
                "KF021944":[1.798,0.876],
                "KF021947":[1.8,1.01],
                "KF021959":[1.799,0.91],
                "KF022016":[1.798,0.915],
                "KF022048":[1.8,0.88],
                "KF022049":[1.8,0.895],
                "KF022083":[1.798,0.905]

}
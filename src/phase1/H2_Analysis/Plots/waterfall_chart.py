'''
A function that attempts to generate a standard waterfall chart in generic Python. Requires two sequences,
one of labels and one of values, ordered accordingly.
'''


from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as lines

#==============================================================================
# Change data below
#==============================================================================

index = ['LCOH','Electrolyzer \n system cost','Pipe vs cable','Shared power \n electronics','Labor savings','Policy']
data = [2.1,0.13,-0.2,-0.05,-0.1,-1.5]

font = 'Arial'
title_size = 20
axis_label_size = 16
legend_size = 14
tick_size = 10
tickfontsize = 16
resolution = 200

Title=""
x_lab="Category"
y_lab="Levelized cost of hydrogen ($/kg)"
formatting = "{:,.1f}"
first_color='navy'
second_color='orange'
third_color='teal'
sorted_value = False
threshold=None
other_label='other'
net_label='Net'
rotation_value = 30
blank_color=(0,0,0,0)
figsize = (9,6)
#convert data and index to np.array
index=np.array(index)
data=np.array(data)

#sorted by absolute value 
if sorted_value: 
    abs_data = abs(data)
    data_order = np.argsort(abs_data)[::-1]
    data = data[data_order]
    index = index[data_order]

#group contributors less than the threshold into 'other' 
if threshold:
    
    abs_data = abs(data)
    threshold_v = abs_data.max()*threshold
    
    if threshold_v > abs_data.min():
        index = np.append(index[abs_data>=threshold_v],other_label)
        data = np.append(data[abs_data>=threshold_v],sum(data[abs_data<threshold_v]))

changes = {'amount' : data}

#define format formatter
def money(x, pos):
    'The two args are the value and tick position'
    return formatting.format(x)
formatter = FuncFormatter(money)

fig, ax = plt.subplots(figsize=figsize)
ax.yaxis.set_major_formatter(formatter)

#Store data and create a blank series to use for the waterfall
trans = pd.DataFrame(data=changes,index=index)
blank = trans.amount.cumsum().shift(1).fillna(0)

trans['positive'] = trans['amount'] > 0

#Get the net total number for the final element in the waterfall
total = trans.sum().amount
trans.loc[net_label]= total
blank.loc[net_label] = total

#The steps graphically show the levels as well as used for label placement
step = blank.reset_index(drop=True).repeat(3).shift(-1)
step[1::3] = np.nan

#When plotting the last element, we want to show the full bar,
#Set the blank to 0
blank.loc[net_label] = 0

#define bar colors for net bar
trans.loc[trans['positive'] > 1, 'positive'] = 99
trans.loc[trans['positive'] < 0, 'positive'] = 99
trans.loc[(trans['positive'] > 0) & (trans['positive'] < 1), 'positive'] = 99

trans['color'] = trans['positive']

trans.loc[trans['positive'] == 1, 'color'] = first_color
trans.loc[trans['positive'] == 0, 'color'] = second_color
trans.loc[trans['positive'] == 99, 'color'] = third_color

my_colors = list(trans.color)

#Plot and label
my_plot = plt.bar(range(0,len(trans.index)), blank, width=0.5, color=blank_color)
plt.bar(range(0,len(trans.index)), trans.amount, width=0.6,
         bottom=blank, color=my_colors)   
# ymin = 0
# ymax = np.max(data) 
# ax.set_ylim([ymin,ymax])                             

# connecting lines - figure out later
#my_plot = lines.Line2D(step.index, step.values, color = "gray")
#my_plot = lines.Line2D((3,3), (4,4))

#axis labels
plt.xlabel("\n" + x_lab,fontsize=12)
plt.ylabel(y_lab + "\n",fontsize=12)

#Get the y-axis position for the labels
y_height = trans.amount.cumsum().shift(1).fillna(0)

temp = list(trans.amount)

# create dynamic chart range
for i in range(len(temp)):
    if (i > 0) & (i < (len(temp) - 1)):
        temp[i] = temp[i] + temp[i-1]

trans['temp'] = temp
        
plot_max = trans['temp'].max()
plot_min = trans['temp'].min()

#Make sure the plot doesn't accidentally focus only on the changes in the data
if all(i >= 0 for i in temp):
    plot_min = 0
if all(i < 0 for i in temp):
    plot_max = 0

if abs(plot_max) >= abs(plot_min):
    maxmax = abs(plot_max)   
else:
    maxmax = abs(plot_min)
    
pos_offset = maxmax / 40

plot_offset = maxmax / 15 ## needs to be cumulative sum dynamic

#Start label loop
loop = 0
for index, row in trans.iterrows():
    # For the last item in the list, we don't want to double count
    if row['amount'] == total:
        y = y_height[loop]
    else:
        y = y_height[loop] + row['amount']
    # Determine if we want a neg or pos offset
    if row['amount'] > 0:
        y += (pos_offset*2)
        plt.annotate(formatting.format(row['amount']),(loop,y),ha="center", color = 'black', fontsize=10)
    else:
        y -= (pos_offset*4)
        plt.annotate(formatting.format(row['amount']),(loop,y),ha="center", color = 'black', fontsize=10)
    loop+=1

#Scale up the y axis so there is room for the labels
plt.ylim(plot_min-round(3.6*plot_offset, 7),plot_max+round(3.6*plot_offset, 7))

#Rotate the labels
plt.xticks(range(0,len(trans)), trans.index, rotation=rotation_value)

#add zero line and title
plt.axhline(0, color='black', linewidth = 0.6, linestyle="dashed")
plt.title(Title)
plt.tight_layout()


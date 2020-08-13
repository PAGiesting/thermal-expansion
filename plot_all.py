# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import matplotlib.pyplot as plt
import pandas as pd
import os
import re
# %%
_, __, files = next(os.walk('data'))
cols=['Sample','Orientation','Run','Filetype']
namedf = pd.DataFrame(columns=cols)
files = list(filter(lambda s: s.endswith('csv'),files))
findletters = re.compile('[a-zA-Z]+')
finddigits = re.compile('\d+')
# %%
for filename in files:
    pieces = filename.split('.')
    dline = {}
    # collect 'c' or 'x' character from end of last piece before extension
    dline['Filetype'] = pieces[-2][-1]
    stems = pieces[0].split('-')
    dline['Sample'] = findletters.findall(stems[0])[0]
    dline['Orientation'] = finddigits.findall(stems[0])[0]
    prelength = len(dline['Sample'])+len(dline['Orientation'])
    dline['Run'] = stems[0][prelength:]
    newline = pd.DataFrame(dline,columns=cols,index=[0])
    namedf = namedf.append(newline,ignore_index=True)
# %%
namedf.sort_values(cols,ascending=[True,False,True,True],inplace=True)
def namegrab(text1,text2,text3,df,filelist):
    """Finds the filename in a list that matches text1 and text2
    in columns 1-3 of the dataframe and has the lower value
    for column 4 because we trust csvs more than workbooks."""
    text4 = df[(df.iloc[:,0]==text1)&(df.iloc[:,1]==text2)&(df.iloc[:,2]==text3)].iloc[:,3].min()
    for name in filelist:
        if (text1 in name)&(str(text2) in name)&(str(text3) in name)&(text4 in name):
            return name
    return None
# %%
plotdict = {}
samples = namedf['Sample'].unique()
for sample in samples:
    plotdict[sample]={}
    or_list = list(namedf[namedf['Sample']==sample].Orientation.unique())
    for orient in or_list:
        plotdict[sample][orient]={}
        run_list = list(namedf[(namedf['Sample']==sample)&
            (namedf['Orientation']==orient)].Run.unique())
        for run in run_list:
            plotdict[sample][orient][run]=namegrab(sample,orient,run,namedf,files)
# %%
for sample in plotdict:
    orients = list(plotdict[sample].keys())
    if '100' in orients:
        orients.remove('100')
        for run in plotdict[sample]['100'].keys():
            df100 = pd.read_csv('data/'+plotdict[sample]['100'][run])
            plt.plot(df100.iloc[:,1],df100['Alpha'],lw=2,c='r',label='100 '+run)
    if '010' in orients:
        orients.remove('010')
        for run in plotdict[sample]['010'].keys():
            df010 = pd.read_csv('data/'+plotdict[sample]['010'][run])
            plt.plot(df100.iloc[:,1],df100['Alpha'],lw=2,c='g',label='010 '+run)
    if '001' in orients:
        orients.remove('001')
        for run in plotdict[sample]['001'].keys():
            df001 = pd.read_csv('data/'+plotdict[sample]['001'][run])
            plt.plot(df001.iloc[:,1],df001['Alpha'],lw=2,c='b',label='001 '+run)
    if len(orients) > 0:
        for orient in orients:
            for run in plotdict[sample][orient].keys():
                df000 = pd.read_csv('data/'+plotdict[sample][orient][run])
                plt.plot(df000.iloc[:,1],df000['Alpha'],lw=2,c='black',label=orient+' '+run)
    plt.title(sample)
    plt.xlabel('Temp (Celsius)')
    plt.ylabel('Linear Thermal Exp.')
    plt.legend()
    plt.savefig('testplots/'+sample+'.tif')
    plt.show()
    plt.clf()
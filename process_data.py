#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 09:04:03 2022

@author: yifan
"""

################################
# ---- Clean poverty status data
################################

# import packages
import pandas as pd
import numpy as np

# load data
df = pd.read_csv('raw_data/Poverty Status in the past 12 months.csv', delimiter=',')

# remove strings before converting to numbers
def remove_str(x):
    if type(x) == str:
        x = x.replace('%','').replace(',','').replace('±','').replace('N', 'NaN').replace('(X)','NaN').replace('-', 'NaN').replace('**', 'NaN')
    return x
df.iloc[:, 1:] = df.iloc[:, 1:].applymap(remove_str)

# convert to numeric data type
df = pd.concat([df.iloc[:, 0], df.iloc[:, 1:].astype(float)], axis=1)

# need to make sure rows have unique names
df.iloc[33:35, 0] = 'Employed ' + df.iloc[33:35, 0].str.strip()
df.iloc[36:38, 0] = 'Unemployed ' + df.iloc[36:38, 0].str.strip()

# ---- Tidy dataset

# first, transpose df
# set_index ensures proper column header after transpose
# reset_index frees first column by setting an additional index
# rename_axis removes the remaining column name "Lable (Grouping)"
df_split = df.set_index('Label (Grouping)').T.reset_index().rename_axis(None, axis=1)

# split column, remove prefix
df_split[['Zipcode', 'Metrics', 'Stats']] = df_split['index'].str.split('!!', expand = True)
df_split['Zipcode'] = df_split['Zipcode'].map(lambda x: x.lstrip('ZCTA5 '))

# remove the index column after transpose
df_split.drop('index', axis=1, inplace=True)

# get df_related by slicing df_split
df_related = pd.concat([df_split.iloc[:,68:71], df_split.iloc[:, 0:52]], axis=1)

# get df_unrelated by slicing df_split
df_unrelated = pd.concat([df_split.iloc[:,68:71], df_split.iloc[:, 52:68]], axis=1)


# ---- Separate tables

# get a list of var names for demographic variables
demo_vars = [x.strip() for x in df_related.columns[df_related.isna().all()].values]
# note that EMP contains 2 layers so won't include it in the batch

# get column names to unpivot (including EMP block)
col_start = [5, 15, 18, 28, 34, 42, 47]
col_end = [14, 17, 27, 33, 41, 46, 55]

to_unpivot = []
for i in range(len(col_start)):
    to_unpivot.append(df_related.columns[col_start[i]:col_end[i]].tolist())
    
# create multiple dfs for unpivotted results
id_cols = ['Zipcode', 'Metrics', 'Stats']

df_demo = {}
for i in range(len(col_start)):
        tmp = df_related.melt(id_vars=id_cols, value_vars=to_unpivot[i], var_name=demo_vars[i])
        # strip white space for easy reference later on
        tmp[demo_vars[i]] = tmp[demo_vars[i]].map(lambda x: x.lstrip())
        # metrics needs to be on the column to allow selection of the same zipcodes with differnet metrics
        df_demo[demo_vars[i]] = tmp.pivot(index=['Zipcode', 'Stats', demo_vars[i]], columns='Metrics', values='value').reset_index().rename_axis(None, axis=1)
    
    # add a population df
df_demo['POPULATION'] = df_related[df_related.columns[0:4]].pivot(index=['Zipcode', 'Stats'], columns='Metrics', values='Population for whom poverty status is determined').reset_index().rename_axis(None, axis=1)



# ---- Write dfs to csv

# write all dfs to folder
for key in df_demo.keys():
    df_demo[key].to_csv(f'processed_data/poverty_{key}.csv')
    
    
################################
# ---- Clean demographic data
################################    
    
# load demographics data
df2 = pd.read_csv('raw_data/ACSDP5Y2020.DP05-2022-06-11T184811.csv', delimiter=',')

# remove strings before converting to numbers
def remove_str(x):
    if type(x) == str:
        x = x.replace('%','').replace(',','').replace('±','').replace('N', 'NaN').replace('(X)','NaN').replace('-', 'NaN').replace('*****', 'NaN').replace('**', 'NaN')
    return x
df2.iloc[:, 1:] = df2.iloc[:, 1:].applymap(remove_str)

# convert to numeric data type
df2 = pd.concat([df2.iloc[:, 0], df2.iloc[:, 1:].astype(float)], axis=1)

    

# ---- Gender table    
    
# select gender rows
df2_gender = df2.iloc[[2,3], :]

# transpose
df2_gender = df2_gender.set_index('Label (Grouping)').T.reset_index().rename_axis(None, axis=1)

# split column, remove prefix, and check
df2_gender[['Zipcode', 'Metrics']] = df2_gender['index'].str.split('!!', expand = True)
df2_gender['Zipcode'] = df2_gender['Zipcode'].map(lambda x: x.lstrip('ZCTA5 '))

# select relevant rows and columns
df2_gender = df2_gender[df2_gender['Metrics'] == 'Estimate'].drop(['index', 'Metrics'], axis=1)

# remove row about the state
df2_gender = df2_gender.loc[df2_gender['Zipcode'] != 'Illinois', :]

# remove white space in column names
df2_gender = df2_gender.rename(columns=lambda x: x.lstrip())
df2_gender.columns.values

# pivot
df2_gender = df2_gender.melt(id_vars='Zipcode', var_name='Gender', value_vars=['Male', 'Female'],value_name='Estimate')




# ---- Age table    

# select age rows
df2_age = df2.iloc[np.r_[5:18], :]

# transpose
df2_age = df2_age.set_index('Label (Grouping)').T.reset_index().rename_axis(None, axis=1)

# split column, remove prefix, and check
df2_age[['Zipcode', 'Metrics']] = df2_age['index'].str.split('!!', expand = True)
df2_age['Zipcode'] = df2_age['Zipcode'].map(lambda x: x.lstrip('ZCTA5 '))

# select relevant rows and columns
df2_age = df2_age[df2_age['Metrics'] == 'Estimate'].drop(['index', 'Metrics'], axis=1)

# remove row about the state
df2_age = df2_age.loc[df2_age['Zipcode'] != 'Illinois', :]

# remove white space in column names
df2_age = df2_age.rename(columns=lambda x: x.lstrip())

# pivot
df2_age = df2_age.melt(id_vars='Zipcode', var_name='Age group', value_name='Estimate')

    


# ---- Race table

# select race rows
df2_race = df2.iloc[np.r_[66:72], :]

# transpose
df2_race = df2_race.set_index('Label (Grouping)').T.reset_index().rename_axis(None, axis=1)

# split column, remove prefix, and check
df2_race[['Zipcode', 'Metrics']] = df2_race['index'].str.split('!!', expand = True)
df2_race['Zipcode'] = df2_race['Zipcode'].map(lambda x: x.lstrip('ZCTA5 '))

# select relevant rows and columns
df2_race = df2_race[df2_race['Metrics'] == 'Estimate'].drop(['index', 'Metrics'], axis=1)

# remove row about the state
df2_race = df2_race.loc[df2_race['Zipcode'] != 'Illinois', :]

# remove white space in column names
df2_race = df2_race.rename(columns=lambda x: x.lstrip())

# pivot
df2_race = df2_race.melt(id_vars='Zipcode', var_name='Race group', value_name='Estimate')    



# ---- Write dfs to csv

# write all dfs to folder
df2_age.to_csv('processed_data/demo_age.csv', index=False)
df2_gender.to_csv('processed_data/demo_gender.csv', index=False)
df2_race.to_csv('processed_data/demo_race.csv', index=False)

    
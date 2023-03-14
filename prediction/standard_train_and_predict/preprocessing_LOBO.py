import os
import numpy as np


# 'IRL-JB',
#files_path = ['IRL-FP', 'IRL-VB', 'IRL-SB', 'IRL-JB', 'IRL-SLE',  'SLE-ME', 'SLE-NF', 'SLE-SF', 'SLE-SF2']



months_len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

leap_years = [2008, 2012, 2016, 2020]

# define global variables
hour = 0
incremental_hour = 0
day = 0
incremental_day = 0
month = 0
incremental_month = 0
year = 0
incremental_year = 0
averages = []
monthly_averages = []
daily_averages_flag = False
p = np.pi/12
daytime_map = [np.cos(i*p) for i in range(24)]

three_lines = 0
miss_data = 0

def rain_to_weather(rain):
    if rain == 0:
        weather = 0
    elif rain > 0 and rain <= 0.098:
        weather = 0.25
    elif rain > 0.098 and rain <= 0.30:
        weather = 0.50
    elif rain > 0.39:
        weather = 0.75
    return weather


# experiment_2/IRL-JB.tsv
def preprocessing(datapath):
    global daily_averages_flag
    global hour
    global incremental_hour
    global day
    global incremental_day
    global month
    global incremental_month
    global year
    global incremental_year
    global averages
    global three_lines
    global months_len
    global addTime
    global farmer_interval
    global daytime_map
    global miss_data

    f = []
    f1 = open(datapath, 'r')
    first_line = True
    incremental_day = 1
    incremental_hour = -1
    
    
    for line_it in f1:

        # skip first three lines
        if three_lines < 3:
            three_lines += 1
            continue

        line = line_it.split('\t')
        # l[0] = l[0][8:13]
        line[-1] = line[-1].replace('\n', '')

        year = int(line[0][0:4])
        month = int(line[0][5:7])
        day = int(line[0][8:10])
        hour = int(line[0][11:13])

        # the line should have round hours,
        if line[0][14:16] != '00':
            continue

        if first_line:

            print("open a new file")
            incremental_hour = hour
            incremental_day = day
            incremental_month = month
            incremental_year = year
            # chlorophyll | dissolved oxygen | pH | salinity | temperature |
            # barometric pressure | rain | wind direction |
            print(line)
            #averages = [[float(line[1]), float(line[2]), float(line[3]), 
            #             float(line[4]), float(line[5]), float(line[6]),
            #             float(line[7]), float(line[8])]]  # only DO
            
            #averages = [[float(line[1]), float(line[2]), float(line[3]), float(hour)]]  # for adding time
            if addTime:
                averages = [[float(line[1]), float(line[2]), rain_to_weather(float(line[3])), 
                             float(line[6]),  float(hour)]]
                # no float(line[4]), solar rad and float(line[5]) , wind direction
                
                # float(daytime_map[int(hour)])
            else:
                averages = [[float(line[1]), float(line[2]), rain_to_weather(float(line[3])), float(line[4]),
                         float(line[5]), float(line[6])]]
            
            first_line = False
        else:
            do_increments()
            if addTime:
                do_averages_with_time_no_fill(line, 1)
            else:
                do_averages_with_time_no_fill(line, 1)  # 1 means no average

        # have to do a function to check which data are complete, if some are missing, fill it with moving average

        if same_hour():
            f.append(line[1])
        else:
            
            if same_day():
                missing_hours = hour - incremental_hour
                # eg data until 16:00 (included) and gap until 19:00 (included) ,
                # incremental_hour = 17, missing_hours = 2, add data for 17,
                # range: 0 -> 18, 1 -> 19

            elif same_month():

                missing_days = day - incremental_day
                missing_hours = from_days_to_hours(missing_days)

            elif same_year():
                days_in_month = months_len[incremental_month - 1] - incremental_day
                days_between = 0
                days_fin_month = day
                if month - incremental_month > 1:
                    print("an entire month missing")
                    months_list = [*range(incremental_month + 1, month)]
                    for m in months_list:
                        days_between += months_len(m)

                missing_days = days_in_month + days_between + days_fin_month
                missing_hours = from_days_to_hours(missing_days)
                print("diff months")

            else:
                if year - incremental_year == 1:
                    days_in_month = months_len[incremental_month - 1] - incremental_day
                    days_fin_month = day
                    days_between = 0
                    if incremental_month < 12:
                        months_list_1 = [*range(incremental_month + 1, 12)]
                        for m in months_list_1:
                            days_between += months_list_1(m)
                    if month > 1:
                        months_lis_2 = [*range(1, month)]
                        for m in months_lis_2:
                            days_between += months_lis_2(m)

                    missing_days = days_in_month + days_between + days_fin_month
                    missing_hours = from_days_to_hours(missing_days)

                else:
                    print("AN ENTIRE YEAR IS MISSING")

            f.append(line[1:9])
            for i in range(missing_hours):
                print('data are missing, month, day,hour', incremental_month, incremental_day, incremental_hour)
                miss_data += 1
                do_increments()
                #if addTime:
                    #do_averages_with_time_no_fill(line, 1)
                #else:
                    #do_averages_with_time_fill(line, 1)
                    #print('no')
                
                #f.append(line[1:9])

    three_lines = 0
    print("avg shape", np.asarray(averages).shape)
    print("f shape", np.asarray(f).shape)

    # return np.asarray(f)
    if daily_averages_flag:
        return np.asarray(monthly_averages)
    
    if addTime and farmer_interval:
        uneven_avg = sample_time(averages)
        print(' uneven data shape', np.array(uneven_avg).shape)
        return np.array(uneven_avg).astype(float)
    
    #print(averages)
    print('missing data', miss_data)
    
    return np.asarray(averages).astype(float)



def do_averages_with_time_no_fill(line, alfa):

    global incremental_hour
    global averages
    global month
    global day
    global hour
    global daytime_map
    global miss_data
    
    '''
    [[float(line[1]), float(line[2]), rain_to_weather(float(line[3])), 
                             float(line[6]),  float(hour)]]
    '''
    
    complete_line = True
    new_avg = []
    for index, avg in enumerate(averages[-1]):
       # print(averages[-1])
        if index != (len(averages[-1]) -1):
                if line[index + 1] != '' :  # and added for adding time
                        #new_avg.append(avg * (1 - alfa) + alfa * float(line[index + 1]))
                        if index == 2:
                            new_avg.append(rain_to_weather(float(line[index+1])))
                        elif index == 3:
                            new_avg.append(float(line[6]))
                        else:
                            new_avg.append(float(line[index + 1]))
                else:
                    complete_line = False
                    new_avg.append(avg)
         
        else:         
            new_avg.append(float(incremental_hour))
            # daytime_map[int(incremental_hour)]

    if complete_line:
        averages.append(new_avg)
    else:
        print('part of data missing', month, day, hour)
        miss_data += 1
        
    
    return averages


def do_averages_with_time_fill(line, alfa):
    global incremental_hour
    global averages

    new_avg = []
    for index, avg in enumerate(averages[-1]):
       # print(averages[-1])
        if index != (len(averages[-1]) -1):
            if line[index + 1] != '' :  # and added for adding time
                    new_avg.append(avg * (1 - alfa) + alfa * float(line[index + 1]))
            else:
                new_avg.append(avg)
         
        else:
            new_avg.append(float(incremental_hour))

    averages.append(new_avg)
    return averages


def do_increments():
    global hour
    global incremental_hour
    global day
    global incremental_day
    global month
    global incremental_month
    global year
    global incremental_year
    global months_len
    global averages
    global monthly_averages
    global daily_averages_flag

    incremental_hour += 1

    if incremental_hour == 24:
        incremental_hour = 0
        incremental_day += 1
        
        if daily_averages_flag:
            avg = np.array(averages).astype(float)
            monthly_averages.append([avg[:,i].sum()/avg.shape[0] for i in range(avg.shape[1])])
            # print("fine mese")
            averages = [averages[-1]] # reset averages

    if incremental_day == months_len[incremental_month - 1] + 1:
        incremental_day = 1
        incremental_month += 1
        
        

    if incremental_month == 13:
        incremental_month = 1
        incremental_year += 1
        if incremental_year in leap_years:
            months_len[1] = 29
        else:
            months_len[1] = 28

        print("fine anno")

    # print("hour", hour, incremental_hour)
    # print("day", day, incremental_day)
    # print("month", month, incremental_month)
    # print("year", year, incremental_year)


def from_days_to_hours(missing_days):
    # eg data until 1 at 16:00 and gap until 4 at 12:00
    # incremental hour = 17, incremental day = 1, missing_days = 3
    if incremental_hour <= hour:
        missing_hours = missing_days * 24 + hour - incremental_hour
    else:
        missing_days -= 1
        missing_hours = missing_days * 24 + (24 - incremental_hour) + hour

    return missing_hours


def same_hour():
    if hour == incremental_hour and day == incremental_day and month == incremental_month and year == incremental_year:
        return True


def same_day():
    if day == incremental_day and month == incremental_month and year == incremental_year:
        return True


def same_month():
    if month == incremental_month and year == incremental_year:
        return True


def same_year():
    if year == incremental_year:
        return True


def sample_time(averages):
    uneven_avg = []
    hours = [16, 21, 23, 1, 3, 5]
    for avg_line in averages:
        if int(avg_line[-1]) in hours:
            uneven_avg.append(avg_line)
            
    return uneven_avg

addTime = True
daily_averages_flag = False  # Means that I want average for each months
farmer_interval = False

def preprocess_lobo(site_number):
    global addTime
    global daily_averages_flag
    global farmer_interval
    # total_data = preprocessing('exp_3_all_Jan_Sept_2018/SLE-ME.tsv')
    
    files_path = ['SLE-NF', 'IRL-SLE', 'IRL-JB', 'SLE-SF', 'SLE-SF2']
    file_path = files_path[site_number] + '.tsv'
    
    #file_folder = '../data/lobo_summer_2018/short/'
    file_folder = '../Data/lobo/'
    #file_folder = '../data/lobo_summer_2018/long_holed/'
    total_data = preprocessing( file_folder + file_path)
    
    return total_data.astype(float)


#total_data = np.expand_dims(total_data, axis=0)
#print(total_data)
#total_data = total_data.astype(float)


#print(total_data.shape)
#np.savetxt('data/lobo_site' + files_path[site_number] + '_short.csv', total_data, delimiter=' ')
#p1 = np.genfromtxt(os.path.join('data/lobo_site' + files_path[site_number] + '_short.csv'))
#print(p1.shape)





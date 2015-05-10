
import matplotlib.pyplot as plt
import numpy as np
import math

def diff_serie(data):
    return [(float(x2) / float(x1) - 1.0) * 100 for (x2, x1) in zip(data[1:], data[:-1])]

def average_change(data):
    return sum(diff_serie(data)) / (len(data) - 1)

def prediction(data, years):
    return data + [pow(1.0 + average_change(data) / 100.0, y) * data[-1] for y in range(1, years)]

def doubling_time(data):
    return math.log(2, 1 + average_change(data) / 100.0)

#1965-
production_tonnes = [1567.9, 1702.3, 1826.6, 1992.8, 2143.4, 2358.0, 2496.2, 2640.6, 2871.3, 2879.4, 2738.2, 2972.9, 3077.1, 3106.8, 3237.3, 3091.9, 2913.9, 2799.7, 2763.0, 2818.7, 2796.8, 2941.6, 2952.5, 3074.7, 3108.6, 3175.4, 3165.7, 3195.3, 3194.5, 3244.0, 3286.1, 3384.2, 3485.9, 3550.8, 3486.9, 3620.4, 3620.3, 3604.5, 3737.5, 3909.6, 3947.5, 3968.7, 3955.3, 3993.2, 3890.9, 3979.3, 4010.6, 4117.4, 4130.2]
consumption_tonnes = [1529.7, 1645.4, 1763.7, 1914.3, 2079.0, 2257.2, 2379.8, 2563.4, 2763.6, 2724.0, 2692.6, 2867.9, 2966.8, 3047.7, 3097.6, 2975.3, 2867.6, 2777.2, 2754.4, 2815.0, 2817.0, 2900.6, 2956.3, 3056.3, 3108.9, 3162.5, 3161.6, 3215.3, 3185.8, 3251.5, 3293.4, 3368.4, 3457.3, 3480.5, 3548.9, 3583.7, 3610.9, 3641.3, 3725.2, 3869.1, 3919.3, 3959.3, 4018.4, 4000.2, 3924.6, 4040.2, 4085.1, 4138.9, 4185.1]
#thousand of barrels daily
production_barrels = [31798, 34563, 37113, 40430, 43627, 48056, 50839, 53662, 58460, 58613, 55822, 60410, 62716, 63338, 66061, 62959, 59547, 57312, 56615, 57696, 57459, 60435, 60745, 63111, 64002, 65385, 65204, 65716, 65978, 67073, 67990, 69845, 72101, 73457, 72293, 74983, 75213, 74991, 77639, 81054, 82107, 82593, 82383, 82955, 81262, 83296, 84049, 86204, 86754]
consumption_barrels = [30811, 33158, 35541, 38455, 41825, 45355, 47880, 51427, 55563, 54792, 54329, 57693, 59889, 62741, 63879, 61244, 59399, 57814, 57591, 58865, 59249, 60995, 62293, 64247, 65578, 66761, 66908, 67972, 67677, 69204, 70364, 71853, 74044, 74577, 76269, 76902, 77607, 78499, 80216, 83055, 84389, 85325, 86754, 86147, 85111, 87801, 88934, 89931, 91331]

production_barrels = [x * 365 for x in production_barrels]
consumption_barrels = [x * 365 for x in consumption_barrels]

energy_consumption = [8796, 8853, 8864, 8956, 9033, 9225, 9460, 9550, 9608, 9808, 10066, 10146, 10347, 10703, 11228, 11520, 11830, 12110, 12268, 12209, 12891, 13101, 13330, 13583]

gas_consumption = [2060, 2114, 2107, 2140, 2146, 2199, 2291, 2321, 2346, 2424, 2509, 2528, 2614, 2699, 2787, 2858, 2926, 3058, 3149, 3074, 3323, 3381, 3488, 3529]


#1980-
#thousand million barrels
reserves_barrels = [683.4, 696.5, 725.6, 737.3, 774.4, 802.6, 907.7, 938.9, 1026.7, 1027.3, 1027.5, 1032.7, 1039.3, 1041.4, 1055.6, 1065.9, 1088.7, 1107.4, 1092.9, 1237.9, 1258.1, 1266.8, 1321.5, 1334.1, 1343.7, 1353.1, 1363.9, 1399.3, 1471.6, 1513.2, 1621.6, 1661.8, 1687.3, 1687.9]
reserves_barrels = [x * 1000000 for x in reserves_barrels]

print("average consumption growth: ", average_change(consumption_barrels), " doubling time: ", doubling_time(consumption_barrels))
print("average reserves change: ", average_change(reserves_barrels), " doubling time: ", doubling_time(reserves_barrels))
print("average energy consumption growth: ", average_change(energy_consumption), " doubling time: ", doubling_time(energy_consumption))

#1980-
#how many years will the reserves last at given year consumption
enough_for_years = [r / c for (r, c) in zip(reserves_barrels, consumption_barrels[-len(reserves_barrels):])]

#1960-2013
world_population = [3036532274, 3077628660, 3130560798, 3195417729, 3260822806, 3327569763, 3397499965, 3467103790, 3537483987, 3611954924, 3686967186, 3763995029, 3840300260, 3915619481, 3991662329, 4066294816, 4139216505, 4212110303, 4286351034, 4362172135, 4438370556, 4515996446, 4596367792, 4677144145, 4757614414, 4839988721, 4925285182, 5012839430, 5101281852, 5189681453, 5278917295, 5365433943, 5448304921, 5531856268, 5614434365, 5697982639, 5780020061, 5861978511, 5942982003, 6023027888, 6101963950, 6179984867, 6257502234, 6334799169, 6412222945, 6489886972, 6567781100, 6645686556, 6724770576, 6804045819, 6884007764, 6964618177, 7043181414, 7125096708]
world_fertility_rate = [4.97948236106441, 4.99685819530925, 5.01113676413739, 5.02191448801587, 5.02037956002923, 4.98999330794235, 4.93157441902233, 4.90693398924276, 4.85108066647119, 4.7838782325247, 4.70957818648593, 4.61218187570381, 4.49410609136349, 4.37544795176232, 4.26246755669855, 4.13826180878561, 4.02672994836869, 3.92932863735946, 3.83936487980546, 3.7736079113279, 3.71631798567279, 3.66392458807635, 3.63705804409513, 3.60623086822255, 3.57588217413512, 3.54839385963458, 3.51367909702325, 3.47111004443242, 3.41597838676048, 3.34521436416391, 3.27108095399287, 3.18149132330502, 3.0946032808544, 3.00573988523987, 2.9315151235276, 2.85926711725989, 2.80269227214385, 2.75019290398177, 2.70876432055345, 2.6701970301134, 2.64511099191879, 2.61393717543333, 2.59120804593079, 2.57341523485324, 2.55846596192828, 2.53920620757993, 2.53091593790034, 2.52411013716623, 2.51595136404155, 2.50060806166854, 2.48883793331158, 2.47573037924979, 2.47085830381361, 2.45989740588603]

  

oil_consumption_per_capita = [c / float(p) for (c, p) in zip(consumption_barrels, world_population[-len(consumption_barrels):])]
print(oil_consumption_per_capita)

def myplot(data, descr, endyear = 2014):
    plt.plot(range(endyear - len(data), endyear), data)
    plt.axis([endyear - len(data) - 1, endyear, min(data) * 0.9, max(data) * 1.07])
    plt.xlabel(descr)
    plt.show()


myplot(oil_consumption_per_capita, "world oil consumption per capita")
#myplot(prediction(consumption_barrels, 10), 'world oil consumption with prediction assuming constant growth at current average', 2024)
#myplot(diff_serie(consumption_barrels), 'consumption_growth rate of world oil consumption in percents')
#myplot(consumption_barrels, 'world oil consumption (yearly in thousand of barrels)');
#myplot(world_population, "world population")
#myplot(world_fertility_rate, "world fertility rate")
#myplot(reserves_barrels, 'world oil proven reserves');
#myplot(enough_for_years, 'world reserves will last for y years at given year consumption');
#myplot(energy_consumption, 'world energy consumption in Mtoe');
#myplot(prediction(energy_consumption, 20), 'world energy consumption in Mtoe and prediction', 2034);
#myplot(gas_consumption, "world natural gas consumption (bcm)")


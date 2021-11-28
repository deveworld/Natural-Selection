import ast
import pandas as pd

data = pd.read_csv('NSdata.csv')
# energy-die-speed, humans, speed
refined_data = {"eds": [], "hus": [], "spd": []}

for generation_eds in data["energy-die-speed"]:
	avg = 0
	generation_eds = ast.literal_eval(generation_eds)
	for x in generation_eds:
		avg += x
	if len(generation_eds) != 0:
		avg = avg/len(generation_eds)
	refined_data["eds"].append(avg)

for generation_spd in data["speed"]:
	avg = 0
	generation_spd = ast.literal_eval(generation_spd)
	for x in generation_spd:
		avg += x
	if len(generation_spd) != 0:
		avg = avg/len(generation_spd)
	refined_data["spd"].append(avg)
	print(avg)
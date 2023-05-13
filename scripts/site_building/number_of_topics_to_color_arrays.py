import json,math

topic_colors=['#41588a','#40598a','#405a8b','#3f5b8b','#3f5c8b','#3e5d8c','#3e5e8c','#3d5f8c','#3d608d','#3c618d','#3c628d','#3b638e','#3b648e','#3a658f','#3a668f','#39678f','#396890','#386990','#386a90','#376b90','#376c91','#366d91','#366e92','#356e92','#356f92','#347092','#337193','#337293','#337393','#327494','#327594','#317694','#317795','#307895','#307995','#2f7a96','#2f7b96','#2e7c96','#2e7c97','#2d7d97','#2d7e97','#2c7f98','#2c8098','#2b8198','#2b8299','#2a8399','#2a8499','#29859a','#29869a','#28879a','#28889b','#27889b','#27899b','#268a9b','#268b9c','#258c9c','#258d9c','#248e9d','#248f9d','#23909d','#23919e','#22929e','#22929e','#21939f','#21949f','#20959f','#2096a0','#1f97a0','#1f98a0','#1f99a1','#1e9aa1','#1e9ba1','#1d9ba1','#1d9ca2','#1c9da2','#1c9ea2','#1b9fa3','#1ba0a3','#1aa1a3','#1aa2a4','#19a3a4','#19a4a4','#18a5a5','#18a5a5','#17a6a5','#17a7a6','#16a8a6','#16a9a6','#15aaa7','#15aba7','#14aca7','#14ada7','#13aea8','#13afa8','#12afa8','#12b0a9','#11b1a9','#11b2a9','#10b3aa','#10b4aa']

number_of_topics_to_colors=dict()

for number_of_topic_tags in range(1,101):

	step = len(topic_colors) / number_of_topic_tags
	
	array_of_colors=[]
	for i in range(number_of_topic_tags):
		array_of_colors.append(topic_colors[math.floor(i*step)])

	number_of_topics_to_colors[number_of_topic_tags]=array_of_colors

with open('number_of_topics_to_color_arrays.json','w') as f:
	json.dump(number_of_topics_to_colors,f)
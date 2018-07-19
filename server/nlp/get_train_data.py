import json
def get_train_data():
    try:
        trained_data = []
        with open('D:/Traning_data/sample_json.txt', "r",encoding='utf-8') as json_file_data:
            process_data = json_file_data.readlines()
        print(len(process_data))
        for js in range(0,len(process_data)):
            json_string=process_data[js]
            #print(json_string)
            json_data=json.loads(json_string)
            #print(json_data)
            for i in range(0,len(json_data)):
                entity_name = json_data[i]['entity_name']
                #print(entity_name)
                for k in range(0,len(json_data[i]["sentences"])):
                    s=json_data[i]["sentences"][k]
                    #print(s)
                    index=0
                    b=[]
                    dict = {}
                    while True:
                        value=s.lower().find(entity_name.lower(),index)
                        #print(value,value+13)
                        if value ==-1:
                            break
                        b.append((value, value + 13, 'CUSTOM'))
                        index=value+1
                        #print("b ",b)
                        dict['entities']=b
                    if index!=0:
                        trained_data.append((s,dict))
        return trained_data
    except Exception as e:
        print("error ",e)
        print("Please give proper Json as Input")
        return 0
#print(get_train_data())
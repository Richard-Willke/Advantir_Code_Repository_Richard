import csv



def find_UPC_from_csv(get_UPC):
    #'/home/pi/GUIraspberrypi/swirlgo_param/flavour_param.csv'
    with open('/home/pi/GUIraspberrypi/swirlgo_param/flavour_param.csv', "rb") as f:
        reader = csv.reader(f, delimiter=',')
        count = 0
        dicst={}
        for idx_col,row in enumerate(reader):
            if idx_col==0:
                header= row
           # print idx_col, row
            if row[0] == 'DEFAULT':
                for idx_row,item in enumerate(row):
                    dicst[header[idx_row]]=row[idx_row]
            if row[0] == get_UPC:
                for idx_row,item in enumerate(row):
                    dicst[header[idx_row]]=row[idx_row]
                return True, dicst
    return False, dicst




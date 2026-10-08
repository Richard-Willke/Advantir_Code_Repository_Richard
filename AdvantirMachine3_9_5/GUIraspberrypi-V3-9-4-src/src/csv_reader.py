import csv
import copy


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

def filtering_empty_seq(dicst):
    if dicst["HEAT_SEQ"]=="" or dicst["HEAT_SEQ"]==" " or dicst["HEAT_SEQ"]=="-":
        dicst["HEAT_SEQ"]="[]"
    if dicst["BLEND_SEQ"]=="" or dicst["BLEND_SEQ"]==" "  or dicst["BLEND_SEQ"]=="-":
        dicst["BLEND_SEQ"]="[]"
    if dicst["FLAVOUR_CALIB_SEQ"]=="" or dicst["FLAVOUR_CALIB_SEQ"]==" "  or dicst["FLAVOUR_CALIB_SEQ"]=="-":
        dicst["FLAVOUR_CALIB_SEQ"]="[]"
    if dicst["DISPENSE_SEQ"]=="" or dicst["DISPENSE_SEQ"]==" "  or dicst["DISPENSE_SEQ"]=="-":
        dicst["DISPENSE_SEQ"]="[]"
    return dicst

def find_UPC_n_SOFT_from_csv(get_UPC, get_soft):
    #'/home/pi/GUIraspberrypi/swirlgo_param/flavour_param.csv'
    with open('/home/pi/GUIraspberrypi/swirlgo_param/flavour_param.csv', "rb") as f:
        reader = csv.reader(f, delimiter=',')
        count = 0
        dicst={}
        tmp_default={}
        default={}
        for idx_col,row in enumerate(reader):
            if idx_col==0:
                header= row
           # print idx_col, row
            if row[0] == 'DEFAULT':
                for idx_row,item in enumerate(row):
                    tmp_default[header[idx_row]]=row[idx_row]
                if tmp_default["SOFTNESS_LVL"]==str(get_soft):
                    # print " default input ", tmp_default["SOFTNESS_LVL"],tmp_default["HEAT_SEQ"]
                    default = copy.deepcopy(tmp_default)
                    
            if row[0] == get_UPC and row[0] !='DEFAULT':
                for idx_row,item in enumerate(row):
                    dicst[header[idx_row]]=row[idx_row]
                if dicst["SOFTNESS_LVL"]==str(get_soft):
                    dicst=filtering_empty_seq(dicst)
                    return True, dicst
        if bool(dicst)==True:
            print "[WARN] QR ID matched, but SOFT:",get_soft,"is not found, but found SOFT:",dicst["SOFTNESS_LVL"]," in the flavourparam list"
            dicst=filtering_empty_seq(dicst)
            return True, dicst
    print " default input ", default["SOFTNESS_LVL"],default["BLEND_SEQ"], default["HEAT_SEQ"]
    dicst=filtering_empty_seq(default)
    return False, default


from sqlalchemy import create_engine
import pymysql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from datetime import date
#biblioteca Mongo
import pymongo
from pymongo import MongoClient
import time 
import calendar

MONGO_HOST = "200.48.235.251"
MONGO_PUERTO ="27017"
MONGO_PWD = "ciba15153232"
MONGO_USER = "estacionesrd"
MONGO_TIEMPO_FUERA =1000
MONGO_BASEDATOS = "PROYECTORD"
MONGO_COLECCION = "PRETRATAMIENTO"

MONGO_URI = "mongodb://"+ MONGO_USER +":"+ MONGO_PWD + "@"+MONGO_HOST +":" + MONGO_PUERTO + "/"+ MONGO_BASEDATOS 

def convert_formato_fecha(fec):
    fec = datetime.strptime(fec, '%d/%m/%Y')
    #restamos 1 dia que es el de consulta
    fec =fec -timedelta(1)
    print("fecha restada:", fec)
    fec_unix=int(time.mktime(fec.timetuple()))
    print("fecha calculada del anterior:", fec_unix)
    fe_unix = calendar.timegm(fec.utctimetuple())
    print("fecha nueva calculada del anterior:", fe_unix)
    if fec.month < 10:
        fec = str(fec.day)+'/0'+str(fec.month)+'/'+str(fec.year)
    else:
        fec = str(fec.day)+'/'+str(fec.month)+'/'+str(fec.year)
    
    
    return(fec, fec_unix)

def BD_MONGO_RIEGO_DEMANDA(pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-7*86400
    print("ts inicial:", fec_inicial_unix)
    print("ts usuario:", fec_unix_usuario)
    #fec_unix_usuario=fec_unix_usuario+86400
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo excedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

def nHidricaDemanda(fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_RIEGO_DEMANDA(pais, estacion, fec_unix_usuario)
    print("datos:", datos)
    ###calculo
    ET_acc = 0
    precip_acc = 0
    agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
    den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    cc_pmp = {'arenosa':0.05, 'arcillosa':0.12, 'franco':0.14}# 5%, 12%, 14%
    # cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    cap_suelo = den_ap_suelo[tipo]*30*cc_pmp[tipo]*0.5*10 # el *10 es para obtener las unidades en mm // *30 se refiere a que para 7 d??as, la profundidad de ra??z es 30 cm.
    # suelo_infil_lluvia = ET_acc + cap_suelo
    #unimos datos para la grafica de la evapotranspiracion
    Vector_Grafica=[]
    evp_cultivo=0

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        ET_acc += et
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        evp_cultivo += round(et*1.1,2)
        #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
        if inc_lluvia > 5:
            precip_acc += inc_lluvia
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
    suelo_infil_lluvia = (ET_acc*1.1) + cap_suelo

    if suelo_infil_lluvia < precip_acc:
        lluvia_efectiva = suelo_infil_lluvia
    else:
        lluvia_efectiva = precip_acc
    ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
    NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
    if NH < 0:
        NH = 0
    Deficit=evp_cultivo-lluvia_efectiva
    #print("lluvia efectiva:", lluvia_efectiva)
    if Deficit <= 0:
        Deficit=0
    print("vector grafica:", Vector_Grafica)
    return round(NH,2), Vector_Grafica, round(evp_cultivo,2), round(Deficit,2)

### funion b : hidrica

def BD_MONGO_RIEGO(dias, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-dias*86400
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo excedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)

# def nHidrica(dias, fec, estacion, tipo, tipo_riego):
#     pais = 3 #1 peru
#     print("Fecha ingresada por el usuario:", fec)
#     #convertimos a string y unix y restamos el dia de consulta
#     fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
#     print("Fecha a ingresar a calculo:", fec_string_usuario)
#     ##solicitamos datos
#     datos=BD_MONGO_RIEGO(dias, pais, estacion, fec_unix_usuario)
#     print(datos)
#     ###calculo
#     ET_acc = 0
#     precip_acc = 0
#     agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
#     den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
#     cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
#     suelo_infil_lluvia = ET_acc + cap_suelo
#     #unimos datos para la grafica de la evapotranspiracion
#     Vector_Grafica=[]
#     evp_cultivo=0

#     for k in datos:
#         fecha = k["Fecha_D_str"]
#         et = k["Datos"]["ET_D"]
#         ET_acc += et
#         inc_lluvia = k["Datos"]["Precipitacion_D"]
#         evp_cultivo += round(et*1.1,2)
#         #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
#         if inc_lluvia > 5:
#             precip_acc += inc_lluvia
#         Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
#     if suelo_infil_lluvia < precip_acc:
#         lluvia_efectiva = suelo_infil_lluvia
#     else:
#         lluvia_efectiva = precip_acc
#     ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
#     NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
#     if NH < 0:
#         NH = 0
#     Deficit=evp_cultivo-lluvia_efectiva
#     #print("lluvia efectiva:", lluvia_efectiva)
#     return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(Deficit,2)

def acumulado_intervalos(data, prof_raiz_cm, periodo, tipo, tipo_riego):
    den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    cc_pmp = {'arenosa':0.05, 'arcillosa':0.12, 'franco':0.14}# 5%, 12%, 14%
    
    chunk_size = periodo
    divide_data = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    prof_raiz = int(round(prof_raiz_cm/len(divide_data)))
    print("Profundidad de ra??z: ", prof_raiz)
    # cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    cap_suelo = den_ap_suelo[tipo]*prof_raiz*cc_pmp[tipo]*0.5*10 # el *10 es para obtener las unidades en mm.
    
    # print("CAP SUELO: ", cap_suelo)
    
    Deficit_total = 0
    NH_total = 0
    
    for j in divide_data:
        ET_acc = 0
        precip_acc = 0
        evp_cultivo=0
        
        for k in j:
            et = k["Datos"]["ET_D"]
            ET_acc += et
            inc_lluvia = k["Datos"]["Precipitacion_D"]
            evp_cultivo += round(et*1.1,2)
            #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
            if inc_lluvia > 5:
                precip_acc += inc_lluvia
    
            
        suelo_infil_lluvia = (ET_acc*1.1) + cap_suelo
        
        if suelo_infil_lluvia < precip_acc:
            lluvia_efectiva = suelo_infil_lluvia
        else:
            lluvia_efectiva = precip_acc
        ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
        NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
        if NH < 0:
            NH = 0
        Deficit=evp_cultivo-lluvia_efectiva
        
        # print("deficit one: ", Deficit)
        # print("NH one: ", NH)
        
        Deficit_total += Deficit
        NH_total += NH
    
    return Deficit_total, NH_total


# # Deficit_total, NH_total = acumulado_intervalos(datos, int(50), int(7))

def nHidrica(dias, fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_RIEGO(dias, pais, estacion, fec_unix_usuario)

    #Obtenci??n datos solo para gr??fica:
    Vector_Grafica=[]

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))

    # agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
    # den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
    # cc_pmp = {'arenosa':0.05, 'arcillosa':0.12, 'franco':0.14}# 5%, 12%, 14%
    #Profundidad de raices / intervalo de riego:
    #7 d??as -> 30 cm de profundidad de ra??z.
    # 8 - 14 d??as -> 50 cm de profundidad de ra??z.
    # 15 - 28 d??as -> 70 cm de profundidad de ra??z.
    intervalo = 7

    if dias == int(7):
        prof_raiz = 30
        Deficit_total, NH_total = acumulado_intervalos(datos, int(prof_raiz), int(intervalo), tipo, tipo_riego)
    elif (dias > int(7) and dias <= int(14)):
        prof_raiz = 50
        Deficit_total, NH_total = acumulado_intervalos(datos, int(prof_raiz), int(intervalo), tipo, tipo_riego)
    else:
        prof_raiz = 70
        Deficit_total, NH_total = acumulado_intervalos(datos, int(prof_raiz), int(intervalo), tipo, tipo_riego)

    #print("lluvia efectiva:", lluvia_efectiva)
    return round(NH_total/10,2), Vector_Grafica, round(Deficit_total,2)

##funcion c : intervalo

def BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario):
    fec_inicial_unix = fec_unix_usuario-dias*86400
    
    try:
        cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIEMPO_FUERA)
        baseDatos = cliente[MONGO_BASEDATOS]
        coleccion=baseDatos[MONGO_COLECCION]
        ##4 CONSULTAS A LA VEZ
        datos = coleccion.aggregate(
                                        [
                                            {"$match": 
                                                {"$and":
                                                        [
                                                            {"pais":pais},
                                                            {"estacion":estacion},
                                                            {"Fecha_D":{"$gt": fec_inicial_unix ,"$lte":fec_unix_usuario}}
                                                        ]
                                                }
                                            },
                                            
                                            {
                                            "$project":{
                                                "_id":0,
                                                "Fecha_D_str":1,
                                                
                                                "Datos.ET_D":1,
                                                "Datos.Precipitacion_D":1,
                                            }
                                            }

                                        ])

        
        
        semana_gdd = list(datos)
        return semana_gdd
    except pymongo.errors.ServerSelectionTimeoutError as errorTiempo:
        return("Tiempo excedido"+ errorTiempo)
    except pymongo.errors.ConnectionFailure as errorConnexion:
        return("Fallo al conectarse a mongodb" + errorConnexion)


# def nHidricaIntervalo(dias, fec, estacion, tipo, tipo_riego):
#     pais = 3 #1 peru
#     print("Fecha ingresada por el usuario:", fec)
#     #convertimos a string y unix y restamos el dia de consulta
#     fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
#     print("Fecha a ingresar a calculo:", fec_string_usuario)
#     ##solicitamos datos
#     datos=BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario)
#     ###calculo
#     ET_acc = 0
#     precip_acc = 0
#     agua_aprove = {'arenosa':2.5, 'arcillosa':7, 'franco':4.75}
#     den_ap_suelo = {'arenosa':1.65, 'arcillosa':1.3, 'franco':1.25}
#     cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
#     suelo_infil_lluvia = ET_acc + cap_suelo
#     #unimos datos para la grafica de la evapotranspiracion
#     Vector_Grafica=[]
#     evp_cultivo=0

#     for k in datos:
#         fecha = k["Fecha_D_str"]
#         et = k["Datos"]["ET_D"]
#         ET_acc += et
#         inc_lluvia = k["Datos"]["Precipitacion_D"]
#         evp_cultivo += round(et*1.1,2)
#         #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
#         if inc_lluvia > 5:
#             precip_acc += inc_lluvia
#         Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
#     if suelo_infil_lluvia < precip_acc:
#         lluvia_efectiva = suelo_infil_lluvia
#     else:
#         lluvia_efectiva = precip_acc
#     ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
#     NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
#     if NH < 0:
#         NH = 0
#     prom_evp_cultivo=evp_cultivo/dias ##sacamos el promedio de evapo del cultivo por dia
#     intervalo_30= (30+lluvia_efectiva)/prom_evp_cultivo ###a 30 le sumamos la lluvia efectiva y dividimos entre el promedio
#     #print("intervalo 30:", intervalo_30)
#     intervalo_50= (50+lluvia_efectiva)/prom_evp_cultivo
#     #print("intervalo 50:", intervalo_50)
#     intervalo_70= (70+lluvia_efectiva)/prom_evp_cultivo
#     #print("intervalo 70:", intervalo_70)
#     return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(intervalo_30, 1), round(intervalo_50,1), round(intervalo_70,1)


# def nHidricaIntervalo(dias, fec, estacion, tipo, tipo_riego):
#     pais = 3 #1 peru
#     print("Fecha ingresada por el usuario:", fec)
#     #convertimos a string y unix y restamos el dia de consulta
#     fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
#     print("Fecha a ingresar a calculo:", fec_string_usuario)
#     ##solicitamos datos
#     datos=BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario)
#     ###calculo
#     ET_acc = 0
#     precip_acc = 0
#     agua_aprove = {'arenosa':2.5, 'arcillosa':6, 'franco':7}
#     den_ap_suelo = {'arenosa':1.43, 'arcillosa':1.33, 'franco':1.43}
#     cc_pmp = {'arenosa':0.05, 'arcillosa':0.12, 'franco':0.14}# 5%, 12%, 14%
#     #Profundidad de raices / intervalo de riego:
#     #7 d??as -> 30 cm de profundidad de ra??z.
#     # 8 - 14 d??as -> 50 cm de profundidad de ra??z.
#     # 15 - 28 d??as -> 70 cm de profundidad de ra??z.
#     if dias == int(7):
#         prof_raiz = 30
#     elif (dias > int(7) and dias <= int(14)):
#         prof_raiz = 50
#     else:
#         prof_raiz = 70

#     # cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
#     cap_suelo = den_ap_suelo[tipo]*prof_raiz*cc_pmp[tipo]*0.5*10 # el *10 es para obtener las unidades en mm.
#     # suelo_infil_lluvia = ET_acc + cap_suelo #As?? estaba ANTES.
#     #unimos datos para la grafica de la evapotranspiracion
#     Vector_Grafica=[]
#     evp_cultivo=0

#     for k in datos:
#         fecha = k["Fecha_D_str"]
#         et = k["Datos"]["ET_D"]
#         ET_acc += et
#         inc_lluvia = k["Datos"]["Precipitacion_D"]
#         evp_cultivo += round(et*1.1,2)
#         #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
#         if inc_lluvia > 5:
#             precip_acc += inc_lluvia
#         Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))
    
#     suelo_infil_lluvia = (ET_acc*1.1) + cap_suelo
    
#     if suelo_infil_lluvia < precip_acc:
#         lluvia_efectiva = suelo_infil_lluvia
#     else:
#         lluvia_efectiva = precip_acc

#     ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
#     NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]
#     if NH < 0:
#         NH = 0
#     prom_evp_cultivo=evp_cultivo/dias ##sacamos el promedio de evapo del cultivo por dia
#     turno_max = (int(cap_suelo) + lluvia_efectiva)/prom_evp_cultivo ### le sumamos la lluvia efectiva y dividimos entre el promedio
#     # #print("intervalo 30:", intervalo_30)
#     # intervalo_50= (50+lluvia_efectiva)/prom_evp_cultivo
#     # #print("intervalo 50:", intervalo_50)
#     # intervalo_70= (70+lluvia_efectiva)/prom_evp_cultivo
#     # #print("intervalo 70:", intervalo_70)
#     # return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(intervalo_30, 1), round(intervalo_50,1), round(intervalo_70,1)
#     return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(turno_max, 1)


def nHidricaIntervalo(dias, fec, estacion, tipo, tipo_riego):
    pais = 3 #1 peru
    print("Fecha ingresada por el usuario:", fec)
    #convertimos a string y unix y restamos el dia de consulta
    fec_string_usuario, fec_unix_usuario = convert_formato_fecha(fec)
    print("Fecha a ingresar a calculo:", fec_string_usuario)
    ##solicitamos datos
    datos=BD_MONGO_INTERVALO(dias, pais, estacion, fec_unix_usuario)

    # print(datos)

    #Obtenci??n datos solo para gr??ficar y obtener la fecha final:
    Vector_Grafica=[]

    for k in datos:
        fecha = k["Fecha_D_str"]
        et = k["Datos"]["ET_D"]
        inc_lluvia = k["Datos"]["Precipitacion_D"]
        Vector_Grafica.append((fecha, round(et*1.1,2), round(inc_lluvia,2)))

    ###calculo
    ET_acc = 0
    precip_acc = 0
    agua_aprove = {'arenosa':2.5, 'arcillosa':6, 'franco':7}
    den_ap_suelo = {'arenosa':1.43, 'arcillosa':1.33, 'franco':1.43}
    cc_pmp = {'arenosa':0.05, 'arcillosa':0.12, 'franco':0.14}# 5%, 12%, 14%
    #Profundidad de raices / intervalo de riego:
    #7 d??as -> 30 cm de profundidad de ra??z.
    # 8 - 14 d??as -> 50 cm de profundidad de ra??z.
    # 15 - 28 d??as -> 70 cm de profundidad de ra??z.
    if dias == int(7):
        prof_raiz_cm = 30
    elif (dias > int(7) and dias <= int(14)):
        prof_raiz_cm = 50
    else:
        prof_raiz_cm = 70

    # ######################

    chunk_size = 7
    divide_data = [datos[i:i + chunk_size] for i in range(0, len(datos), chunk_size)]
    
    prof_raiz = int(round(prof_raiz_cm/len(divide_data)))
    print("Profundidad de ra??z: ", prof_raiz)
    # cap_suelo = den_ap_suelo[tipo]*500*agua_aprove[tipo]
    cap_suelo = den_ap_suelo[tipo]*prof_raiz*cc_pmp[tipo]*0.5*10 # el *10 es para obtener las unidades en mm.
    
    # print("CAP SUELO: ", cap_suelo)

    NH_total = 0
    evp_cultivo_total=0
    turno_max_total = 0
    
    for j in divide_data:
        ET_acc = 0
        precip_acc = 0
        evp_cultivo=0
        
        for k in j:
            et = k["Datos"]["ET_D"]
            ET_acc += et
            inc_lluvia = k["Datos"]["Precipitacion_D"]
            evp_cultivo += round(et*1.1,2)
            #print("Fecha:", fecha, " ","Temperatura:", temperatura , " ", "GDD:", gdd)
            if inc_lluvia > 5:
                precip_acc += inc_lluvia
    
            
        suelo_infil_lluvia = (ET_acc*1.1) + cap_suelo
        
        if suelo_infil_lluvia < precip_acc:
            lluvia_efectiva = suelo_infil_lluvia
        else:
            lluvia_efectiva = precip_acc

        ef_riego = {'inundaci??n':0.5,'microaspersi??n':0.7,'goteo':0.9}
        NH = (ET_acc*1.1 - lluvia_efectiva)*10/ef_riego[tipo_riego]

        if NH < 0:
            NH = 0

        prom_evp_cultivo=evp_cultivo/chunk_size ##sacamos el promedio de evapo del cultivo por semana (7 d??as)
        turno_max = (int(cap_suelo) + lluvia_efectiva)/prom_evp_cultivo ### le sumamos la lluvia efectiva y dividimos entre el promedio


        # print("NH one: ", NH)

        NH_total += NH
        evp_cultivo_total += evp_cultivo
        turno_max_total += turno_max

    # #print("intervalo 30:", intervalo_30)
    # intervalo_50= (50+lluvia_efectiva)/prom_evp_cultivo
    # #print("intervalo 50:", intervalo_50)
    # intervalo_70= (70+lluvia_efectiva)/prom_evp_cultivo
    # #print("intervalo 70:", intervalo_70)
    # return round(NH/10,2), Vector_Grafica, round(evp_cultivo,2), round(intervalo_30, 1), round(intervalo_50,1), round(intervalo_70,1)
    return round(NH_total/10,2), Vector_Grafica, round(evp_cultivo_total,2), round(turno_max_total, 1)


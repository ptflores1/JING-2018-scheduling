"""
Este modulo se encarga de leer los archivos de la instancia y crear los parametros
y subconjuntos que se necesitan en el modelo
"""

import csv
from collections import defaultdict

# Conjuntos
def deportes(path_factibilidad):
    """
    Retorna una lista con todos los deportes
    :param path: Ruta al archivo csv de la relacion de factibilidad cancha-deporte
    :return:
    """
    with open(path_factibilidad, "r", encoding="UTF-8") as file:
        linea = file.readline().strip().split(";")
        return linea[1:]


def eventos(path_eventos):
    """
    Retorna una lista con todos los eventos
    :param path: Ruta al archivo csv donde se guarda la informacion de cada evento
    :return:
    """
    with open(path_eventos, "r", encoding="UTF-8") as file:
        data = csv.reader(file, skipinitialspace=True, delimiter=";")
        return [l[0] for l in list(data)[1:]]

def dias(path_dias):
    """
    Retorna una lista con todos los dias y un diccionario con los parametros
    correspondientes a los periodos de 5 minutos por cada dia
    :param path: Ruta al archivo csv donde se guardan los periodos de tiempo para cada dia
    :return:
    """
    with open(path_dias, "r", encoding="UTF-8") as file:
        data = csv.DictReader(file, skipinitialspace=True, delimiter=";")
        data = list(data)
        dias = [int(d["dia"]) for d in data]
        periodos = {int(d["dia"]): int(d["bloques de 15 min"]) for d in data}
        return dias, periodos


def canchas(path_factibilidad):
    """
    Retorna una lista con todas las canchas
    :param path: Ruta al archivo csv de la relacion de factibilidad cancha-deporte
    :return:
    """
    with open(path_factibilidad, "r", encoding="UTF-8") as file:
        data = csv.reader(file, skipinitialspace=True, delimiter=";")
        return [l[0] for l in list(data)[1:]]


# Parametros
def factibilidad_canchas_deporte(path_factibilidad):
    """
    Retorna un diccionario con los parametros correspondientes a la factibilidad
    de las canchas para un deporte
    :param path: Ruta al archivo csv de la relacion de factibilidad cancha-deporte
    :return:
    """
    with open(path_factibilidad, "r", encoding="UTF-8") as file:
        data = csv.DictReader(file, skipinitialspace=True, delimiter=";")
        params = {(linea["cancha"], deporte): int(linea[deporte]) for linea in data for deporte in list(linea.keys())[1:]}
    return params

def factibilidad_canchas_evento(path_eventos, path_factibilidad):
    """
    Retorna un diccionario con los parametros correspondientes a la factibilidad
    de las canchas para un evento
    :param path_eventos: Ruta al archivo csv donde se guarda la informacion de cada evento
    :param path_factibilidad: Ruta al archivo csv de la relacion de factibilidad cancha-deporte
    :return:
    """
    *_, evento_deporte, _ = params_eventos(path_eventos)
    factibilidad_deporte = factibilidad_canchas_deporte(path_factibilidad)
    factibilidad_evento = dict()
    for key, factibilidad in factibilidad_deporte.items():

        cancha, deporte = key
        for evento, deporte_evento in evento_deporte.items():
            if deporte == deporte_evento:
                factibilidad_evento[evento, cancha] = int(factibilidad)
    return factibilidad_evento


def params_eventos(path_eventos):
    """
    Retorna una tupla con los parametos correspondientes a:
    La cantidad de veces que se debe jugar cada evento
    La jerarquia de cada evento
    Que tan atractiva es la final del evento
    El deporte correspondiente al evento
    :param path: Ruta al archivo csv donde se guarda la informacion de cada evento
    :return:
    """

    with open(path_eventos, "r", encoding="UTF-8") as file:
        data = csv.DictReader(file, skipinitialspace=True, delimiter=";")
        data = list(data)
        veces = {d["evento"]: int(d["veces que se juega"]) for d in data}
        jerarquia = {d["evento"]: int(d["jerarquia"]) for d in data}
        atractivo = {d["evento"]: int(d["deporte atractivo"]) for d in data}
        deporte = {d["evento"]: d["deporte"] for d in data}
        duracion = {d["evento"]: int(d["duracion"]) for d in data}

        return  veces, jerarquia, atractivo, deporte, duracion

def param_beta(base_path):
    """
    Retorna un diccionarion con los parametros correspondientes a beta
    :param base_path: Base de la ruta a los archivos donde se guardan los parametro beta para cada dia
    Si los archivos se llaman 'instancia/beta_viernes.csv', 'instancia/beta_sabado.csv', 'instancia/beta_domingo.csv'
    la ruta base debe ser: 'instancia/beta'
    :return:
    """
    dias = ["viernes", "sabado", "domingo"]
    n_dia = {"viernes": 1, "sabado": 2, "domingo": 3}
    beta = dict()
    for dia in dias:
        with open(base_path + "_" + dia + ".csv", "r", encoding="UTF-8") as file:
            data = csv.DictReader(file, skipinitialspace=True, delimiter=";")
            params = {(int(linea["hora"]), cancha, n_dia[dia]): int(linea[cancha]) for linea in
                      data for cancha in list(linea.keys())[1:]}
            for key, value in params.items():
                beta[key] = value
    return beta


# Subconjuntos

def epsilon_s(deportes, eventos_deportes):
    r = defaultdict(list)
    for deporte in deportes:
        for evento, deporte_evento in eventos_deportes.items():
            if deporte == deporte_evento:
                r[deporte].append(evento)
    return r


def epsilon_f(atractivos):
    return [e for e, a in atractivos.items() if a == 1]

def epsilon_n():
    pass



if __name__ == "__main__":
    #*_, eventos_deporte = params_eventos("instancia/eventos.csv")
    #deportes = deportes("instancia/factibilidad cancha-deporte.csv")
    # print(eventos("instancia/eventos.csv"))
    # print(dias("instancia/dias.csv"))
    # print(canchas("instancia/factibilidad cancha-deporte.csv"))
    # print(param_beta("instancia/beta"))
    print(factibilidad_canchas_evento("instancia/eventos.csv", "instancia/factibilidad cancha-deporte.csv"))
    #print(epsilon_s(deportes, eventos_deporte))

    #evento_veces, evento_jerarquia, evento_atractivo, eventos_deporte, duracion = params_eventos("instancia/eventos.csv")
    #print(duracion)

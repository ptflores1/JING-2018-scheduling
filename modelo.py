import gurobipy
import reader
import collections

instancias = {1: "instancia", # 10 Eventos de futbol
              2: "instancia2", # Un evento de cada tipo
              3: "instancia3.0", # Todos los eventos
              4: "instancia 4" # Todos los eventos en bloques de 5 min
              }
instancia = instancias[1]

PATH_EVENTOS = f"{instancia}/eventos.csv"
PATH_DIAS = f"{instancia}/dias.csv"
BASE_PATH_BETA = f"{instancia}/beta"
PATH_FACTIBILIDAD = f"{instancia}/factibilidad cancha-deporte.csv"


model = gurobipy.Model("JING 2018 scheduling")
print("Definiendo parametros")

# Definicion de Conjuntos
deportes = reader.deportes(PATH_FACTIBILIDAD)
dias, T_d = reader.dias(PATH_DIAS)
canchas = reader.canchas(PATH_FACTIBILIDAD)
eventos = reader.eventos(PATH_EVENTOS)


# Parametros
R = len(canchas)
evento_veces, phi_e, evento_atractivo, eventos_deporte, t_e = reader.params_eventos(PATH_EVENTOS)
f_e_k = reader.factibilidad_canchas_evento(PATH_EVENTOS, PATH_FACTIBILIDAD)
beta_t_k_d = reader.param_beta(BASE_PATH_BETA)
M = 8*200


# Subconjuntos
epsilon_s = reader.epsilon_s(deportes, eventos_deporte)
epsilon_n = epsilon_s["natacion"]
epsilon_f = reader.epsilon_f(evento_atractivo)
delta_s_i = collections.defaultdict(list)
for evento, jerarquia in phi_e.items():
    delta_s_i[eventos_deporte[evento], jerarquia].append(evento)
eta_e = reader.jerarquia_eventos(PATH_EVENTOS)
print(eta_e)



print("Definiendo variables")
# Variables
x = dict()
y = dict()

for d in dias:
    for t in range(1, T_d[d] + 1):
        for k in canchas:
            for e in eventos:
                x[t, e, k, d] = model.addVar(vtype=gurobipy.GRB.BINARY,
                                             name="X_{}_{}_{}_{}".format(t,
                                                                         e,
                                                                         k,
                                                                         d))
                y[t, e, k, d] = model.addVar(vtype=gurobipy.GRB.BINARY,
                                             name="Y_{}_{}_{}_{}".format(t,
                                                                         e,
                                                                         k,
                                                                         d))


gamma = model.addVar(vtype=gurobipy.GRB.INTEGER, name="gamma")
model.update()

# Restricciones
print("Creando restricciones")


print("Todos los eventos ocurren una sola vez")
for e in eventos:
    model.addConstr(gurobipy.quicksum(x[t, e, k, d] for d in dias
                                      for t in range(1, T_d[d] + 1)
                                      for k in canchas if f_e_k[e, k] == 1) == 1,
                    "El evento {} ocurre una vez".format(e))

    # model.addConstr(gurobipy.quicksum(x[t, e, k, d] for d in dias
    #                                   for t in range(1, T_d[d] + 1)
    #                                   for k in canchas) <= 1,
    #                 "El evento {} ocurre una vez".format(e))

    model.addConstr(gurobipy.quicksum(x[t, e, k, d] for d in dias
                                      for t in range(1, T_d[d] + 1)
                                      for k in canchas if f_e_k[e, k] == 0) == 0,
                    "El evento {} ocurre una vez".format(e))
model.update()

# print("Todos los eventos ocurren una sola vez sin meter factibilidad")
# for e in eventos:
#     model.addConstr(gurobipy.quicksum(x[t, e, k, d] for d in dias
#                                       for t in range(1, T_d[d] + 1)
#                                       for k in canchas) == 1,
#                     "El evento {} ocurre una vez".format(e))
#
# model.update()

# print("Factibilidad de canchas")
# for e in eventos:
#     for k in canchas:
#         model.addConstr(
#             gurobipy.quicksum(x[t, e, k, d] for d in dias for t in range(1, T_d[d]+1)) <=
#             f_e_k[e, k],
#             "Compatibilidad entre evento {} y cancha {}".format(e, k))


model.update()
print("Sólo se juega un evento a la vez en cada cancha")
for d in dias:
    for t in range(1, T_d[d] + 1):
        for k in canchas:
            model.addConstr(
                gurobipy.quicksum(y[t, e, k, d] for e in eventos) <= 1)
model.update()



print("Construcción de la variable gamma")
for d in dias:
    for t in range(1, T_d[d] + 1):
        model.addConstr(gamma >= gurobipy.quicksum(
            y[t, e, k, d] for k in canchas for e in eventos),
                        "topes de horario en el bloque con más topes de horario")
model.update()


print("Respetar la jerarquía de eventos")
for e in eventos:
    if len(eta_e[e]) > 0:  # evalua si hay eventos de jerarquia mayor que el evento e
        for d in dias:
            for t in range(1, T_d[d]+1):
                model.addConstr(gurobipy.quicksum(x[t, e, k, d] for k in canchas)<=
                                (gurobipy.quicksum(y[r, e2, k2, d] for k2 in canchas for e2 in eta_e[e]  for r in range(1, t)) +
                                 gurobipy.quicksum(y[r, e2, k2, c] for k2 in canchas for c in range(1, d) for e2 in eta_e[e] for r in range(1, T_d[d]+1)))
                                /(len(eta_e[e]*t_e[e])))




print("Respetar hora de termino Cataldo edition")
for e in eventos:
    for k in canchas:
        if f_e_k[e, k]==1:
            for d in dias:
                for t in range(T_d[d]-t_e[e]+2, T_d[d] + 1):
                    model.addConstr(x[t,e,k,d]==0)
model.update()

#print("Eventos de natación no pueden quedar el mismo día")


print('No pueden topar las finales atractivas')
for t in range(1, T_d[3]+1):
    model.addConstr(gurobipy.quicksum(y[t, e, k, 3] for k in canchas for e in epsilon_f) <= 1)


print("Las finales atractivas deben quedar para el último dia")
for e in epsilon_f:
    for d in range(1, 3):
        for t in range(1, T_d[d] + 1):
            for k in canchas:
                if f_e_k[e, k] == 1:
                    model.addConstr(x[t,e,k,d]==0)
model.update()



model.update()

print("Disponibilidad de cancha")
for d in dias:
    for t in range(1, T_d[d] + 1):
        for k in canchas:
            model.addConstr(beta_t_k_d[t, k, d] >= gurobipy.quicksum(
                y[t, e, k, d] for e in eventos),
                            "No se puedeocupar la cancha {} el dia {} en el "
                            "periodo {} si esta no está disponible".format(k, d, t))




print("relacion x con y")
for e in eventos:
    for k in canchas:
        for d in dias:
            for t in range(1 , T_d[d] + 1):
                t2 = 1 if t - t_e[e] + 1 <= 0 else t - t_e[e] + 1
                model.addConstr(gurobipy.quicksum(
                    x[r, e, k, d] for r in range(t2, t + 1)) == y[t, e, k, d],
                                "El evento {} se está llevando acabo el dia {} en {}en {} si empezó a lo más {} "
                                "periodos atras ".format(e, d, k, t,
                                                         t - t_e[e]))




model.setObjective(gamma, gurobipy.GRB.MINIMIZE)

print("Optimizando csm depresion incoming")
model.optimize()
model.write("solucion.sol")
model.printAttr("X")









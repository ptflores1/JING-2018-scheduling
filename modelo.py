import gurobipy
import collections


import reader
from calendario.calendartry import create_calendar

INSTANCIAS = {1 : "instancia", 2: "instancia2"}
INSTANCIA = INSTANCIAS[2]

PATH_EVENTOS = f"{INSTANCIA}/eventos.csv"
PATH_DIAS = f"{INSTANCIA}/dias.csv"
BASE_PATH_BETA = f"{INSTANCIA}/beta"
PATH_FACTIBILIDAD = f"{INSTANCIA}/factibilidad cancha-deporte.csv"


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




print("Definiendo variables")
# Variables
x = dict()
y = dict()
w = dict()

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
                                      for k in canchas) == 2,
                    "El evento {} ocurre una vez".format(e))
model.update()


print("Sólo se juega un evento a la vez en cada cancha")
for d in dias:
    for t in range(1, T_d[d] + 1):
        for k in canchas:
            model.addConstr(
                gurobipy.quicksum(y[t, e, k, d] for e in eventos) <= 2)
model.update()



print("Compatibilidad entre eventos y canchas")
for e in eventos:
    for k in canchas:
        model.addConstr(
          gurobipy.quicksum(
              x[t, e, k, d] for t in range(1, T_d[d] + 1) for d in dias) <= 2*f_e_k[e, k],
            "Compatibilidad entre evento {} y cancha {}".format(e, k))
model.update()


print("Construcción de la variable gamma")
for d in dias:
    for t in range(1, T_d[d] + 1):
        model.addConstr(gamma >= gurobipy.quicksum(
            y[t, e, k, d] for k in canchas for e in eventos),
                        "topes de horario en el bloque con más topes de horario")
model.update()

# print("Respetar jerarquía de eventos entre dias y durante el día 2.0")
# for s in deportes:
#     for e in epsilon_s[s]:
#         for j in epsilon_s[s]:
#             if phi_e[e] + 1 == phi_e[j]:
#                 for d in dias:
#                     for t in range(1,T_d[d]+1):
#                         for i in range(1, max(phi_e[h] for h in epsilon_s[s]) + 1):
#                             model.addConstr((gurobipy.quicksum(x[r, j, k, c] for k in canchas for f in delta_s_i[s, i] for c in range(1, d +1) for r in range(1, T_d[c]+1) ) + gurobipy.quicksum(x[r, f, k, d] for r in range(1, t - t_e[e] + 1) for k in canchas for f in delta_s_i[s,i]))/len(delta_s_i[s,i])>= gurobipy.quicksum(x[t, e, k, d] for k in canchas))


print("respetar hora de término")
for d in dias:
    for t in range(1, T_d[d] + 1):
        for k in canchas:
            for e in eventos:
                model.addConstr(t + x[t, e, k, d] * t_e[e] <= T_d[d],
                                "evento {} empieza en {} antes que"
                                "se exceda el tiempo de termino {} el dia {}".format(
                                    e, t, T_d[d], d))
model.update()

# print("no pueden quedar ambos eventos de natación el mismo dia")
# for d in dias:
#     for e in epsilon_n:
#         for j in epsilon_n:
#             model.addConstr(w[e, d] + w[j, d] <= 1,
#                             "no se realizan los eventos {} y {} "
#                             "el mismo dia {}".format(e, j, d))
#
# model.update()


# print("las finales mas atractivas no pueden topar")
# for t in range(1, T_d[3] + 1):
#     model.addConstr(gurobipy.quicksum(y[t, e, k, 3] for k in canchas
#                                                     for e in epsilon_f) <= 1,
#                     "las finales atractivas no pueden topar")
# model.update()

print("Las finales atractivas deben quedar para el último dia")
model.addConstr(gurobipy.quicksum(x[t, e, k, d]
                                  for e in epsilon_f
                                  for k in canchas
                                  for d in range(1, 2 + 1)
                                  for t in range(1, T_d[d] + 1)) == 0,
                "las finales atractivas ocurren el ultimo día")

model.update()

#
# print("Disponibilidad de cancha")
# for d in dias:
#     for t in range(1, T_d[d] + 1):
#         for k in canchas:
#             model.addConstr(beta_t_k_d[t, k, d] >= gurobipy.quicksum(
#                 y[t, e, k, d] for e in eventos),
#                             "No se puedeocupar la cancha {} el dia {} en el "
#                             "periodo {} si esta no está disponible".format(k, d, t))


print("relacion x con y")
for e in eventos:
    for k in canchas:
        for d in dias:
            for t in range(1 , T_d[d] + 1):
                t2 = 1 if t - t_e[e] + 1 <= 0 else t - t_e[e] + 1
                model.addConstr(gurobipy.quicksum(
                    x[r, e, k, d] for r in range(t2, t + 1)) <= y[t, e, k, d],
                                "El evento {} se está llevando acabo el dia {} en {}en {} si empezó a lo más {} "
                                "periodos atras ".format(e, d, k, t,
                                                         t - t_e[e]))

model.update()



model.setObjective(gamma, gurobipy.GRB.MINIMIZE)

print("Optimizando")
model.optimize()
#model.write("solucion.sol")
model.printAttr("X")


#create_calendar(y, dias, eventos, T_d)









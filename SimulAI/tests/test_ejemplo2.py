import win32com.client as win32
import matplotlib.pyplot as plt
import os
import numpy as np


# datos reinforcement learning
alfa = 0.15
gamma = 0.95
epsilon = 0.10

# numero de episodios
ep_maximo = 5

# numero de pasos
t_maximo = 10

# inicializar recompensa por episodio
r_episodio = np.arange(ep_maximo, dtype=float)
a = np.arange(ep_maximo, dtype=float)

# guardar resultados a minimizar
r_transportes = np.arange(ep_maximo, dtype=float)
r_buffers = np.arange(ep_maximo, dtype=float)
r_salidas = np.arange(ep_maximo, dtype=float)
r_total = np.arange(ep_maximo, dtype=float)

# inicializar acciones
acciones = np.array(
    [
        [0, 0, 0],
        [10, 0, 0],
        [-10, 0, 0],
        [10, 10, 0],
        [10, -10, 0],
        [-10, 10, 0],
        [-10, -10, 0],
        [10, 10, 1],
        [10, 10, -1],
        [10, -10, 1],
        [10, -10, -1],
        [-10, 10, 1],
        [-10, 10, -1],
        [-10, -10, 1],
        [-10, -10, -1],
        [0, 10, 0],
        [0, -10, 0],
        [0, 10, 1],
        [0, 10, -1],
        [0, -10, 1],
        [0, -10, -1],
        [0, 0, 1],
        [0, 0, -1],
        [10, 0, 1],
        [10, 0, -1],
        [-10, 0, 1],
        [-10, 1, -1],
    ]
)

# inicializar tabla Q
Q = np.zeros((625, 6))

# inicializar estados
e1 = np.arange(60, 310, 10)
e2 = np.repeat(e1, 25)
e3 = np.arange(10, 60, 10)
e4 = np.tile(e3, 125)
e5 = np.arange(1, 6, 1)
e6 = np.repeat(e5, 5)
e7 = np.tile(e6, 25)
e8 = np.column_stack((e2, e4))
S = np.column_stack((e8, e7))  # 625 estados


# funcion elegir accion
def elegir_accion(fila):
    p = np.random.random()
    if p < (1 - epsilon):
        i = np.argmax(Q[fila, :])
    else:
        i = np.random.choice(6)
    return i


# Funcion que retorna la ruta del archivo completa
# Parametro de entrada: nombre del archivo
# Retorno: ruta del archivo
def get_path(madel_name):
    path = os.getcwd() + "\\" + madel_name
    print((os.getcwd()))
    return path


# Funcion que retorna el objeto de conexion
# Parametro de entrada: nombre del archivo
# Retorno: objeto de conexion
def open_model(madel_name):
    com_obj = win32.Dispatch("Tecnomatix.PlantSimulation.RemoteControl.15.0")
    com_obj.setVisible(True)
    com_obj.loadModel(get_path(madel_name))
    print(("Path model: " + get_path(madel_name)))
    return com_obj

def data_table_names(plant_sim):
    var_list = []
    for vl in range(1,10):
        if plant_sim.Models.Modelo.Class.Value == "InformationFlow.DataTable":
            var_list.append(plant_sim.Models.Modelo.Name)
        else:
        	break
    print(var_list)
#Models = ".Models.Model.InformationFlow.DataTable"


# funcion buscar resultado de la simulacion
def buscar_res(plant_sim, estado):
    plant_sim.setValue(".Models.Modelo.espera", estado[0])
    plant_sim.setValue(".Models.Modelo.stock", estado[1])
    plant_sim.setValue(".Models.Modelo.numviajes", estado[2])
    plant_sim.startSimulation(".Models.Modelo")

    a = np.zeros(9)
    b = np.zeros(20)
    c = np.zeros(20)
    for g in range(1, 10):
        a[g - 1] = plant_sim.getValue(".Models.Modelo.transportes[2,%s]" % (g))
    for h in range(1, 21):
        b[h - 1] = plant_sim.getValue(".Models.Modelo.buffers[3,%s]" % (h))
        c[h - 1] = plant_sim.getValue(".Models.Modelo.salidas[2,%s]" % (h))
    d = np.sum(a)
    e = np.sum(b)
    f = np.sum(c)
    r = d * 0.2 + e * 0.3 + f * 0.5

    plant_sim.resetSimulation(".Models.Modelo")
    return (r, d, e, f)


# funcion rl- actualizar estados y matriz Q
def rl(plant_sim):
    for n in range(ep_maximo):
        S0 = S[0]
        t = 0
        r_acum = 0
        res0, v1, v2, v3 = buscar_res(plant_sim, S0)
        r_t = v1
        r_b = v2
        r_s = v3
        r_tot = res0
        while t < t_maximo:
            # buscar indice k del estado actual
            for k in range(625):
                if S[k][0] == S0[0]:
                    if S[k][1] == S0[1]:
                        if S[k][2] == S0[2]:
                            break
            # elegir accion de la fila k
            j = elegir_accion(k)
            # actualizar estado
            Snew = S0 + acciones[j]
            # limites
            if Snew[0] > 300:
                Snew[0] -= 10
            elif Snew[0] < 60:
                Snew[0] += 10
            elif Snew[1] > 50:
                Snew[1] -= 10
            elif Snew[1] < 10:
                Snew[1] += 10
            elif Snew[2] > 5:
                Snew[2] -= 1
            elif Snew[2] < 1:
                Snew[2] += 1
            # actualizar resultado simulacion
            res1, v4, v5, v6 = buscar_res(plant_sim, Snew)
            # recompensa
            if res1 < res0:
                r = 1
            else:
                r = 0
            # buscar indice del estado nuevo S'
            for l in range(625):
                if S[l][0] == Snew[0]:
                    if S[l][1] == Snew[1]:
                        if S[l][2] == Snew[2]:
                            break
            # actualizar matriz Q
            Q[k, j] = Q[k, j] + alfa * (r + gamma * np.max(Q[l, :]) - Q[k, j])
            # actualizar parametros
            t += 1
            S0 = Snew
            res0 = res1
            r_acum = r_acum + r
            r_t = r_t + v4
            r_b = r_t + v5
            r_s = r_t + v6
            r_tot = r_tot + res1
        r_transportes[n] = r_t / t_maximo
        r_buffers[n] = r_b / t_maximo
        r_salidas[n] = r_s / t_maximo
        r_total[n] = r_tot / t_maximo
        r_episodio[n] = r_acum


def plant_simulation():
    model = "MaterialHandling.spp"
    plant_sim = open_model(model)
    data_table_names(plant_sim)
    rl(plant_sim)

    # resultados
    plt.plot(r_episodio, "b-")
    plt.axis([0, ep_maximo, 0, t_maximo])
    plt.title("Recompensa acumulada por episodio")
    plt.xlabel("Numero de episodios")
    plt.ylabel("R acumulada")
    plt.show()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, constrained_layout=True)
    ax1.plot(r_transportes, "r-")
    ax1.set(title="Resultados a minimizar", ylabel="Transportes", ylim=(0, 2))
    ax2.plot(r_buffers, "b-")
    ax2.set(ylabel="Buffers", ylim=(0, 2))
    ax3.plot(r_salidas, "g-")
    ax3.set(xlabel="Numero de episodios", ylabel="Salidas", ylim=(0, 2))
    plt.show()

    plt.plot(r_total, "b-")
    plt.axis([0, ep_maximo, 0, 4])
    plt.title("Resultado total a minimizar")
    plt.xlabel("Numero de episodios")
    plt.ylabel("Resultado")
    plt.show()


if __name__ == "__main__":
    plant_simulation()
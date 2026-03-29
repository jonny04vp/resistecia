import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

# Configuración inicial
st.set_page_config(page_title="Calculadora Pro: Vigas y Esfuerzos", layout="wide")
st.title("🚀 Análisis Estructural Completo: Vigas & Sección T")
st.markdown("Cálculo de Reacciones, Esfuerzos Internos, Deflexión y Esfuerzo Normal ($\sigma$).")

# ==========================================
# --- BARRA LATERAL: ENTRADA DE DATOS ---
# ==========================================
st.sidebar.header("1. Geometría y Apoyos")
L = st.sidebar.number_input("Longitud total L (m)", value=5.0, min_value=0.5, step=0.5)

tipo_apoyo = st.sidebar.radio("Tipo de Viga / Apoyos:", [
    "Simplemente Apoyada", 
    "Empotrada (Voladizo)", 
    "Doblemente Empotrada",
    "Empotrada y Apoyada",
    "Múltiples Apoyos (Viga Continua)"
])

supports = {'type': tipo_apoyo}
if tipo_apoyo == "Simplemente Apoyada":
    col_a1, col_a2 = st.sidebar.columns(2)
    supports['xA'] = col_a1.number_input("Posición Apoyo 1 (m)", value=0.0)
    supports['xB'] = col_a2.number_input("Posición Apoyo 2 (m)", value=float(L))
elif tipo_apoyo == "Empotrada (Voladizo)":
    supports['xA'] = st.sidebar.number_input("Posición del Empotramiento (m)", value=0.0)
elif tipo_apoyo == "Doblemente Empotrada":
    supports['xA'], supports['xB'] = 0.0, L
elif tipo_apoyo == "Empotrada y Apoyada":
    col_a1, col_a2 = st.sidebar.columns(2)
    supports['xA'] = col_a1.number_input("Posición Empotramiento (m)", value=0.0)
    supports['xB'] = col_a2.number_input("Posición Apoyo Simple (m)", value=float(L))
elif tipo_apoyo == "Múltiples Apoyos (Viga Continua)":
    num_apoyos = st.sidebar.number_input("Cantidad de apoyos simples", min_value=2, max_value=10, value=3)
    supports['apoyos'] = []
    for i in range(num_apoyos):
        pos_defecto = float(i * L / (num_apoyos - 1)) if num_apoyos > 1 else 0.0
        pos = st.sidebar.number_input(f"Posición Apoyo {i+1} (m)", value=pos_defecto, max_value=float(L), key=f"apoyo_{i}")
        supports['apoyos'].append(pos)

st.sidebar.divider()
st.sidebar.header("2. Propiedades de la Sección")
E = st.sidebar.number_input("Módulo de Elasticidad E (Pa)", value=200e9, format="%.2e")
tipo_seccion = st.sidebar.selectbox("Tipo de Sección:", ["Rectangular", "Circular", "Sección T"])

I = 0.0
y_centroide = 0.0 
h_total = 0.0

if tipo_seccion == "Rectangular":
    b = st.sidebar.number_input("Base b (m)", value=0.1)
    h = st.sidebar.number_input("Altura h (m)", value=0.2)
    I = (b * h**3) / 12.0
    y_centroide = h / 2
    h_total = h
elif tipo_seccion == "Circular":
    d = st.sidebar.number_input("Diámetro d (m)", value=0.15)
    I = (np.pi * d**4) / 64.0
    y_centroide = d / 2
    h_total = d
elif tipo_seccion == "Sección T":
    st.sidebar.subheader("Dimensiones de la T")
    bf = st.sidebar.number_input("Ancho Ala (bf) (m)", value=0.20)
    tf = st.sidebar.number_input("Espesor Ala (tf) (m)", value=0.02)
    hw = st.sidebar.number_input("Altura Alma (hw) (m)", value=0.18)
    tw = st.sidebar.number_input("Espesor Alma (tw) (m)", value=0.02)
    A_ala, A_alma = bf * tf, hw * tw
    y_ala, y_alma = hw + tf/2, hw/2
    y_centroide = (A_ala * y_ala + A_alma * y_alma) / (A_ala + A_alma)
    I = ((bf * tf**3)/12 + A_ala * (y_ala - y_centroide)**2) + ((tw * hw**3)/12 + A_alma * (y_alma - y_centroide)**2)
    h_total = hw + tf

EI = E * I

st.sidebar.divider()
st.sidebar.header("3. Configuración de Cargas")

# --- CARGAS PUNTUALES ---
num_p = st.sidebar.number_input("Nº de cargas puntuales", 0, 5, 1)
cargas_puntuales = []
for i in range(num_p):
    col1, col2 = st.sidebar.columns(2)
    P = col1.number_input(f"P{i+1} (N)", value=5000.0, key=f"P_{i}")
    pos = col2.number_input(f"x_p{i+1}", value=L/2, key=f"Px_{i}")
    cargas_puntuales.append((P, pos))

# --- MOMENTOS CONCENTRADOS ---
num_m = st.sidebar.number_input("Nº de momentos concentrados", 0, 3, 0)
momentos_concentrados = []
for i in range(num_m):
    col1, col2 = st.sidebar.columns(2)
    M_val = col1.number_input(f"M{i+1} (N·m)", value=1000.0, key=f"M_{i}")
    pos_m = col2.number_input(f"x_m{i+1}", value=L/2, key=f"Mx_{i}")
    momentos_concentrados.append((M_val, pos_m))

# --- CARGAS UNIFORMES ---
num_qu = st.sidebar.number_input("Nº de cargas uniformes", 0, 3, 0)
cargas_uniformes = []
for i in range(num_qu):
    st.sidebar.markdown(f"**Rectangular {i+1}**")
    q = st.sidebar.number_input(f"q (N/m)", value=2000.0, key=f"qu_v_{i}")
    col1, col2 = st.sidebar.columns(2)
    xi = col1.number_input(f"Inicio (m)", value=0.0, key=f"qu_xi_{i}")
    xf = col2.number_input(f"Fin (m)", value=float(L), key=f"qu_xf_{i}")
    if xf > xi: cargas_uniformes.append((q, xi, xf))

# --- CARGAS TRIANGULARES ---
num_qt = st.sidebar.number_input("Nº de cargas triangulares", 0, 3, 0)
cargas_triangulares = []
for i in range(num_qt):
    st.sidebar.markdown(f"**Triangular {i+1}**")
    q_max = st.sidebar.number_input(f"q_max (N/m)", value=3000.0, key=f"qt_v_{i}")
    col1, col2 = st.sidebar.columns(2)
    xi = col1.number_input(f"Inicio (m)", value=0.0, key=f"qti_{i}")
    xf = col2.number_input(f"Fin (m)", value=float(L), key=f"qtf_{i}")
    if xf > xi: cargas_triangulares.append((q_max, xi, xf))

# ==========================================
# --- MOTOR DE CÁLCULO NUMÉRICO Y MATRICIAL ---
# ==========================================
N = 1000
x = np.linspace(0, L, N)
dx = L / (N - 1)

F_y_cargas, M_0_cargas = 0.0, 0.0
M_loads = np.zeros_like(x)

for P, pos in cargas_puntuales:
    F_y_cargas -= P
    M_0_cargas -= P * pos
    M_loads += np.where(x > pos, -P * (x - pos), 0)

for M_c, pos in momentos_concentrados:
    M_0_cargas -= M_c
    M_loads += np.where(x >= pos, M_c, 0)

for q, a, b in cargas_uniformes:
    W = q * (b - a); cg = (a + b) / 2
    F_y_cargas -= W; M_0_cargas -= W * cg
    M_loads += np.where((x > a) & (x <= b), -q * (x - a)**2 / 2, 0)
    M_loads += np.where(x > b, -W * (x - cg), 0)

for q0, a, b in cargas_triangulares:
    W = 0.5 * q0 * (b - a); cg = a + (2/3) * (b - a)
    F_y_cargas -= W; M_0_cargas -= W * cg
    m_slope = q0 / (b - a)
    M_loads += np.where((x > a) & (x <= b), -m_slope * (x - a)**3 / 6, 0)
    M_loads += np.where(x > b, -W * (x - cg), 0)

# --- SISTEMA DE RESOLUCIÓN GENERAL ---
unknowns = []
bc_eqs = []

if supports['type'] == "Simplemente Apoyada":
    unknowns.extend([{'type': 'Ry', 'pos': supports['xA']}, {'type': 'Ry', 'pos': supports['xB']}])
    bc_eqs.extend([{'type': 'v', 'pos': supports['xA']}, {'type': 'v', 'pos': supports['xB']}])
elif supports['type'] == "Empotrada (Voladizo)":
    unknowns.extend([{'type': 'Ry', 'pos': supports['xA']}, {'type': 'M', 'pos': supports['xA']}])
    bc_eqs.extend([{'type': 'v', 'pos': supports['xA']}, {'type': 'theta', 'pos': supports['xA']}])
elif supports['type'] == "Doblemente Empotrada":
    unknowns.extend([{'type': 'Ry', 'pos': 0.0}, {'type': 'M', 'pos': 0.0}, {'type': 'Ry', 'pos': L}, {'type': 'M', 'pos': L}])
    bc_eqs.extend([{'type': 'v', 'pos': 0.0}, {'type': 'theta', 'pos': 0.0}, {'type': 'v', 'pos': L}, {'type': 'theta', 'pos': L}])
elif supports['type'] == "Empotrada y Apoyada":
    unknowns.extend([{'type': 'Ry', 'pos': supports['xA']}, {'type': 'M', 'pos': supports['xA']}, {'type': 'Ry', 'pos': supports['xB']}])
    bc_eqs.extend([{'type': 'v', 'pos': supports['xA']}, {'type': 'theta', 'pos': supports['xA']}, {'type': 'v', 'pos': supports['xB']}])
elif supports['type'] == "Múltiples Apoyos (Viga Continua)":
    for pos in supports['apoyos']:
        unknowns.append({'type': 'Ry', 'pos': pos})
        bc_eqs.append({'type': 'v', 'pos': pos})

def get_v_theta_unit_F(a):
    M_u = np.where(x > a, x - a, 0)
    th_u = np.cumsum(M_u) * dx / EI
    v_u = np.cumsum(th_u) * dx
    return v_u, th_u

def get_v_theta_unit_M(a):
    M_u = np.where(x >= a, 1, 0)
    th_u = np.cumsum(M_u) * dx / EI
    v_u = np.cumsum(th_u) * dx
    return v_u, th_u

theta_loads = np.cumsum(M_loads) * dx / EI
v_loads = np.cumsum(theta_loads) * dx

N_eq = len(unknowns) + 2
A_mat = np.zeros((N_eq, N_eq))
B_vec = np.zeros(N_eq)

for j, unk in enumerate(unknowns):
    if unk['type'] == 'Ry': A_mat[0, j] = 1
B_vec[0] = -F_y_cargas

for j, unk in enumerate(unknowns):
    if unk['type'] == 'Ry': A_mat[1, j] = unk['pos']
    elif unk['type'] == 'M': A_mat[1, j] = 1
B_vec[1] = -M_0_cargas

unit_arrays = []
for unk in unknowns:
    if unk['type'] == 'Ry': unit_arrays.append(get_v_theta_unit_F(unk['pos']))
    elif unk['type'] == 'M': unit_arrays.append(get_v_theta_unit_M(unk['pos']))

for i, bc in enumerate(bc_eqs):
    row = i + 2
    idx = np.argmin(np.abs(x - bc['pos']))
    for j, unk in enumerate(unknowns):
        v_u, th_u = unit_arrays[j]
        A_mat[row, j] = v_u[idx] if bc['type'] == 'v' else th_u[idx]
    
    if bc['type'] == 'v':
        A_mat[row, -2] = x[idx] 
        A_mat[row, -1] = 1      
        B_vec[row] = -v_loads[idx]
    else:
        A_mat[row, -2] = 1
        A_mat[row, -1] = 0
        B_vec[row] = -theta_loads[idx]

try:
    X_sol = np.linalg.solve(A_mat, B_vec)
except np.linalg.LinAlgError:
    st.error("Error: Sistema inestable o redundante. Verifica que los apoyos no estén en la misma posición.")
    st.stop()

reacciones_fuerza = []
reacciones_momento = []
for j, unk in enumerate(unknowns):
    if unk['type'] == 'Ry': reacciones_fuerza.append((X_sol[j], unk['pos']))
    elif unk['type'] == 'M': reacciones_momento.append((X_sol[j], unk['pos']))

C1, C2 = X_sol[-2], X_sol[-1]

V_x, M_x = np.zeros_like(x), np.copy(M_loads)
for R, pos in reacciones_fuerza:
    V_x += np.where(x > pos, R, 0)
    M_x += np.where(x > pos, R * (x - pos), 0)
for M_R, pos in reacciones_momento:
    M_x += np.where(x >= pos, M_R, 0)
for P, pos in cargas_puntuales:
    V_x += np.where(x > pos, -P, 0)
for q, a, b in cargas_uniformes:
    V_x += np.where((x > a) & (x <= b), -q * (x - a), 0)
    V_x += np.where(x > b, -q * (b - a), 0)
for q0, a, b in cargas_triangulares:
    m_s = q0 / (b - a)
    V_x += np.where((x > a) & (x <= b), -m_s * (x - a)**2 / 2, 0)
    V_x += np.where(x > b, -0.5 * q0 * (b - a), 0)

theta_raw = np.cumsum(M_x) * dx / EI
v_raw = np.cumsum(theta_raw) * dx

v = v_raw + C1 * x + C2
theta = theta_raw + C1

# ==========================================
# --- VISUALIZACIÓN ---
# ==========================================
st.sidebar.divider()
st.sidebar.header("4. Punto de Análisis")
x_eval = st.sidebar.slider("Punto x (m)", 0.0, float(L), float(L/2))
y_max_top, y_max_bot = h_total - y_centroide, -y_centroide
y_fiber = st.sidebar.slider("Fibra y (m desde E.N.)", float(y_max_bot), float(y_max_top), float(y_max_top))

idx_ev = np.argmin(np.abs(x - x_eval))
sigma_x = -(M_x[idx_ev] * y_fiber) / I

M_max_abs = np.max(np.abs(M_x))
c_max = max(abs(y_max_top), abs(y_max_bot))
sigma_max_abs = (M_max_abs * c_max) / I

st.markdown("### 📊 Resultados Globales Máximos")
col_g1, col_g2, col_g3 = st.columns(3)
col_g1.metric("Momento Flector Máx", f"{M_max_abs:.2f} N·m")
col_g2.metric("Esfuerzo Normal Máx (σ)", f"{sigma_max_abs/1e6:.3f} MPa")
col_g3.metric("Deflexión Máxima", f"{np.max(np.abs(v))*1000:.3f} mm")

st.markdown(f"### 📍 Resultados en el Punto Analizado (x = {x_eval:.2f} m)")
col_l1, col_l2, col_l3 = st.columns(3)
col_l1.metric("Deflexión local (y)", f"{v[idx_ev]*1000:.3f} mm")
col_l2.metric("Ángulo de Giro (θ)", f"{np.degrees(theta[idx_ev]):.4f}°")
col_l3.metric("Esfuerzo en fibra seleccionada (σ)", f"{sigma_x/1e6:.3f} MPa")

st.divider()

# --- TABS GRÁFICOS INCLUYENDO LA NUEVA ANIMACIÓN ---
tabs = st.tabs(["Diagrama Físico (DCL)", "Diagramas V-M", "Sección y Esfuerzos", "Deflexión", "Animación 🎬"])

with tabs[0]:
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.add_patch(patches.Rectangle((0, -0.1), L, 0.2, facecolor='lightgray', edgecolor='black', lw=2))
    
    ax1.axvline(x_eval, color='blue', ls='--', alpha=0.6, label='Análisis x')
    ax1.plot(x_eval, 0, 'ob', ms=6) 

    if supports['type'] == "Simplemente Apoyada":
        ax1.add_patch(patches.Polygon([[supports['xA'], -0.1], [supports['xA']-0.03*L, -0.4], [supports['xA']+0.03*L, -0.4]], color='black'))
        ax1.add_patch(patches.Circle((supports['xB'], -0.25), 0.05*L, color='black', fill=False, lw=2))
    elif supports['type'] == "Empotrada (Voladizo)":
        ax1.plot([supports['xA'], supports['xA']], [-0.5, 0.5], color='black', lw=4)
    elif supports['type'] == "Doblemente Empotrada":
        ax1.plot([0, 0], [-0.5, 0.5], color='black', lw=4); ax1.plot([L, L], [-0.5, 0.5], color='black', lw=4)
    elif supports['type'] == "Empotrada y Apoyada":
        ax1.plot([supports['xA'], supports['xA']], [-0.5, 0.5], color='black', lw=4)
        ax1.add_patch(patches.Polygon([[supports['xB'], -0.1], [supports['xB']-0.03*L, -0.4], [supports['xB']+0.03*L, -0.4]], color='black'))
    elif supports['type'] == "Múltiples Apoyos (Viga Continua)":
        for pos in supports['apoyos']:
            ax1.add_patch(patches.Polygon([[pos, -0.1], [pos-0.03*L, -0.4], [pos+0.03*L, -0.4]], color='black'))

    for P, pos in cargas_puntuales: 
        ax1.arrow(pos, 0.7, 0, -0.4, head_width=0.03*L, head_length=0.1, fc='red', ec='red', lw=2)
        ax1.text(pos, 0.8, f"{P}N", color='red', ha='center', fontsize=9, fontweight='bold')
    for M_c, pos in momentos_concentrados: 
        ax1.plot(pos, 0, 'oy', ms=8)
        ax1.text(pos, 0.2, f"{M_c}Nm", color='orange', ha='center', fontweight='bold')
    for q, a, b in cargas_uniformes: 
        ax1.add_patch(patches.Rectangle((a, 0.1), b-a, 0.3, facecolor='blue', alpha=0.3))
        ax1.text((a+b)/2, 0.45, f"q={q}N/m", color='blue', ha='center', fontsize=9, fontweight='bold')
    for q0, a, b in cargas_triangulares: 
        ax1.add_patch(patches.Polygon([[a, 0.1], [b, 0.1], [b, 0.4]], color='red', alpha=0.3))
        ax1.text(b, 0.45, f"qmax={q0}N/m", color='red', ha='right', fontsize=9, fontweight='bold')
    for R, pos in reacciones_fuerza: 
        ax1.arrow(pos, -0.8, 0, 0.4 if R>0 else -0.4, head_width=0.03*L, head_length=0.1, fc='green', ec='green', lw=3)
        ax1.text(pos, -1.0, f"R={R:.2f}N", color='green', ha='center', fontweight='bold', fontsize=9)
    for M_R, pos in reacciones_momento: 
        sentido = "↺" if M_R > 0 else "↻"
        ax1.text(pos, -1.3, f"M={abs(M_R):.1f}N·m {sentido}", color='purple', ha='center', fontweight='bold')

    ax1.set_xlim(-0.1 * L, 1.1 * L); ax1.set_ylim(-1.5, 1.5); ax1.axis('off')
    st.pyplot(fig1)

with tabs[1]:
    fig2, (axv, axm) = plt.subplots(2, 1, figsize=(10, 6))
    axv.plot(x, V_x, color='teal', lw=2); axv.axvline(x_eval, color='blue', ls=':'); axv.set_ylabel("V (N)")
    axm.plot(x, M_x, color='crimson', lw=2); axm.axvline(x_eval, color='blue', ls=':'); axm.set_ylabel("M (N·m)")
    st.pyplot(fig2)

with tabs[2]:
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        fig_s, axs = plt.subplots(figsize=(4, 5))
        if tipo_seccion == "Sección T":
            axs.add_patch(patches.Rectangle((-tw/2, 0), tw, hw, fc='gray', ec='black'))
            axs.add_patch(patches.Rectangle((-bf/2, hw), bf, tf, fc='gray', ec='black'))
        elif tipo_seccion == "Rectangular":
            axs.add_patch(patches.Rectangle((-b/2, 0), b, h, fc='gray', ec='black'))
        elif tipo_seccion == "Circular":
            axs.add_patch(patches.Circle((0, d/2), d/2, fc='gray', ec='black'))
        
        axs.axhline(y_centroide, color='red', ls='--', label='E.N.')
        axs.plot(0, y_centroide + y_fiber, 'ob', ms=10, label='Fibra analizada')
        axs.set_xlim(-0.3, 0.3); axs.set_ylim(-0.01, h_total+0.05); axs.legend(); st.pyplot(fig_s)
    with c_s2:
        y_p = np.linspace(y_max_bot, y_max_top, 50)
        sig_p = -(M_x[idx_ev] * y_p) / I / 1e6
        fig_sig, axsig = plt.subplots()
        axsig.plot(sig_p, y_p + y_centroide, color='purple', lw=2); axsig.axvline(0, color='black')
        axsig.fill_betweenx(y_p + y_centroide, sig_p, 0, alpha=0.2, color='purple')
        axsig.set_xlabel("Esfuerzo σ (MPa)"); axsig.set_ylabel("Altura (m)"); st.pyplot(fig_sig)

with tabs[3]:
    fig_d, axd = plt.subplots(figsize=(10, 3))
    # Ya no se usa invert_yaxis() -> Si v es negativa (hacia abajo), se grafica hacia abajo.
    axd.plot(x, v*1000, color='blue', lw=2); axd.axvline(x_eval, color='blue', ls=':')
    axd.grid(True, ls=':'); axd.set_ylabel("Deflexión y (mm)"); st.pyplot(fig_d)

# --- ANIMACIÓN ---
with tabs[4]:
    st.subheader("🎬 Animación de Deformación Progresiva")
    st.markdown("Observa cómo se flexiona la viga desde el 0% hasta alcanzar el 100% de las cargas aplicadas.")
    
    if st.button("▶ Iniciar Animación", type="primary"):
        anim_placeholder = st.empty()
        frames = 30
        
        # Encontrar límites fijos para que el gráfico no salte durante la animación
        max_deflex_abs = np.max(np.abs(v)) * 1000
        y_lim = max_deflex_abs * 1.5 if max_deflex_abs > 0 else 1.0
        
        for i in range(frames + 1):
            factor = i / frames
            fig_anim, ax_anim = plt.subplots(figsize=(10, 3))
            
            # Dibujar línea recta original
            ax_anim.plot([0, L], [0, 0], color='gray', lw=2, ls='--')
            
            # Dibujar la viga deformándose escalada por el factor
            # (Sin invert_yaxis para que caiga hacia los negativos correctamente)
            ax_anim.plot(x, v * 1000 * factor, color='blue', lw=3, label=f'Carga al {int(factor*100)}%')
            
            # Dibujar los apoyos
            if supports['type'] == "Simplemente Apoyada":
                ax_anim.plot(supports['xA'], 0, '^k', ms=10)
                ax_anim.plot(supports['xB'], 0, '^k', ms=10)
            elif supports['type'] == "Empotrada (Voladizo)":
                ax_anim.plot([supports['xA'], supports['xA']], [-y_lim, y_lim], 'k', lw=4)
            elif supports['type'] == "Doblemente Empotrada":
                ax_anim.plot([0, 0], [-y_lim, y_lim], 'k', lw=4)
                ax_anim.plot([L, L], [-y_lim, y_lim], 'k', lw=4)
            elif supports['type'] == "Empotrada y Apoyada":
                ax_anim.plot([supports['xA'], supports['xA']], [-y_lim, y_lim], 'k', lw=4)
                ax_anim.plot(supports['xB'], 0, '^k', ms=10)
            elif supports['type'] == "Múltiples Apoyos (Viga Continua)":
                for pos in supports['apoyos']:
                    ax_anim.plot(pos, 0, '^k', ms=10)
            
            ax_anim.set_xlim(-0.1 * L, 1.1 * L)
            ax_anim.set_ylim(-y_lim, y_lim) 
            ax_anim.set_xlabel("Posición x (m)")
            ax_anim.set_ylabel("Deflexión y (mm)")
            ax_anim.grid(True, ls=':')
            ax_anim.legend(loc="upper right")
            
            anim_placeholder.pyplot(fig_anim)
            plt.close(fig_anim)
            time.sleep(0.05)
        
        st.success("✅ ¡Animación completada!")
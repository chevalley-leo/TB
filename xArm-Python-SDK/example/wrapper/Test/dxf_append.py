import sys
sys.path.append('/home/leshauts/.local/lib/python3.12/site-packages')
from xarm.wrapper import XArmAPI
import ezdxf
import math
import matplotlib
matplotlib.use('Agg')  # Utilisation d'un backend non interactif
import matplotlib.pyplot as plt
import numpy as np
from xarm.wrapper import XArmAPI
import time

# Paramètres
Z_DRAW = 100     # Hauteur de dessin
Z_UP = 103        # Hauteur quand le stylo est levé
SCALE_FACTOR = 0.3  # Facteur d'échelle

# Connexion au robot
arm = XArmAPI('192.168.1.215', baud_checkset=False)

# Initialisation du robot
arm.clean_warn()
arm.clean_error()
arm.motion_enable(True)
arm.set_mode(0)
arm.set_state(0)
arm.set_tcp_jerk(10000)
arm.set_tcp_jerk(500)

# Paramètres du robot
TCP_SPEED = 100
TCP_ACC = 50000

def apply_offset(x, y, offset_x=200, offset_y=600):
    """Applique un offset aux coordonnées x et y."""
    return x * SCALE_FACTOR + offset_x, y * SCALE_FACTOR + offset_y

def process_dxf(dxf_file):
    """Lit un fichier DXF et génère une liste ordonnée de positions (x, y, z)."""
    doc = ezdxf.readfile(dxf_file)
    msp = doc.modelspace()
    
    trajectory = []
    last_point = None  # Dernier point traité
    
    for entity in msp:
        entity_points = []

        if entity.dxftype() == "LINE":
            p1 = apply_offset(entity.dxf.start.x, entity.dxf.start.y)
            p2 = apply_offset(entity.dxf.end.x, entity.dxf.end.y)
            entity_points = [p1, p2]

        elif entity.dxftype() == "LWPOLYLINE":
            entity_points = [apply_offset(p[0], p[1]) for p in entity.get_points("xy")]

        elif entity.dxftype() == "CIRCLE":
            cx, cy = apply_offset(entity.dxf.center.x, entity.dxf.center.y)
            r = entity.dxf.radius * SCALE_FACTOR
            num_points = 36
            entity_points = [
                (cx + r * math.cos(2 * math.pi * i / num_points),
                 cy + r * math.sin(2 * math.pi * i / num_points))
                for i in range(num_points + 1)
            ]

        elif entity.dxftype() == "ARC":
            cx, cy = apply_offset(entity.dxf.center.x, entity.dxf.center.y)
            r = entity.dxf.radius * SCALE_FACTOR
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            num_points = 20
            entity_points = [
                (cx + r * math.cos(start_angle + (end_angle - start_angle) * i / num_points),
                 cy + r * math.sin(start_angle + (end_angle - start_angle) * i / num_points))
                for i in range(num_points + 1)
            ]

        # Gestion du levé/stylo
        if entity_points:
            first_point = entity_points[0]
            if last_point is None or last_point != first_point:
                trajectory.append((last_point[0], last_point[1], Z_UP) if last_point else None)  # Lever le stylo
                trajectory.append((first_point[0], first_point[1], Z_UP))  # Déplacement au-dessus du point
                trajectory.append((first_point[0], first_point[1], Z_DRAW))  # Redescente

            for point in entity_points:
                trajectory.append((*point, Z_DRAW))  # Tracer

            last_point = entity_points[-1]

    return [p for p in trajectory if p is not None]

def plot_trajectory_3d(trajectory):
    """Affiche la trajectoire en 3D avec un dégradé de couleurs."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Extraire les coordonnées
    x_vals, y_vals, z_vals = zip(*trajectory)

    # Création du dégradé de couleurs
    num_points = len(trajectory)
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(0, num_points - 1)
    colors = [cmap(norm(i)) for i in range(num_points)]

    # Tracé avec couleur progressive
    for i in range(len(x_vals) - 1):
        ax.plot(x_vals[i:i+2], y_vals[i:i+2], z_vals[i:i+2], color=colors[i])

    # Labels et affichage
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Trajectoire 3D du Robot")
    plt.show()
    plt.savefig("trajectory3d.png")




import matplotlib.pyplot as plt

def plot_trajectory_2d(trajectory):
    """Affiche uniquement les parties de la trajectoire où Z < 3 (contact avec la surface)."""
    x_vals = []
    y_vals = []
    
    for i in range(len(trajectory)):
        x, y, z = trajectory[i]
        if z < 103:
            x_vals.append(x)
            y_vals.append(y)
        else:
            # Ajoute une rupture dans le tracé pour éviter des traits entre segments
            x_vals.append(None)
            y_vals.append(None)

    plt.figure(figsize=(8, 8))  # Taille du graphique ajustée
    plt.plot(x_vals, y_vals, marker='.', markersize=1, linestyle='-', linewidth=0.5, color='b', alpha=0.8)  
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Dessin Final (Seulement Z < 3)")
    plt.axis("equal")
    plt.grid(True, linewidth=0.3)

    # Sauvegarde au lieu d'afficher (évite les erreurs en SSH)
    plt.savefig("trajectory2d.png", dpi=300)
    plt.close()
    print("✅ Dessin final enregistré en 'drawing_final_2d.png'")

def move_to_position(x,y,z):
    """Déplace le robot à une position (x, y, z) donnée."""

    if z == Z_UP:
        arm.set_cgpio_digital(0, 1)
        arm.set_cgpio_analog(0, 0)

    else:
        arm.set_cgpio_digital(0, 0)
        arm.set_cgpio_analog(0, 5)


    arm.set_position(x, y, z, 0, 90, 90, wait=False, speed=TCP_SPEED, mvacc=TCP_ACC, radius=0)


# Exécution
dxf_file = "genevepapa.dxf"
trajectory = process_dxf(dxf_file)

# Affichage des points générés
for point in trajectory:
    print(point)

# Affichage en 3D
plot_trajectory_3d(trajectory)
plot_trajectory_2d(trajectory)


for x, y, z in trajectory:
    move_to_position(x, y, z)   # Déplacement du robot


# Retour à la position initiale
move_to_position(200, 600, Z_UP)

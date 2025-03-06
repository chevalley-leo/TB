from xarm.wrapper import XArmAPI
import time
import ezdxf
import math
import matplotlib
matplotlib.use('Agg')  # Utilisation du backend non interactif pour l'enregistrement d'image
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

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

time.sleep(1)

# Paramètres du robot
TCP_SPEED = 100
TCP_ACC = 50000
Z_HEIGHT = 100  # Hauteur de sécurité

# Position de base
BASE_X_OFFSET = 200
BASE_Y_OFFSET = 600

# Charger le fichier DXF
dxf_file = "coeur.dxf"  # Remplace par ton fichier
doc = ezdxf.readfile(dxf_file)
msp = doc.modelspace()

# Facteur d'échelle pour ajuster la taille du dessin
scale_factor = 1

# Liste pour stocker la trajectoire
trajectory = []



def apply_offset(x, y):
    """Applique l'offset aux coordonnées x et y."""
    return x + BASE_X_OFFSET, y + BASE_Y_OFFSET

def move_to_position(x, y):
    """Déplace le robot à la position spécifiée et enregistre la trajectoire."""
    print(f"Déplacement à",x,y,Z_HEIGHT)
    trajectory.append((x, y, Z_HEIGHT))
    arm.set_position(x, y, Z_HEIGHT, 0.0, 90.0, 90.0, speed=TCP_SPEED, mvacc=TCP_ACC, radius=0, wait=False)


def process_lwpolyline(polyline):
    """Reconstruit correctement une LWPOLYLINE avec segments droits et arcs."""
    points = polyline.get_points('xyb')  # Récupérer x, y et bulge
    num_points = len(points)

    if num_points < 2:
        return  # Rien à tracer

    # Déplacer au premier point
    x_start, y_start = apply_offset(points[0][0] * scale_factor, points[0][1] * scale_factor)
    move_to_position(x_start, y_start)
    print(f"Déplacement au point de départ : {x_start}, {y_start}")

    # Traiter chaque segment
    for i in range(num_points - 1):
        x1, y1, bulge = points[i]
        x2, y2, _ = points[i + 1]
        x1, y1 = apply_offset(x1 * scale_factor, y1 * scale_factor)
        x2, y2 = apply_offset(x2 * scale_factor, y2 * scale_factor)

        if bulge == 0:
            # Segment droit
            print(f"Dessin d'un segment droit de ({x1}, {y1}) à ({x2}, {y2})")
            move_to_position(x2, y2)
        else:
            # Arc
            print(f"Dessin d'un arc de ({x1}, {y1}) à ({x2}, {y2}) avec bulge={bulge}")
            arc_points = calculate_arc(x1, y1, x2, y2, bulge)
            for x, y in arc_points:
                move_to_position(x, y)

    # Fermer la polyligne si nécessaire
    if polyline.is_closed:
        print("Fermeture de la polyligne...")
        last_point = points[-1]
        x_last, y_last = apply_offset(last_point[0] * scale_factor, last_point[1] * scale_factor)

        # Si le dernier segment est un arc, le traiter aussi
        if last_point[2] != 0:
            arc_points = calculate_arc(x_last, y_last, x_start, y_start, last_point[2])
            for x, y in arc_points:
                move_to_position(x, y)

        # Revenir au premier point
        move_to_position(x_start, y_start)


def calculate_arc(x1, y1, x2, y2, bulge):
    """Calcule les points intermédiaires d'un arc défini par un bulge."""
    num_segments = 30  # Ajustable pour lisser l'arc
    arc_points = []

    # Calcul de l'angle et du rayon
    bulge_angle = math.atan(bulge) * 4  # Angle central
    chord_length = math.hypot(x2 - x1, y2 - y1)
    radius = chord_length / (2 * math.sin(bulge_angle / 2))

    # Calcul du centre du cercle
    chord_mid_x = (x1 + x2) / 2
    chord_mid_y = (y1 + y2) / 2
    height = abs(radius * math.cos(bulge_angle / 2))  # Hauteur depuis le milieu de la corde

    # Déterminer la direction perpendiculaire correcte
    dx, dy = x2 - x1, y2 - y1
    norm = math.sqrt(dx**2 + dy**2)
    perp_x, perp_y = -dy / norm, dx / norm  # Vecteur perpendiculaire normalisé

    # Déterminer de quel côté est le centre du cercle
    center_x = chord_mid_x + height * perp_x * (-1 if bulge < 0 else 1)
    center_y = chord_mid_y + height * perp_y * (-1 if bulge < 0 else 1)

    # Calculer les angles de départ et de fin
    start_angle = math.atan2(y1 - center_y, x1 - center_x)
    end_angle = math.atan2(y2 - center_y, x2 - center_x)

    # Ajuster la direction de l'arc si nécessaire
    if bulge > 0 and end_angle < start_angle:
        end_angle += 2 * math.pi
    elif bulge < 0 and end_angle > start_angle:
        start_angle += 2 * math.pi

    # Générer les points de l'arc
    for i in range(1, num_segments):
        angle = start_angle + (end_angle - start_angle) * (i / num_segments)
        arc_x = center_x + radius * math.cos(angle)
        arc_y = center_y + radius * math.sin(angle)
        arc_points.append((arc_x, arc_y))

    arc_points.append((x2, y2))  # Ajouter le point final de l'arc
    return arc_points


def plot_trajectory_3d_with_gradient(trajectory):
    """Affiche la trajectoire du robot en 3D avec un dégradé de couleurs."""
    # Normalisation des points pour l'ordre des trajectoires
    num_points = len(trajectory)
    norm = plt.Normalize(0, num_points - 1)  # Normalisation de l'ordre des points
    cmap = plt.get_cmap('viridis')  # Choix du dégradé de couleurs (par exemple 'viridis')

    # Extraire les coordonnées pour le plot
    x_vals, y_vals, z_vals = zip(*trajectory)

    # Créer la figure en 3D
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Tracer les points et appliquer les couleurs
    for i, (x, y, z) in enumerate(trajectory):
        ax.scatter(x, y, z, color=cmap(norm(i)), marker='o', s=30)  # Tracer chaque point avec une couleur

    # Tracer la ligne de trajectoire
    ax.plot(x_vals, y_vals, z_vals, marker='', linestyle='-', color='b', alpha=0.7)

    # Ajouter une barre de couleur pour le dégradé
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Pour éviter l'avertissement
    fig.colorbar(sm, ax=ax, orientation='vertical', label='Ordre des points')

    # Labels et titre
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Trajectoire du Robot en 3D")

    # Sauvegarder l'image
    plt.savefig("trajectoire_3d_degrade.png", dpi=300)
    plt.close()
    print("Trajectoire 3D enregistrée en 'trajectoire_3d_degrade.png' 📷")




def plot_trajectory_2d_with_gradient(trajectory):
    """Affiche la trajectoire du robot en 2D avec un dégradé de couleurs et une échelle uniforme."""
    # Normalisation des points pour l'ordre des trajectoires
    num_points = len(trajectory)
    norm = plt.Normalize(0, num_points - 1)  # Normalisation de l'ordre des points
    cmap = plt.get_cmap('viridis')  # Choix du dégradé de couleurs (par exemple 'viridis')

    # Extraire les coordonnées pour le plot
    x_vals, y_vals, _ = zip(*trajectory)  # Ignorer la coordonnée Z pour la 2D

    # Créer la figure en 2D
    fig, ax = plt.subplots()

    # Tracer les points et appliquer les couleurs
    for i, (x, y, _) in enumerate(trajectory):
        ax.scatter(x, y, color=cmap(norm(i)), marker='o', s=30)  # Tracer chaque point avec une couleur

    # Tracer la ligne de trajectoire
    ax.plot(x_vals, y_vals, marker='', linestyle='-', color='b', alpha=0.7)

    # Ajouter une barre de couleur pour le dégradé
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Pour éviter l'avertissement
    fig.colorbar(sm, ax=ax, orientation='vertical', label='Ordre des points')

    # Ajuster l'échelle pour éviter les déformations
    ax.set_aspect('equal', adjustable='box')  # Garder une échelle égale sur les axes

    # Labels et titre
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Trajectoire du Robot en 2D")

    # Sauvegarder l'image
    plt.savefig("trajectoire_2d_degrade.png", dpi=300)
    plt.close()
    print("Trajectoire 2D enregistrée en 'trajectoire_2d_degrade.png' 📷")

print("Dessin du fichier DXF...")
move_to_position(BASE_X_OFFSET, BASE_Y_OFFSET)
print("Déplacement à la position de base...")

# Lire les entités du DXF
for entity in msp:
    if entity.dxftype() == "LINE":
        print("Dessin d'une ligne...")
        x1, y1 = apply_offset(entity.dxf.start.x * scale_factor, entity.dxf.start.y * scale_factor)
        x2, y2 = apply_offset(entity.dxf.end.x * scale_factor, entity.dxf.end.y * scale_factor)

        move_to_position(x1, y1)
        move_to_position(x2, y2)

    elif entity.dxftype() == "ARC":
        print("Dessin d'un arc...")
        cx, cy = apply_offset(entity.dxf.center.x * scale_factor, entity.dxf.center.y * scale_factor)
        radius = entity.dxf.radius * scale_factor
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)

        num_points = 50
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_points)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            move_to_position(x, y)

    elif entity.dxftype() == "CIRCLE":
        print("Dessin d'un cercle...")
        cx, cy = apply_offset(entity.dxf.center.x * scale_factor, entity.dxf.center.y * scale_factor)
        radius = entity.dxf.radius * scale_factor

        num_points = 50
        points = [(cx + radius * math.cos(2 * math.pi * i / num_points),
                   cy + radius * math.sin(2 * math.pi * i / num_points)) for i in range(num_points + 1)]

        move_to_position(points[0][0], points[0][1])

        for x, y in points:
            move_to_position(x, y)

    elif entity.dxftype() == "POINT":
        print("Déplacement vers un point...")
        x, y = apply_offset(entity.dxf.location.x * scale_factor, entity.dxf.location.y * scale_factor )
        print(x,y)
        move_to_position(x, y)

    elif entity.dxftype() == "LWPOLYLINE":
        print("Dessin d'une polyligne...")
        process_lwpolyline(entity)

    elif entity.dxftype() == "SPLINE":
        print("Dessin d'une spline...")

        spline = entity  # L'entité SPLINE d'ezdxf
        num_points = 60  # Nombre de points pour l'interpolation

        # Approximation de la spline en segments droits
        distance_tolerance = 0.1  # Tolérance de distance pour l'approximation
        angle_tolerance = 5  # Tolérance d'angle en degrés (optionnel)
    
        spline_points = list(spline.flattening(distance_tolerance, angle_tolerance, num_points))


        # Appliquer l'offset et dessiner
        first = True
        for x, y, _ in spline_points:  # Les splines peuvent avoir des coordonnées 3D, on ignore Z ici
            x, y = apply_offset(x * scale_factor, y * scale_factor)
            if first:
                move_to_position(x, y)  # Déplacement initial
                first = False
            move_to_position(x, y)

    else:
        print("Entité inconnue:", entity.dxftype())

        

arm.set_position(BASE_X_OFFSET, BASE_Y_OFFSET, Z_HEIGHT, 0.0, 90.0, 90.0, speed=TCP_SPEED, mvacc=TCP_ACC, radius= 0, wait=True)
#move_to_position(BASE_X_OFFSET, BASE_Y_OFFSET)
arm.disconnect()

# Afficher la trajectoire en 3D
#plot_trajectory_3d_with_gradient(trajectory)
plot_trajectory_2d_with_gradient(trajectory)




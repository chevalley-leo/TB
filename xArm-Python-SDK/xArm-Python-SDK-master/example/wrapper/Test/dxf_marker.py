import time
import ezdxf
import math
from xarm.wrapper import XArmAPI

# Connexion au robot
arm = XArmAPI('192.168.1.215', baud_checkset=False)

# Initialisation du robot
arm.clean_warn()
arm.clean_error()
arm.motion_enable(True)
arm.set_mode(0)
arm.set_state(0)
time.sleep(1)

# Paramètres du robot
TCP_SPEED = 300
TCP_ACC = 2000
Z_HEIGHT = 100  # Hauteur de sécurité

# Position de base
BASE_X_OFFSET = 200
BASE_Y_OFFSET = 600

# Charger le fichier DXF
dxf_file = "coeur.dxf"  # Remplace par ton fichier
doc = ezdxf.readfile(dxf_file)
msp = doc.modelspace()

# Facteur d'échelle pour ajuster la taille du dessin
scale_factor = 1.0

# Déplacer en hauteur de sécurité avant de commencer
arm.set_position(BASE_X_OFFSET, BASE_Y_OFFSET, Z_HEIGHT+10, 0.0, 90.0, 90.0, speed=TCP_SPEED, wait=True)

def apply_offset(x, y):
    """Applique l'offset aux coordonnées x et y."""
    return x + BASE_X_OFFSET, y + BASE_Y_OFFSET

def move_to_position(x, y):
    """Déplace le robot à la position spécifiée."""
    arm.set_position(x, y, Z_HEIGHT, 0.0, 90.0, 90.0, speed=TCP_SPEED, radius=0, wait=False)

def process_lwpolyline(polyline):
    """Reconstruit correctement une LWPOLYLINE avec segments droits et arcs."""
    points = polyline.get_points('xyb')  # Récupérer x, y et bulge
    num_points = len(points)

    if num_points < 2:
        return  # Rien à tracer

    # Déplacer au premier point
    x_start, y_start = apply_offset(points[0][0] * scale_factor, points[0][1] * scale_factor)
    move_to_position(x_start, y_start)

    # Traiter chaque segment
    for i in range(num_points - 1):
        x1, y1, bulge = points[i]
        x2, y2, _ = points[i + 1]
        x1, y1 = apply_offset(x1 * scale_factor, y1 * scale_factor)
        x2, y2 = apply_offset(x2 * scale_factor, y2 * scale_factor)

        if bulge == 0:
            # Segment droit
            move_to_position(x2, y2)
        else:
            # Arc : calcul du centre et des points intermédiaires
            arc_points = calculate_arc(x1, y1, x2, y2, bulge)
            for x, y in arc_points:
                move_to_position(x, y)

    # Si la polyligne est fermée, connecter le dernier point au premier
    if polyline.is_closed:
        move_to_position(x_start, y_start)

def calculate_arc(x1, y1, x2, y2, bulge):
    """Calcule les points intermédiaires d'un arc défini par un bulge."""
    num_segments = 10  # Plus de segments = arc plus lisse
    arc_points = []

    # Calcul du centre de l'arc
    bulge_angle = math.atan(bulge) * 4
    chord_length = math.hypot(x2 - x1, y2 - y1)
    radius = chord_length / (2 * math.sin(bulge_angle / 2))

    # Calcul du centre du cercle
    chord_mid_x = (x1 + x2) / 2
    chord_mid_y = (y1 + y2) / 2
    height = radius * math.cos(bulge_angle / 2)

    # Déterminer la direction de l'arc
    dx, dy = x2 - x1, y2 - y1
    norm = math.sqrt(dx**2 + dy**2)
    perp_x, perp_y = -dy / norm, dx / norm  # Perpendiculaire à la corde

    center_x = chord_mid_x + height * perp_x * (-1 if bulge < 0 else 1)
    center_y = chord_mid_y + height * perp_y * (-1 if bulge < 0 else 1)

    # Générer les points intermédiaires de l'arc
    start_angle = math.atan2(y1 - center_y, x1 - center_x)
    end_angle = math.atan2(y2 - center_y, x2 - center_x)

    if bulge < 0:
        start_angle, end_angle = end_angle, start_angle

    for i in range(1, num_segments):
        angle = start_angle + (end_angle - start_angle) * (i / num_segments)
        arc_x = center_x + radius * math.cos(angle)
        arc_y = center_y + radius * math.sin(angle)
        arc_points.append((arc_x, arc_y))

    arc_points.append((x2, y2))  # Fin de l'arc
    return arc_points

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

        num_points = 20
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_points)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            move_to_position(x, y)

    elif entity.dxftype() == "CIRCLE":
        print("Dessin d'un cercle...")
        cx, cy = apply_offset(entity.dxf.center.x * scale_factor, entity.dxf.center.y * scale_factor)
        radius = entity.dxf.radius * scale_factor

        num_points = 36
        points = [(cx + radius * math.cos(2 * math.pi * i / num_points),
                   cy + radius * math.sin(2 * math.pi * i / num_points)) for i in range(num_points + 1)]

        move_to_position(points[0][0], points[0][1])

        for x, y in points:
            move_to_position(x, y)

    elif entity.dxftype() == "POINT":
       print("Déplacement vers un point...")
       # x, y = apply_offset(entity.dxf.location.x * scale_factor, entity.dxf.location.y * scale_factor)
       # move_to_position(x, y)

    elif entity.dxftype() == "LWPOLYLINE":
        print("Dessin d'une polyligne...")
        process_lwpolyline(entity)

    else:
        print("Entité inconnue:", entity.dxftype())

# Fin du programme
arm.set_position(BASE_X_OFFSET, BASE_Y_OFFSET, Z_HEIGHT+10, 0.0, 90.0, 90.0, speed=TCP_SPEED, mvacc=TCP_ACC, wait=True)
arm.disconnect()
print("Dessin terminé !")

# ============================
#   Makefile pour mon projet
# ============================

# Cible par défaut
all: update submodules commit push

# Met à jour le dépôt principal depuis 'origin' et initialise/ met à jour les sous-modules
update:
	@echo "Mise à jour du dépôt principal..."
	git pull origin main
	git submodule update --init --recursive

# Met à jour chaque sous-module en tirant les dernières modifications
submodules:
	@echo "Mise à jour des sous-modules..."
	git submodule foreach --recursive git pull origin main

# Commit les changements dans le dépôt principal avec un message fourni
commit:
	@read -p "Entrez le message de commit : " msg; \
	echo "Préparation du commit..."; \
	git add .; \
	git commit -m "$$msg"

# Pousse les changements du dépôt principal et de tous les sous-modules
push:
	@echo "Pousser les changements..."
	git push origin main
	git submodule foreach --recursive git push origin main

# Affiche l'état actuel des sous-modules
status:
	@echo "État des sous-modules :"
	git submodule status

.PHONY: all update commit push

all: update commit push

update:
	@echo "Mise à jour du dépôt principal..."
	git pull origin main
	@echo "Mise à jour des sous-modules..."
	git submodule update --init --recursive || true

commit:
	@read -p "Entrez le message de commit pour le dépôt principal: " msg; \
	git submodule foreach --recursive 'if [ -n "$$(git status --porcelain)" ]; then \
		read -p "Entrez le message de commit pour $$path: " submsg; \
		git add .; \
		git commit -m "$$submsg"; \
	fi'; \
	git add .; \
	git commit -m "$$msg"

push:
	@echo "Push des changements..."
	git push origin main
	git submodule foreach --recursive 'git push origin main || true'

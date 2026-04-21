#!/bin/bash

# 1. Nombre del repositorio (ajusta si prefieres otro)
REPO_NAME="financial-pipeline"
USER_NAME="cperezdengra"
URL="https://github.com/$USER_NAME/$REPO_NAME.git"

echo "Iniciando reparacion de Git para: $REPO_NAME"

# 2. Eliminar cualquier configuracion previa de remote
git remote remove origin 2>/dev/null

# 3. Asegurar que estamos en la rama main
git branch -M main

# 4. Añadir el origen correcto
git remote add origin $URL

# 5. Intentar hacer el push
echo "Intentando subir archivos a $URL..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "Exito: El repositorio se ha actualizado correctamente."
else
    echo "Error: No se pudo subir. Verifica que el repo existe en la web con el nombre exacto."
fi

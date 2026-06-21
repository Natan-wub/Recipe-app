 async function findRecipes() {
            const input = document.getElementById("ingredients").value;
            const recipesDiv = document.getElementById("recipes");

            if (input.trim() === "") {
                recipesDiv.innerHTML = "<p class='message'>Please type at least one ingredient.</p>";
                return;
            }

            recipesDiv.innerHTML = "<p class='message'>Searching...</p>";

            try {
                const response = await fetch("/api/recipes?ingredients=" + encodeURIComponent(input));
                const data = await response.json();

                if (data.error) {
                    recipesDiv.innerHTML = "<p class='message'>Problem: " + data.error + "</p>";
                    return;
                }
                if (data.recipes.length === 0) {
                    recipesDiv.innerHTML = "<p class='message'>No recipes found. Try different ingredients.</p>";
                    return;
                }

                recipesDiv.innerHTML = "";
                for (const recipe of data.recipes) {
                    recipesDiv.innerHTML +=
                        "<div class='recipe' onclick='showRecipe(" + recipe.id + ")'>" +
                        "<img src='" + recipe.image + "'>" +
                        "<div class='recipe-body'>" +
                        "<p class='recipe-title'>" + recipe.title + "</p>" +
                        "<p class='recipe-meta'>Uses " + recipe.used + " of yours · " + recipe.missed + " more needed</p>" +
                        "</div>" +
                        "</div>";
                }
            } catch (err) {
                recipesDiv.innerHTML = "<p class='message'>Couldn't reach the server — check the terminal.</p>";
            }
        }

       async function showRecipe(id) {
            const modal = document.getElementById("modal");
            const content = document.getElementById("modal-content");
            content.innerHTML = "<p class='message'>Loading recipe...</p>";
            modal.style.display = "flex";

            const response = await fetch("/api/recipe/" + id);
            const data = await response.json();

            currentRecipe = { id: id, title: data.title, image: data.image };
            /* this line is for localStorage version — now replaced with server-side storage, but keeping this here in case you want to switch back or see how it was done without a backend.
            const alreadySaved = getSaved().some(function (r) { return r.id === id; });*/
            const saved = await getSaved();
            const alreadySaved = saved.some(function (r) { return r.id === id; });

            let html = "<h2>" + data.title + "</h2>";
            html += "<img src='" + data.image + "' class='modal-img'>";
            html += "<p class='meta'>Ready in " + data.readyInMinutes + " min · Serves " + data.servings + "</p>";
            html += "<button id='save-btn' onclick='saveCurrentRecipe()'>" +
                    (alreadySaved ? "✓ Saved" : "♥ Save recipe") + "</button>";

            html += "<h3>Ingredients</h3><ul>";
            for (const ing of data.ingredients) {
                html += "<li>" + ing + "</li>";
            }
            html += "</ul>";

            html += "<h3>Instructions</h3>";
            if (data.steps.length === 0) {
                html += "<p>No step-by-step instructions available for this one.</p>";
            } else {
                html += "<ol>";
                for (const step of data.steps) {
                    html += "<li>" + step + "</li>";
                }
                html += "</ol>";
            }

            content.innerHTML = html;
        }

        function closeModal() {
            document.getElementById("modal").style.display = "none";
        }

       function getDrink() {
            const result = document.getElementById("result");
            result.innerHTML = "<p class='message'>Finding your location...</p>";

            if (!navigator.geolocation) {
                fetchWeather();
                return;
            }

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    fetchWeather(position.coords.latitude, position.coords.longitude);
                },
                function () {
                    fetchWeather();
                },
                { timeout: 8000 }
            );
        }

        async function fetchWeather(lat, lon) {
            const result = document.getElementById("result");
            result.innerHTML = "<p class='message'>Checking the weather...</p>";

            let url = "/api/weather";
            if (lat !== undefined && lon !== undefined) {
                url += "?lat=" + lat + "&lon=" + lon;
            }

            try {
                const response = await fetch(url);
                const data = await response.json();

                let html = "<div class='drink-card'>";
                html += "<div class='drink-emoji'>" + data.emoji + "</div>";
                html += "<p>It's " + data.temperature + "°C. Today's pick: " + data.name + ".</p>";
                html += "</div>";

                html += "<div class='drink-recipe'>";
                html += "<h3>Ingredients</h3><ul>";
                for (const ing of data.ingredients) {
                    html += "<li>" + ing + "</li>";
                }
                html += "</ul>";
                html += "<h3>How to make it</h3><ol>";
                for (const step of data.steps) {
                    html += "<li>" + step + "</li>";
                }
                html += "</ol></div>";

                result.innerHTML = html;
            } catch (err) {
                result.innerHTML = "<p class='message'>Couldn't get the weather right now.</p>";
            }
        }

        /*this block is for localStorage version — now replaced with server-side storage, but keeping this here in case you want to switch back or see how it was done without a backend.
        let currentRecipe = null;

        function getSaved() {
            const raw = localStorage.getItem("savedRecipes");
            return raw ? JSON.parse(raw) : [];
        }

        function setSaved(list) {
            localStorage.setItem("savedRecipes", JSON.stringify(list));
        }

        function saveCurrentRecipe() {
            if (!currentRecipe) return;
            const saved = getSaved();
            if (!saved.some(function (r) { return r.id === currentRecipe.id; })) {
                saved.push(currentRecipe);
                setSaved(saved);
                renderSaved();
            }
            document.getElementById("save-btn").textContent = "✓ Saved";
        }

        function removeRecipe(event, id) {
            event.stopPropagation();
            const saved = getSaved().filter(function (r) { return r.id !== id; });
            setSaved(saved);
            renderSaved();
        }

        function renderSaved() {
            const savedDiv = document.getElementById("saved");
            const saved = getSaved();

            if (saved.length === 0) {
                savedDiv.innerHTML = "<p class='message'>No saved recipes yet — open a recipe and tap Save.</p>";
                return;
            }

            savedDiv.innerHTML = "";
            for (const recipe of saved) {
                savedDiv.innerHTML +=
                    "<div class='recipe' onclick='showRecipe(" + recipe.id + ")'>" +
                    "<img src='" + recipe.image + "'>" +
                    "<div class='recipe-body'>" +
                    "<p class='recipe-title'>" + recipe.title + "</p>" +
                    "<button class='remove-btn' onclick='removeRecipe(event, " + recipe.id + ")'>Remove</button>" +
                    "</div>" +
                    "</div>";
            }
        }

        renderSaved();*/ 

        let currentRecipe = null;

        async function getSaved() {
            const response = await fetch("/api/saved");
            const data = await response.json();
            return data.recipes;
        }

        async function saveCurrentRecipe() {
            if (!currentRecipe) return;
            await fetch("/api/saved", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(currentRecipe)
            });
            renderSaved();
            document.getElementById("save-btn").textContent = "✓ Saved";
        }

        async function removeRecipe(event, id) {
            event.stopPropagation();
            await fetch("/api/saved/" + id, { method: "DELETE" });
            renderSaved();
        }

        async function renderSaved() {
            const savedDiv = document.getElementById("saved");
            const saved = await getSaved();

            if (saved.length === 0) {
                savedDiv.innerHTML = "<p class='message'>No saved recipes yet — open a recipe and tap Save.</p>";
                return;
            }

            savedDiv.innerHTML = "";
            for (const recipe of saved) {
                savedDiv.innerHTML +=
                    "<div class='recipe' onclick='showRecipe(" + recipe.id + ")'>" +
                    "<img src='" + recipe.image + "'>" +
                    "<div class='recipe-body'>" +
                    "<p class='recipe-title'>" + recipe.title + "</p>" +
                    "<button class='remove-btn' onclick='removeRecipe(event, " + recipe.id + ")'>Remove</button>" +
                    "</div>" +
                    "</div>";
            }
        }
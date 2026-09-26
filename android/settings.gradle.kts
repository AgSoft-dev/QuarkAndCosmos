// Quark & Cosmos — POC Android (Stage 5, cf. todo.md §4.4).
//   :core-physics  Kotlin pur : port du moteur Python (stage3-physics-engine), testé contre les golden
//   :game          libGDX (JVM) : écran de niveau, rendu DA v2, entrées
//   :app           coque Android : menus Compose, activité libGDX, sauvegarde
pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "QuarkAndCosmos"
include(":core-physics", ":game", ":app")

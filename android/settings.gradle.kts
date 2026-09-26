// Quark & Cosmos — Android POC (Stage 5, see todo.md §4.4).
//   :core-physics  pure Kotlin: port of the Python engine (levels-builder), tested against the goldens
//   :game          libGDX (JVM): level screen, art direction v2 rendering, input
//   :app           Android shell: Compose menus, libGDX activity, saving, EN/FR strings
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

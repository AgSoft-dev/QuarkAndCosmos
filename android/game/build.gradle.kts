import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Vue de jeu libGDX (JVM pur, sans dépendance Android) : écran de niveau,
// rendu DA v2 (matière B + fond C), entrées. Le backend Android est dans :app.
plugins {
    alias(libs.plugins.kotlin.jvm)
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    api(project(":core-physics"))
    api(libs.gdx)
    implementation(libs.gdx.freetype)
}

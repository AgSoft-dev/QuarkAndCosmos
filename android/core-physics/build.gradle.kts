import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Physique du jeu en Kotlin pur (aucune dépendance Android ni libGDX) : port
// déterministe de stage3-physics-engine/engine, cf. docs/physics-spec.md.
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
    implementation(libs.kotlinx.serialization.json)
    testImplementation(libs.junit)
}

// Les niveaux et les trajectoires golden restent à leur place unique, dans le
// moteur Python : le test les lit directement (cf. GoldenTest).
val stage3 = layout.projectDirectory.dir("../../stage3-physics-engine")
tasks.test {
    systemProperty("stage3.dir", stage3.asFile.absolutePath)
    inputs.dir(stage3.dir("levels")).withPropertyName("levels")
    inputs.dir(stage3.dir("tests/golden")).withPropertyName("golden")
}

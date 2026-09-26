import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// libGDX game view (pure JVM, no Android dependency): level screen, art
// direction v2 rendering (B matter + C background), input. The Android backend
// lives in :app; player-facing strings come from :app through GameText.
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

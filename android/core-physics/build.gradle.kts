import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Game physics in pure Kotlin (no Android or libGDX dependency): deterministic
// port of levels-builder/src/quarkcosmos_levels/core, see docs/physics-spec.md.
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

// Levels and golden trajectories stay in their single place (content/ and the
// Python builder): the test reads them directly (see GoldenTest).
val repo = layout.projectDirectory.dir("../..")
val levels = repo.dir("content/levels/quantique")
val golden = repo.dir("levels-builder/tests/golden")
tasks.test {
    systemProperty("levels.dir", levels.asFile.absolutePath)
    systemProperty("golden.dir", golden.asFile.absolutePath)
    inputs.dir(levels).withPropertyName("levels")
    inputs.dir(golden).withPropertyName("golden")
}

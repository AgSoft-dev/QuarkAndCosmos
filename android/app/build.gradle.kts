import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Android shell: Compose menus (welcome, scales, Quantum world map), libGDX
// activity for the level, star saving (DataStore), English + French strings.
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "dev.agsoft.quarkcosmos"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.agsoft.quarkcosmos"
        minSdk = 26 // Android 8.0
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-poc"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }

    // Per-app language (Android 13+ settings): locales taken from res/values-*,
    // default locale declared in res/resources.properties.
    androidResources {
        generateLocaleConfig = true
    }

    sourceSets.getByName("main") {
        // Levels and Codex lines copied from content/ at every build (single source, nothing duplicated in git).
        assets.srcDir(layout.buildDirectory.dir("generated/content-assets").get().asFile)
        // libGDX native libraries, extracted from the `natives` jars below.
        jniLibs.srcDir(layout.buildDirectory.dir("gdx-natives").get().asFile)
    }
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

val natives: Configuration by configurations.creating

dependencies {
    implementation(project(":game"))
    implementation(libs.gdx.backend.android)
    for (abi in listOf("armeabi-v7a", "arm64-v8a", "x86", "x86_64")) {
        natives("com.badlogicgames.gdx:gdx-platform:${libs.versions.gdx.get()}:natives-$abi")
        natives("com.badlogicgames.gdx:gdx-freetype-platform:${libs.versions.gdx.get()}:natives-$abi")
    }

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.foundation)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    debugImplementation(libs.androidx.compose.ui.tooling)
    implementation(libs.androidx.datastore.preferences)
}

// Shipped content (content/ at the repo root, see docs/level-schema.md):
// levels -> assets/levels/, Codex lines -> assets/codex/<lang>/.
val content = rootProject.layout.projectDirectory.dir("../content")
val copyContent by tasks.registering(Sync::class) {
    from(content.dir("levels/quantique")) {
        include("*.json")
        into("levels")
    }
    from(content.dir("codex")) {
        include("*/*.json")
        into("codex")
    }
    into(layout.buildDirectory.dir("generated/content-assets"))
}

// Extract libGDX .so files per ABI (same approach as the gdx-liftoff template).
val copyAndroidNatives by tasks.registering {
    val out = layout.buildDirectory.dir("gdx-natives")
    inputs.files(natives)
    outputs.dir(out)
    doFirst {
        natives.files.forEach { jar ->
            val abi = jar.nameWithoutExtension.substringAfterLast("natives-")
            copy {
                from(zipTree(jar))
                into(out.get().dir(abi))
                include("*.so")
            }
        }
    }
}

tasks.named("preBuild") { dependsOn(copyContent, copyAndroidNatives) }

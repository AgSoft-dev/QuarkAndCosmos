import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// Coque Android : menus Compose (accueil, échelles, carte du monde Quantique),
// activité libGDX pour le niveau, sauvegarde des étoiles (DataStore).
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

    sourceSets.getByName("main") {
        // Niveaux copiés depuis le moteur Python à chaque build (source unique, rien de dupliqué dans git).
        assets.srcDir(layout.buildDirectory.dir("generated/levels-assets").get().asFile)
        // Bibliothèques natives de libGDX, extraites des jars `natives` ci-dessous.
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

// Niveaux livrés : seulement stage3-physics-engine/levels/*.json (jamais meta/, réservé au dev).
val copyLevels by tasks.registering(Sync::class) {
    from(rootProject.layout.projectDirectory.dir("../stage3-physics-engine/levels")) {
        include("*.json")
    }
    into(layout.buildDirectory.dir("generated/levels-assets/levels"))
}

// Extraction des .so de libGDX par ABI (même principe que le gabarit gdx-liftoff).
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

tasks.named("preBuild") { dependsOn(copyLevels, copyAndroidNatives) }

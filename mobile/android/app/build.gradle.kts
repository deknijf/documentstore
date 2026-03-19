import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.devtools.ksp")
}

fun loadDocstoreEnv(): Properties {
    val props = Properties()
    val repoRoot = projectDir.resolve("../../..").normalize()
    val envFiles = listOf(repoRoot.resolve(".env"), repoRoot.resolve(".env.example"))
    val selected = envFiles.firstOrNull { it.exists() } ?: return props
    selected.inputStream().use { props.load(it) }
    return props
}

fun envValue(props: Properties, key: String, default: String): String {
    val raw = props.getProperty(key)?.trim().orEmpty()
    return if (raw.isNotEmpty()) raw else default
}

fun runtimeOrEnvValue(props: Properties, key: String, default: String): String {
    val runtime = System.getenv(key)?.trim().orEmpty()
    if (runtime.isNotEmpty()) return runtime
    return envValue(props, key, default)
}

fun toVersionCode(version: String): Int {
    val parts = version.split(".").mapNotNull { it.toIntOrNull() }
    val major = parts.getOrElse(0) { 0 }
    val minor = parts.getOrElse(1) { 0 }
    val patch = parts.getOrElse(2) { 0 }
    return (major * 10000) + (minor * 100) + patch
}

fun ensureTrailingSlash(value: String): String = if (value.endsWith("/")) value else "$value/"

val docstoreEnv = loadDocstoreEnv()
val appSemver = envValue(docstoreEnv, "VERSION", "0.6.6")
val mobileBaseUrl = ensureTrailingSlash(
    envValue(
        docstoreEnv,
        "MOBILE_APP_BASE_URL",
        envValue(docstoreEnv, "PUBLIC_BASE_URL", "https://docstore.deknijf.eu"),
    ),
)
val signingStoreFile = runtimeOrEnvValue(
    docstoreEnv,
    "ANDROID_SIGNING_STORE_FILE",
    rootDir.resolve("build-support/docstore-release.keystore").absolutePath,
)
val signingStorePassword = runtimeOrEnvValue(docstoreEnv, "ANDROID_SIGNING_STORE_PASSWORD", "android")
val signingKeyAlias = runtimeOrEnvValue(docstoreEnv, "ANDROID_SIGNING_KEY_ALIAS", "docstore")
val signingKeyPassword = runtimeOrEnvValue(docstoreEnv, "ANDROID_SIGNING_KEY_PASSWORD", signingStorePassword)

android {
    namespace = "eu.deknijf.docstoremobile"
    compileSdk = 35

    signingConfigs {
        create("docstoreRelease") {
            storeFile = file(signingStoreFile)
            storePassword = signingStorePassword
            keyAlias = signingKeyAlias
            keyPassword = signingKeyPassword
        }
    }

    defaultConfig {
        applicationId = "eu.deknijf.docstoremobile"
        minSdk = 26
        targetSdk = 35
        versionCode = toVersionCode(appSemver)
        versionName = appSemver

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
        buildConfigField("String", "DOCSTORE_BASE_URL", "\"$mobileBaseUrl\"")
        buildConfigField("String", "APP_VERSION_LABEL", "\"$appSemver\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("docstoreRelease")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.03")

    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.navigation:navigation-compose:2.8.4")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("com.google.android.material:material:1.12.0")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")

    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    implementation("androidx.work:work-runtime-ktx:2.9.1")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    implementation("io.coil-kt:coil-compose:2.7.0")

    implementation("com.google.android.gms:play-services-mlkit-document-scanner:16.0.0-beta1")
}
